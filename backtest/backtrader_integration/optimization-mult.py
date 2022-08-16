from __future__ import (absolute_import, division, print_function,unicode_literals)
from datetime import datetime
from os import getcwd
import pickle

import backtrader as bt
import pandas as pd

from polaristools.polarisbot import PolarisBot
from strategies import mystrategies


def optimization(
                symbol:str,
                timeframe:str,
                cash:int,
                sizer:int,
                comm:float,
                sample:dict,
                custom_strategy:mystrategies,
                parameters:dict
                ):
    cerebro = bt.Cerebro()
    
    cerebro.broker.set_cash( cash )
    cerebro.addsizer(bt.sizers.PercentSizer, percents=sizer)
    cerebro.broker.setcommission(commission=comm, mult=parameters.get('leverage_factor'))
    
    if timeframe == '1d':
        tframe = bt.TimeFrame.Days
    else:
        tframe = bt.TimeFrame.Minutes
    
    filename = f'df_klines_{symbol}_{timeframe}'
    df = polaris.dataframeFromBinary(filename)
    if sample:
        df = df.loc[sample.get('start'):sample.get('end')].copy()
    
    feed = bt.feeds.PandasData(dataname=df, timeframe=tframe, compression = int(timeframe[:-1]))
    cerebro.adddata(feed)
    
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    cerebro.optstrategy(custom_strategy, **parameters)
    backtests = cerebro.run()
    
    return backtests

def parse_analyzers(backtests):
    try:
        all_params = [dict(zip(
                list(x[0].params._getkeys()),
                list(x[0].params._getvalues()),
            ))for x in backtests]
        df_params = pd.DataFrame(all_params)
        df_params.drop(columns=['verbose'], inplace=True)
    except:
        print('SOMETHING HAS FAILED WHILE TRYING TO RETRIEVE THE PARAMETERS FROM STRATEGY.', __main__)
        return
    try:
        trades = [dict(
            pnl_net         = x[0].analyzers.tradeanalyzer.get_analysis()['pnl']['net']['total'], 
            trades          = x[0].analyzers.tradeanalyzer.get_analysis()['total']['total'], 
            won             = x[0].analyzers.tradeanalyzer.get_analysis()['won']['total'], 
            lost            = x[0].analyzers.tradeanalyzer.get_analysis()['lost']['total'],
            
            long_won        = x[0].analyzers.tradeanalyzer.get_analysis()['long']['won'],
            short_won       = x[0].analyzers.tradeanalyzer.get_analysis()['short']['won'],
            
            long_lost       = x[0].analyzers.tradeanalyzer.get_analysis()['long']['lost'],
            short_lost      = x[0].analyzers.tradeanalyzer.get_analysis()['short']['lost'],
            
            longs_pnl       = x[0].analyzers.tradeanalyzer.get_analysis()['long']['pnl']['total'],
            shorts_pnl      = x[0].analyzers.tradeanalyzer.get_analysis()['short']['pnl']['total'],
            
            moneydown_max   = x[0].analyzers.drawdown.get_analysis()['max']['moneydown'],
            )for x in backtests
        ]
        df_trades = pd.DataFrame(trades)
        df_results = pd.concat([df_params, df_trades], axis=1)
        return df_results
    except:
        print('FAILED PARSING ANALYZERS')
        return pd.DataFrame()
        # return df_params

def filter_results(dataframe, symbol:str, timeframe:str, by_col:str):
    if dataframe.empty:
        print(f'FAILED TEST ON symbol: {symbol}, tf: {timeframe}')
        return dataframe
    labels = ['pnl_net','won','lost',
            'trades','moneydown_max',
            'long_won','long_lost',
            'short_won','short_lost',
            'longs_pnl','shorts_pnl',
            'leverage_factor','aroon_timeperiod','ema',]
    best5 = dataframe[labels].nlargest(5, by_col)
    worse3 = dataframe[labels].nsmallest(3, by_col)
    
    bs = f'{symbol} {timeframe} BEST_5' 
    ws = f'{symbol} {timeframe} WORSE_3'
    best_horse = pd.concat([best5,worse3], keys=[bs, ws], axis=0)
    
    return best_horse
    
def dataframeToBinary(dataframe:pd.DataFrame, name:str):
    filename = f'logs/OPT-{name}.pckl'
    with open(filename, 'wb') as bin_df:
        pickle.dump(dataframe, bin_df)
    print(f'{filename} persisted as binary ok')
    
def dataframeToBinary(dataframe:pd.DataFrame, name:str):
    filename = f'logs/OPT-{name}.pckl'
    with open(filename, 'wb') as bin_df:
        pickle.dump(dataframe, bin_df)
    print(f'{filename} persisted as binary ok')
    
def dataframeFromBinary(name:str):
    filename = f'logs/OPT-{name}.pckl'
    try:
        df_bin = open(filename, 'rb')
        dataframe = pickle.load(df_bin)
        df_bin.close()
        return dataframe
    except:
        print(f'Filename: {filename} does not exists yet.', __name__)
        return None
        

if __name__== '__main__':
    
    polaris = PolarisBot()
    
    # LOOP #20 - RUN Multiple tests
    ema                 = list(range(50, 101, 10))
    aroon_timeperiod    = list(range(50, 101, 10))
    
    