import argparse
from os import environ
from os import getcwd, chdir
from time import sleep

from polaristools.polarisbot import PolarisBot


''' 
    (1) Download data through the API and persist it in a mongo database.
        Create new collections from scratch or update current collections.
        
    (2) Use it in commands terminal.
    '''


def obtain_data_klines(polaris, args=None):
    current = getcwd()
    if not current.endswith('capture-data'):
        chdir('/home/llagask/Trading/polaris39/capture-data')
    
    args = parse_inputs(args)

    updateOption = args.updatedb
    createDbOption = args.createdb

    # top_vol_24h_usdt = [
        # 'BTCUSDT','ETHUSDT','TRXUSDT','BNBUSDT',
        # 'SOLUSDT','ADAUSDT','XRPUSDT','LINKUSDT',
        # 'AVAXUSDT','DOGEUSDT','DOTUSDT','LTCUSDT',
        # 'MATICUSDT','WAVESUSDT','SHIBUSDT','ZILUSDT',
        # 'ATOMUSDT','APEUSDT',
    # ]

    symbols_1m = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT','DOGEUSDT']

    if args.symbol:
        asymbols = args.symbol
    # elif args.portfoliosymbols:
        # asymbols = top_vol_24h_usdt
    elif args.portfoliosymbols:
        asymbols = symbols_1m
    else:
        print('No valid symbol entered')

    interval    = args.interval
    stream_type = args.streamtype
    market_type = args.markettype

    if createDbOption:
        polaris.createDatabaseKlines(
        symbols      = asymbols, 
        interval     = interval,
        quoted_asset = 'usdt',
        stream_type  = stream_type,
        market_type  = market_type,
    )

    if updateOption:
        polaris.updateDatabaseKlines(
        symbols      = asymbols, 
        interval     = interval,
        quoted_asset = 'usdt',
        stream_type  = stream_type,
        market_type  = market_type,
    )
    
    chdir('/home/llagask/Trading/polaris39')

def parse_inputs(pargs=None):
    parser = argparse.ArgumentParser(
        description='Choose between create database from scratch or update existing collections'
    )
    parser.add_argument('--createdb',
        action='store_true',
        help='Create a brand new database and collections'
    )
    parser.add_argument('--updatedb',
        action='store_true',
        help='Update existent collections in a database'
    )
    parser.add_argument('--symbol',
        action='append',
        help='call each time for each symbol'
    )
    parser.add_argument('--portfoliosymbols',
        action='store_true',
        help='Load data for a list of previously selected symbols'
    )
    parser.add_argument('--markettype',
        choices=['spot_margin', 'futures_usd', 'futures_coins']
    )
    parser.add_argument('--quotedasset',
        choices=['USDT','BUSD','BTC']
    )
    parser.add_argument('--interval',
        choices=['1d','1h','15m','5m','1m'],
        help='Pick up an interval from the list'
    )
    parser.add_argument('--streamtype',
        choices=['klines', 'continuous_klines']
    )
    return parser.parse_args(pargs)


if __name__== '__main__':
    ''' 
        Create Databases and Collections in a MongoDB database and/or Update Collections in a database

        # 1 DAY - SPOTMARGIN
        python3 obtain-data-klines.py \
        --createdb \
        --markettype spot_margin \
        --interval 1d \
        --portfoliosymbols \
        --streamtype klines
        
        ###################################
        ###################################
        
        # 1 MIN - SPOTMARGIN
        cd capture-data/ && \
        python3 obtain-data-klines.py \
        --updatedb \
        --markettype spot_margin \
        --interval 1m \
        --portfoliosymbols \
        --streamtype klines \
        && cd ..
        
        '''
    
    database_config = dict(
        db_host = '192.168.8.106', #raspi
        db_user = 'admin',
        db_pass = environ.get('mongodbadminpass')
    )
    
    polaris = PolarisBot(mongo_cred=database_config)
    
    obtain_data_klines(polaris)