import argparse
from os import environ
# from os import getcwd, chdir
from time import perf_counter
from datetime import datetime

import pandas as pd

from polaristools.polarisbot import PolarisBot

''' 
    This script does two things.
    
    (1) Read mongo database in a specific collection and
        create a dataframe from scratch OR update an existent one.
        Finally persist this as binary file.
    
    (2) Read dataframes in 1 minute interval,
        resample it in many other major intervals,
        finally persist as binary.
    
    APPLY PERIODICALLY WITH NEW DATA.
    '''

raspi = '192.168.8.106'
db_user = 'admin'
db_pass = environ.get('mongodbadminpass')

database_config = {
    'db_host':raspi,
    'db_user':db_user,
    'db_pass':db_pass,
}
polaris = PolarisBot(mongo_cred=database_config)


def from_mongo_to_binary_df(symbols:list, stream_type:str, interval:int, database:str):
    start=perf_counter()
    
    for symbol in symbols:
        # Define filename
        filename = f'df_{stream_type}_{symbol}_{interval}'
        
        # Read dataframe from binary.
        df_bin = polaris.dataframeFromBinary(filename)
        
        if df_bin is None:
            # Query database for entire data.
            collection = f'{stream_type}_{symbol}_{interval}'
            df_new = polaris.createDataframe(mydb=database, collection=collection)
            polaris.dataframeToBinary(dataframe=df_new, filename=filename)
            print(f'*** New Dataframe persisted as binary... {symbol} - {interval} ***\n')
            continue
        
        # Capture newest date from last row in previously saved Dataframe.
        last_date = df_bin.last_valid_index().to_pydatetime()
        
        # Query databse
        collection = f'{stream_type}_{symbol}_{interval}'
        df_new = polaris.createDataframe(mydb=database, collection=collection, date_range={'gt':last_date})
        if df_new.empty:
            print('There are no new data to add in: ',filename)
            continue
        
        # Concatenate dataframes
        df_updated = pd.concat([df_bin, df_new])
        
        # Persist again as .pckl. Overwrite
        polaris.dataframeToBinary(dataframe=df_updated, filename=filename)
        print(f'*** Updated Dataframe persisted as binary... {symbol} - {interval} ***')
    end=perf_counter()
    totalt= (end-start)
    print(f'Elapsed time: {totalt:.2f} seconds.\n')

def read_resample_write(stream_type:str, symbols:list):
    ''' 
        open 1 minute datasets
        and resample to 240,120,60,30,15,10,5,3.
        '''
    start=perf_counter()
    dfs_1m = [f"df_{stream_type}_{symbol}_1m" for symbol in symbols]
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
            polaris.dataframeToBinary(df_rs, filename)
            print(f'Ready with {df} // resampled to {p} minutes')
    end=perf_counter()
    elapsed = end-start
    print(f'Resample finished succesfully. Elapsed time: {elapsed:.2f} seconds.')

def parse_inputs(pargs=None):
    parser = argparse.ArgumentParser(
        description='...'
    )
    
    parser.add_argument('--mongo_to_df',
        action='store_true',
        help='...'
    )
    parser.add_argument('--resample_df',
        action='store_true',
        help='...'
    )
    
    # parser.add_argument('--portfolio',
        # choices=['futures_busd', 'spot_usdt'],
        # help='Load data for a list of previously selected symbols'
    # )
    
    parser.add_argument('--interval',
        choices=['1d', '1m'],
        help='Pick up an interval from the list'
    )
    parser.add_argument('--streamtype',
        choices=['klines', 'continuous_klines']
    )
    parser.add_argument('--quotedasset',
        choices=['usdt', 'busd']
    )
    parser.add_argument('--markettype',
        choices=['spot_margin', 'futures_stable', 'futures_coins']
    )
    return parser.parse_args(pargs)

def main(args=None):
    arg = parse_inputs(args)
    
    database = f"binance_{arg.markettype}_{arg.quotedasset}"
    
    futures_busd = [
        'BTCBUSD','ANCBUSD','SOLBUSD','BNBBUSD','ETCBUSD','ETHBUSD',
        'ADABUSD','DOGEBUSD','LTCBUSD','MATICBUSD','LINKBUSD','XRPBUSD',
        'WAVESBUSD','AVAXBUSD','FTTBUSD','GALBUSD','LEVERBUSD','GMTBUSD',
        'LDOBUSD','APEBUSD','NEARBUSD','FTMBUSD','ICPBUSD','FILBUSD',
        'DOTBUSD','TLMBUSD','SANDBUSD','CVXBUSD','AUCTIONBUSD','DODOBUSD',
        'GALABUSD','TRXBUSD','UNIBUSD',
        'LUNA2BUSD','1000LUNCBUSD','1000SHIBBUSD',
        ]
    spot_usdt = [
        'DODOUSDT','BNBUSDT','CVXUSDT','ETHUSDT','MATICUSDT','FTMUSDT',
        'FTTUSDT','GMTUSDT','GALAUSDT','BTCUSDT','ADAUSDT','ANCUSDT',
        'TLMUSDT','WAVESUSDT','ICPUSDT','AUCTIONUSDT','DOTUSDT','TRXUSDT',
        'SANDUSDT','FILUSDT','LEVERUSDT','UNIUSDT','DOGEUSDT','LDOUSDT',
        'AVAXUSDT','LTCUSDT','APEUSDT','SOLUSDT','NEARUSDT','XRPUSDT',
        'ETCUSDT','LINKUSDT','GALUSDT',
        'LUNCUSDT','SHIBUSDT','LUNAUSDT',
        ]
    
    if arg.streamtype=='continuous_klines':
        coins=futures_busd
    elif arg.streamtype=='klines':
        coins=spot_usdt
    
    symbols = [coin for coin in coins]
    
    if arg.mongo_to_df:
        from_mongo_to_binary_df(
            symbols = symbols,
            stream_type = arg.streamtype,
            interval = arg.interval,
            database = database,
        )
    if arg.resample_df:
        read_resample_write(
            stream_type=arg.streamtype,
            symbols=symbols,
        )


if __name__== '__main__':
    main()
    
    ''' 
        ########## SPOT #########################
        python3 dataframes-as-binary.py \
        --mongo_to_df \
        --streamtype klines \
        --interval 1d \
        --quotedasset usdt \
        --markettype spot_margin \
        
        ########## FUTURES #########################
        python3 dataframes-as-binary.py \
        --mongo_to_df \
        --streamtype continuous_klines \
        --interval 1d \
        --quotedasset busd \
        --markettype futures_stable \
        
            ########## FUTURES #########################
            python3 dataframes-as-binary.py \
            --mongo_to_df \
            --resample_df \
            --streamtype continuous_klines \
            --interval 1m \
            --quotedasset busd \
            --markettype futures_stable \
        
        '''