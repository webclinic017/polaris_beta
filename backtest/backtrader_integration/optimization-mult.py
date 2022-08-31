from __future__ import (absolute_import, division, print_function,unicode_literals)
from datetime import datetime
import os
import pickle

import backtrader as bt
from numpy import nan as npnan
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
        return pd.DataFrame()
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
    analyzers = [
            'pnl_net','trades',
            'won','lost',
            'long_won','short_won',
            'long_lost','short_lost',
            'longs_pnl','shorts_pnl',
            'moneydown_max',
            ]
    params = [
            'aroon_timeperiod',
            'ema','leverage_factor',
            ]
    if not analyzers[0] in dataframe.columns:
        print(f'FAILED TEST (invalid analyzers) ON symbol: {symbol}, tf: {timeframe}.')
        # df_anyz_mt = pd.DataFrame([{key:npnan for key in analyzers}])
        # dataframe = pd.concat([dataframe, df_anyz_mt], axis=1).copy()
        return dataframe
    elif dataframe.empty:
        print(f'FAILED TEST (empty data, invalid params) ON symbol: {symbol}, tf: {timeframe}')
        return dataframe
    best5 = dataframe[analyzers+params].nlargest(5, by_col).copy()
    worse3 = dataframe[analyzers+params].nsmallest(3, by_col).copy()
    bs = f'{symbol} {timeframe} BEST_5' 
    ws = f'{symbol} {timeframe} WORSE_3'
    best_horse = pd.concat([best5,worse3], keys=[bs, ws], axis=0)
    return best_horse

def loop_optimizations(backtest_params, symbols, timeframes):
    # Store each results Dataframe here.
    symbols_df = pd.DataFrame()
    
    it_counter = 0
    total_it = int(len(symbols)*len(timeframes))
    
    print(f"""Try backtest against:
    {symbols} {timeframes}
    Expected iterations : {total_it}
    """)
    
    for symbol in symbols:
        
        # rolling values:init.
        backt_params = backtest_params.copy()
        prev_tf = 0
        curr_tf = 0
        
        for idx,timeframe in enumerate(timeframes):
            backt_params.update(dict(symbol=symbol, timeframe=timeframe))
            
            # RUN BACKTEST.
            backtest = optimization(**backt_params)
            
            # *Update rolling values.
            # if idx==0:
            #     prev_tf = int(timeframe[:-1])
            # curr_tf = int(timeframe[:-1])
            # if curr_tf>0:
            #     paramconst = (prev_tf / curr_tf)*10
            #     ema_timeperiod                                  = backt_params['parameters'].get('ema')
            #     aroon_timeperiod                                = backt_params['parameters'].get('aroon_timeperiod')
            #     backt_params['parameters']['ema']               = [num+paramconst for num in ema_timeperiod]
            #     backt_params['parameters']['aroon_timeperiod']  = [num+paramconst for num in aroon_timeperiod]
            #     prev_tf=curr_tf
            
            df = parse_analyzers(backtest)
            best5_worse3 = filter_results(dataframe=df, symbol=symbol, timeframe=timeframe, by_col='pnl_net')
            
            # First iteration.
            if symbols_df.empty:
                symbols_df = best5_worse3
            else:
                symbols_df = pd.concat([symbols_df, best5_worse3], axis=0)
            
            it_counter+=1
            now = datetime.now()
            print(f'Iteration #{it_counter} of {total_it}. At {now}. SYMBOL: {symbol} TIMEFRAME: {timeframe}')
    return symbols_df


if __name__== '__main__':
    polaris = PolarisBot()
    
    symbols    = [
        # 'BTCUSDT',
        # 'DOGEUSDT',
        'BNBUSDT',
        # 'ETHUSDT'
    ]              #len 4
    timeframes = [
        '240m',
        # '120m',
        # '60m',
        # '30m',
        # '15m'
    ]          #len 5
    
    hyp_params = dict(
        enter_long          = True,
        enter_short         = True,
        ema                 = list(range(10, 51, 5)), #240m optimized.
        aroon_timeperiod    = list(range(10, 51, 5)), #240m optimized.
        leverage_factor     = 1.0,
    )
    backtest_params = dict(
        cash = 100,
        sizer = 20,
        comm = 0.05,
        sample = {'start':'2022-01-01', 'end':'2022-08-25'},
        custom_strategy = mystrategies.AroonPlusMa,
        parameters = hyp_params
    )
    
    opts_df = loop_optimizations(
        symbols=symbols,
        timeframes=timeframes,
        backtest_params=backtest_params,
    )
    
    # PERSIST RESULTS
    if not os.getcwd().endswith('backtrader_integration'):
        os.chdir('backtest/backtrader_integration')
    now=datetime.now()
    name='aroon strategy'
    filename = f'logs/OPT-{name}-{now}.pckl'
    opts_df.to_pickle(path=filename)