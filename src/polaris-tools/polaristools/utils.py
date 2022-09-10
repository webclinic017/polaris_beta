from datetime import datetime
import inspect
import logging
import sys
from time import time

import dateparser
from pandas import DataFrame, to_datetime
# import pytz


def historicalKlinesParser(klines:list):
    """
        Convert object raw kline to DataFrame
        obtained from the api
        """
    set_index=False
    columns_name = [ 'open_time','open','high','low','close',
                    'volume','close_time','quote_asset_volume',
                    'number_of_trades','taker_buy_base_asset_volume',
                    'taker_buy_quote_asset_volume','ignore'
                    ]
    df = DataFrame(data=klines, columns=columns_name)
    df['open_time'] = to_datetime(df['open_time'],   unit='ms')
    df['close_time'] = to_datetime(df['close_time'],  unit='ms')
    tofloat64 = [ 
            'open','high','low','close','volume',
            'quote_asset_volume',
            'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume'
    ]
    df[tofloat64] = df[tofloat64].astype('float64') 
    df.drop('ignore', axis=1, inplace=True)
    if set_index:
            df.set_index(df['open_time'], inplace=True)
    return df

def logger_func(logger_name,filename):
	# logger = logging.getLogger(__name__)
	logger = logging.getLogger(logger_name)
	
	# Create handlers
	c_handler = logging.StreamHandler(sys.stdout)
	f_handler = logging.FileHandler(filename=filename)
	c_handler.setLevel(logging.INFO)
	f_handler.setLevel(logging.WARNING)
	
	# Create formatters and add it to handlers
	c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
	f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	c_handler.setFormatter(c_format)
	f_handler.setFormatter(f_format)
	
	# Add handlers to the logger
	logger.addHandler(c_handler)
	logger.addHandler(f_handler)
	
	return logger

def date_to_milliseconds(date_str: str) -> int():
    """
        Convert UTC date to milliseconds
        If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
        See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/
        :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
        """
    epoch_cero  = datetime.utcfromtimestamp(0)#.replace(tzinfo=pytz.utc)
    date_string = dateparser.parse(date_str, settings={'TIMEZONE': "UTC"})
    return int((date_string - epoch_cero).total_seconds() * 1000.0)

def interval_to_milliseconds(interval: str) -> int():
    """
        Convert a Binance interval string to milliseconds
		:param interval: Binance interval string, e.g.: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
		:return:
		int value of interval in milliseconds
		None if interval prefix is not a decimal integer
		None if interval suffix is not one of m, h, d, w
		"""
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
    }
    try:
        return int(interval[0]) * seconds_per_unit[interval[-1]] * 1000
    except (ValueError, KeyError):
        return None

def convert_ts_str(ts_str):
    if ts_str is None:
        return ts_str
    if type(ts_str) == int:
        return ts_str
    return date_to_milliseconds(ts_str)

def latest_valid_timestamp(timeframe):
    ''' 
        retunr last valid timestamp in ms
        closed kline
        '''
    return int((time()*1000) - timeframe)

def parse_snapshotvos(snapshotVos:list):
    if snapshotVos:
        # SPOT
        snapshotvos = snapshotVos.copy()
        for idx,snapshot in enumerate(snapshotvos):
            snapshotvos[idx]['updateTime'] = datetime.fromtimestamp(snapshot.get('updateTime')/1000)
            snapshotvos[idx].update({'totalAssetOfBtc': snapshot['data'].get('totalAssetOfBtc')})
            for balance in snapshot['data']['balances']:
                if float(balance.get('free')) > 0:
                    snapshotvos[idx].update({balance.get('asset') : [float(balance.get('free')), float(balance.get('locked'))] })
            snapshotvos[idx].pop('data')
        # return snapshotvos[-1]
        df = DataFrame(snapshotvos)
        df.set_index(df.updateTime, inplace=True)
        df.drop(['updateTime'], axis=1, inplace=True)
        df.sort_values(by='updateTime', ascending=False, inplace=True)
        return df
    else:
        return []


if __name__== '__main__':
	
	from polaristools.utils import *
	interval = interval_to_milliseconds('1d')
	print(interval)
	
	logger = logger_func()
	logger.info('This is an info : %s'%mensaje)
	logger.warning('This is a warning : %s'%mensaje)
	logger.error('This is an error')
	logger.critical('This is an critical')
	
	var = [
            {"asset":"ADA","free":"180.8","locked":"0"},
            {"asset":"ADA","free":"180.8","locked":"0"},
            {"asset":"BNB","free":"0.0002626","locked":"0"},
            {"asset":"BNB", "free":"0.0002626", "locked":"0"},
            {"asset":"BUSD", "free":"37.4469256", "locked":"0"},
            {"asset":"BUSD" ,"free":"37.4469256", "locked":"0"}
            ]