from os import environ
from os import getcwd, chdir
from time import perf_counter
from datetime import datetime

import pandas as pd

from polaristools.polarisbot import PolarisBot

''' 
    This script does two things.
    
    (1) Read mongo database in a specific collection, 
        create a dataframe  or update a existent one.
        Finally persist this as binary file.
    (2) Read dataframes in e.g: 1 minute interval,
            resample in many other major intervals,
            finally persist as binary.
            
    USE: Apply periodically with new data.
    '''

raspi = '192.168.8.106'
db_user = 'admin'
db_pass = environ.get('mongodbadminpass')

database_config = {
    'db_host':raspi,
    'db_user':db_user,
    'db_pass':db_pass
}
polaris = PolarisBot(mongo_cred=database_config)


def from_mongo_to_binary_df(symbols:list, interval:int, database:str):
    start=perf_counter()
    for symbol in symbols:
        # Define filename
        filename = f'df_klines_{symbol}_{interval}'
        
        # Read dataframe from binary.
        df_bin = polaris.dataframeFromBinary(filename)
        
        if df_bin is None:
            # Query databse for entire data.
            collection = f'klines_{symbol}_{interval}'
            df_new = polaris.createDataframe(mydb=database, collection=collection)
            polaris.dataframeToBinary(dataframe=df_new, filename=filename)
            print(f'*** New Dataframe persisted as binary... {symbol} - {interval} ***')
            continue
        
        # Capture newest date from last row in previously saved Dataframe.
        last_date = df_bin.last_valid_index().to_pydatetime()
        
        # Query databse
        collection = f'klines_{symbol}_{interval}'
        df_new = polaris.createDataframe(mydb=database, collection=collection, date_range={'gt':last_date})
        if df_new.empty:
            print('There are no new data to add in: ',filename)
            continue
        
        # Search for NaN in dataframes.
        ''' if int(df_new.isnull().sum().sum()) > 0:
            print('There are NaN values in the new data.')
            print(df_new.isnull().sum())
            break '''
        
        # Concatenate dataframes
        df_updated = pd.concat([df_bin, df_new])
        
        # Persist again as .pckl. Overwrite
        polaris.dataframeToBinary(dataframe=df_updated, filename=filename)
        print(f'*** Updated Dataframe persisted as binary... {symbol} - {interval} ***')
    end=perf_counter()
    totalt= (end-start)
    print(f'Elapsed time: {totalt:.2f} seconds.\n')

def read_resample_write():
    ''' 
        open 1 minute datasets
        and resample to 240,120,60,30,15,10,5,3.
        '''
    start=perf_counter()
    dfs_1m = [
        'df_klines_BTCUSDT_1m',
        'df_klines_ETHUSDT_1m',
        'df_klines_BNBUSDT_1m',
        'df_klines_DOGEUSDT_1m'
    ]
    rs_p = [240,120,60,30,15,10,5,3]
    for df in dfs_1m:
        dataframe = polaris.dataframeFromBinary(df)
        for p in rs_p:
            period = str(p)+'T'
            df_rs = dataframe.resample(
                period, label='right',closed='right'
                ).agg(
                    {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
                )
            filename = df[:-2]+str(p)+'m'
            polaris.dataframeToBinary(df_rs,filename)
            print(f'Ready with {df} // resampled to {p} minutes')
    end=perf_counter()
    elapsed = end-start
    print(f'Resample finished succesfully. Elapsed time: {elapsed:.2f} seconds.')


if __name__== '__main__':
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT','DOGEUSDT']
    database = 'binance_spot_margin_usdt'
    
    from_mongo_to_binary_df(
        symbols = symbols,
        interval = '1d',
        database = database,
    )
    
    from_mongo_to_binary_df(
        symbols = symbols,
        interval = '1m',
        database = database,
    )

    read_resample_write()