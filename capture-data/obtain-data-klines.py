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
    # difference= {'1000LUNC', '1000SHIB', 'LUNA2','LUNA',     'LUNC', 'SHIB'}
    #               fut         fut         fut    spot         spot    spot
    
    if arg.streamtype=='continuous_klines':
        coins=futures_busd
    elif arg.streamtype=='klines':
        coins=spot_usdt
    
    symbols = [coin for coin in coins]
    
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
    
    # parser.add_argument('--portfolio',
        # choices=['futures_busd', 'spot_usdt'],
        # help='Load data for a list of previously selected symbols'
    # )
    
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
        --interval 1d \
        --quotedasset usdt \
        --markettype spot_margin \
        --streamtype klines
            
            ###################################
            # 1 DAY - SPOT_MARGIN
            python3 obtain-data-klines.py \
            --updatedb \
            --interval 1d \
            --quotedasset usdt \
            --markettype spot_margin \
            --streamtype klines
        
        
        ###################################
        # 1 DAY - FUTURES_STABLE
        python3 obtain-data-klines.py \
        --createdb \
        --interval 1d \
        --quotedasset busd \
        --markettype futures_stable \
        --streamtype continuous_klines
        
            ###################################
            # 1 DAY - FUTURES_STABLE
            python3 obtain-data-klines.py \
            --updatedb \
            --interval 1d \
            --quotedasset busd \
            --markettype futures_stable \
            --streamtype continuous_klines
        
        ###################################
        # 1 MINUTE - FUTURES_STABLE
        python3 obtain-data-klines.py \
        --createdb \
        --interval 1m \
        --quotedasset busd \
        --markettype futures_stable \
        --streamtype continuous_klines
        
            ###################################
            # 1 MINUTE - FUTURES_STABLE
            python3 obtain-data-klines.py \
            --updatedb \
            --interval 1m \
            --quotedasset busd \
            --markettype futures_stable \
            --streamtype continuous_klines
        
        '''