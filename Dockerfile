FROM continuumio/miniconda3:4.8.2

RUN conda install --yes \
    -c conda-forge \
    python==3.8 \
    python-blosc \
    cytoolz \
    dask==2021.7.1 \
    lz4 \
    nomkl \
    s3fs \
    rechunker \
    fsspec \
    h5netcdf \
    h5py \
    hdf5 \
    prefect \
    rasterio \
    numcodecs \
    zarr \
    netcdf4 \
    scipy \
    zarr \
    numpy==1.21.1 \
    pandas==1.3.0 \
    tini==0.18.0 \
    && conda clean -tipsy \
    && find /opt/conda/ -type f,l -name '*.a' -delete \
    && find /opt/conda/ -type f,l -name '*.pyc' -delete \
    && find /opt/conda/ -type f,l -name '*.js.map' -delete \
    && find /opt/conda/lib/python*/site-packages/bokeh/server/static -type f,l -name '*.js' -not -name '*.min.js' -delete \
    && rm -rf /opt/conda/pkgs

RUN /opt/conda/bin/pip install pangeo-forge-recipes
RUN python3 -m pip --no-cache-dir install --upgrade awscli

COPY prepare.sh /usr/bin/prepare.sh

RUN mkdir /opt/app

ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]