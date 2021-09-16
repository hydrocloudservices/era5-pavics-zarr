import xarray as xr
from dask.distributed import Client
from prefect import task, Flow, case, agent
from datetime import datetime, timedelta
import os
import errno
import numpy as np
import fsspec
import zarr
from rechunker import rechunk
from prefect.executors import DaskExecutor
import s3fs
import pandas as pd
import itertools
import numpy as np
import shutil
from itertools import product
from config import Config
from prefect import task, Flow, Parameter
import subprocess


@task(max_retries=5, retry_delay=timedelta(seconds=10))
def list_all_files_to_fetch(short_name_variables):
    """
    Determines list of all possible unique single variable daily files from a list of dates.
    It then compares if those files exist in the bucket (Config.BUCKET)

    :return: Matrix with dates and variables to extract
    """
    # fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)

    date_range: list = pd.date_range(start=Config.START_DATE_ZARR,
                                     end=Config.END_DATE).strftime('%Y%m%d')

    filenames = ['{}_{}_ERA5_SL_REANALYSIS.nc'.format(date, variable.upper()) for
            date, variable in product(date_range, [short_name_variables])]
    print(filenames)

    return filenames


@task(max_retries=5, retry_delay=timedelta(seconds=10))
def save_unique_variable_date_file(filename):

    path = 'tmp/data'

    try:
        fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)
        fs.download(os.path.join(Config.BUCKET, filename),
                    os.path.join(path, filename))
    except FileNotFoundError:
        filename_list = filename.split('_')
        date_str = filename_list[0]
        variable = filename_list[1]
        times = pd.date_range(date_str, periods=24, freq='h')
        longitude = np.arange(0.0, 360, 0.25)
        latitude = np.arange(90, -90 - 0.25, -0.25)

        data = np.full([times.size, latitude.size, longitude.size], np.nan).astype(np.float32)

        da = xr.DataArray(data,
                          coords=[times, latitude, longitude],
                          dims=["time", "latitude", "longitude"]).rename(variable.lower())
        ds = da.to_dataset()
        ds.to_netcdf(os.path.join(path, filename))
    return path


@task(max_retries=5, retry_delay=timedelta(seconds=10))
def create_current_zarr_dataset(variable, path):

    ds = xr.open_mfdataset(os.path.join(path,'*.nc'))
    print(ds)
    ds['longitude'] = (((ds.longitude + 180) % 360) - 180)
    ds = ds.sortby('longitude')
    for var in ds.variables:
        if not var in ds.coords:
            ds[var] = ds[var].astype('float32')

    print('Saving to zarr...')
    output_path = os.path.join('tmp/zarr/source',variable)
    delayed = ds.to_zarr(output_path, consolidated=True, compute=False)
    delayed.compute(retries=10)
    shutil.rmtree(path)

    return output_path


@task(max_retries=5, retry_delay=timedelta(seconds=10))
def chunk_zarr_dataset(variable, source_store):

    temp_store = os.path.join('tmp/zarr/tmp', variable)
    # target_store = fsspec.get_mapper(Config.BUCKET_ZARR_CURENT,
    #                                  profile=Config.PROFILE,
    #                                  client_kwargs=Config.CLIENT_KWARGS)
    target_store = os.path.join('tmp/zarr/current', variable)
    source_group = zarr.open(source_store)

    chunks = {'time': source_group.time.size, 'latitude': 5, 'longitude': 5}
    target_chunks = {}
    for value in list(source_group.items()):
        if len(value[1].chunks) == 1:
            target_chunks[value[0]] = None
        else:
            target_chunks[value[0]] = chunks

    # target_chunks = {
    #     't2m': chunks,
    #     'tp': chunks,
    #     'time': None,  # don't rechunk this array
    #     'longitude': None,
    #     'latitude': None,
    # }
    max_mem = '1500MB'

    array_plan = rechunk(source_group,
                         target_chunks=target_chunks,
                         max_mem=max_mem,
                         target_store=target_store,
                         temp_store=temp_store)
    array_plan.execute(retries=100)
    shutil.rmtree(source_store)
    # shutil.rmtree(temp_store)
    return target_store


@task(max_retries=5, retry_delay=timedelta(seconds=10))
def store_variable(variable, store, idx):

    fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)
    if idx == 0:
        input_store = store
        target_store = Config.BUCKET_ZARR_CURENT
    else:
        input_store = os.path.join(store, variable)
        target_store = os.path.join(Config.BUCKET_ZARR_CURENT, variable)

    # fs.put(input_store,
    #        target_store,
    #        recursive=True)

    command = "aws s3 sync {} {} " \
              "--endpoint-url={} --region={} --profile={}".format(input_store,
                                                                  target_store,
                                                                  Config.CLIENT_KWARGS['endpoint_url'],
                                                                  Config.CLIENT_KWARGS['region_name'],
                                                                  Config.PROFILE)
    subprocess.call(command, shell=True)


if __name__ == '__main__':
    client = Client(processes=False)
    executor = DaskExecutor(address=client.scheduler.address)
    with Flow("ERA5-ETL") as flow:
        variable = Parameter('variable')
        idx = Parameter('idx')
        filenames = list_all_files_to_fetch(variable)

        netcdf_path = save_unique_variable_date_file.map(filenames)
        zarr_path = create_current_zarr_dataset(variable, netcdf_path[0])
        target_store = chunk_zarr_dataset(variable, zarr_path)
        store_variable(variable, target_store, idx)

    for idx, var in enumerate(list(Config.VARIABLES.values())):
        print(var)
        flow.run(executor=executor,
                 parameters=dict(variable=var,
                                 idx=idx))
    fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)
    store = fsspec.get_mapper(Config.BUCKET_ZARR_CURENT,
                              profile=Config.PROFILE,
                              client_kwargs=Config.CLIENT_KWARGS)
    zarr.consolidate_metadata(store)


