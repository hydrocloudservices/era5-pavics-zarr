from datetime import datetime, timedelta
import os

END_DATE_DATETIME = (datetime.utcnow()- timedelta(days=5))


class Config(object):
    # Bucket configuration
    BUCKET = 's3://era5/world/reanalysis/single-levels/netcdf'

    CLIENT_KWARGS = {'endpoint_url': 'https://s3.wasabisys.com',
                     'region_name': 'us-east-1'}
    CONFIG_KWARGS = {'max_pool_connections': 100}
    PROFILE = 'default'

    STORAGE_OPTIONS = {'profile': PROFILE,
                       'client_kwargs': CLIENT_KWARGS,
                       'config_kwargs': CONFIG_KWARGS
                       }

    # Dataset
    BATCH_IMPORT_DAYS = ['06Jan', '06Apr','06Jul','06Oct']

    DATETIME_NOW = datetime.utcnow()
    END_DATE_DATETIME = (datetime.utcnow()- timedelta(days=6))
    print(END_DATE_DATETIME)
    END_DATE = END_DATE_DATETIME.strftime('%Y-%m-%d')
    BUCKET_ZARR_CURENT = os.path.join('s3://era5/world/reanalysis/single-levels/zarr-time-cache', END_DATE)

    print(DATETIME_NOW)
    start_dates = []
    for day in BATCH_IMPORT_DAYS:
        date = datetime.strptime(day + str(DATETIME_NOW.year), '%d%b%Y')
        if date > DATETIME_NOW:
            date = date.replace(year=date.year - 1)
        start_dates.append(date)
    dates_list = [10000 if i <= 0 else i for i in [(END_DATE_DATETIME - (start_date - timedelta(days=6))).days
                                                   for start_date in start_dates]]
    index = dates_list.index(min(dates_list))
    START_DATE_ZARR = (start_dates[index] - timedelta(days=5)).strftime('%Y-%m-%d')
    print(START_DATE_ZARR)
    print(END_DATE)

    VARIABLES = {'2m_temperature': 't2m',
                 'total_precipitation': 'tp'} # 'snowfall': 'sf'

    TIMES = ['00:00', '01:00', '02:00',
             '03:00', '04:00', '05:00',
             '06:00', '07:00', '08:00',
             '09:00', '10:00', '11:00',
             '12:00', '13:00', '14:00',
             '15:00', '16:00', '17:00',
             '18:00', '19:00', '20:00',
             '21:00', '22:00', '23:00'
             ]
