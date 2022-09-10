import argparse
from os import environ, getcwd, chdir
from time import sleep

from polaristools.polarisbot import PolarisBot


''' 
    (1) Download data through the API and persist it in a mongo database.
        Create new collections from scratch or update current collections.
        
    (2) Use it in commands terminal.
    '''


def obtain_data_klines(polaris, args=None):
    # Because logging.
    current = getcwd()
    if not current.endswith('capture-data'):
        chdir('/home/llagask/Trading/polaris_beta/capture-data')
    
    arg = parse_inputs(args)

    # current: futures busd (1d)
    coins = [
        'GMT',
        'ANC',
        'APE','LDO',
        'FIL','ADA','ETC','BNB',
        'AVAX','ETH','GAL','DOT',
        'DOGE','LTC','NEAR','XRP',
        'ICP',
        'SOL',
        'BTC','MATIC',
    ]
    
    symbols = [(coin+arg.quotedasset).upper() for coin in coins]

    kwargs = dict(
        symbols      = symbols, 
        interval     = arg.interval,
        quoted_asset = arg.quotedasset,
        stream_type  = arg.streamtype,
        market_type  = arg.markettype,
    )
    if arg.createdb:
        polaris.createDatabaseKlines(**kwargs)
    elif arg.updatedb:
        polaris.updateDatabaseKlines(**kwargs)
    chdir('/home/llagask/Trading/polaris_beta')

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
    
    parser.add_argument('--portfolio',
        action='store_true',
        help='Load data for a list of previously selected symbols'
    )
    
    parser.add_argument('--interval',
        choices=['1d','1m'],
        help='Pick up an interval from the list'
    )
    parser.add_argument('--quotedasset',
        choices=['usdt','busd','btc']
    )
    parser.add_argument('--markettype',
        choices=['spot_margin', 'futures_stable', 'futures_coins']
    )
    parser.add_argument('--streamtype',
        choices=['klines', 'continuous_klines']
    )
    
    return parser.parse_args(pargs)


if __name__== '__main__':
    database_config = dict(
        db_host = '192.168.8.106', #raspi
        db_user = 'admin',
        db_pass = environ.get('mongodbadminpass')
    )
    polaris = PolarisBot(mongo_cred=database_config)
    
    obtain_data_klines(polaris)

    ''' 
        ###################################
        # 1 DAY - SPOT_MARGIN
        python3 obtain-data-klines.py \
        --createdb \
        --markettype spot_margin \
        --interval 1d \
        --symbols_1m \
        --streamtype klines
        
        
        ###################################
        # 1 DAY - FUTURE_STABLE
        python3 obtain-data-klines.py \
        --createdb \
        --markettype spot_margin \
        --interval 1d \
        --symbols_1m \
        --streamtype klines
        
        '''
        
    ''' 
        ###################################
        # 1 DAY - FUTURES_STABLE
        python3 obtain-data-klines.py \
        --updatedb \
        --interval 1d \
        --quotedasset busd \
        --streamtype continuous_klines \
        --markettype futures_stable
        
        ###################################
        # 1 MIN - FUTURES_STABLE
        python3 obtain-data-klines.py \
        --updatedb \
        --interval 1m \
        --quotedasset busd \
        --streamtype continuous_klines \
        --markettype futures_stable
        
        ###################################
        
        # 1 MIN - SPOTMARGIN
        python3 obtain-data-klines.py \
        --updatedb \
        --markettype spot_margin \
        --streamtype klines \
        --portfolio \
        --interval 1m \
        --quotedasset usdt \
        
        '''