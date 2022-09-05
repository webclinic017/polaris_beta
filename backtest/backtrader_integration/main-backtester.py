''' 
    Actually works
    pip install matplotlib==3.2.2
    '''
from __future__ import (absolute_import, division, print_function,unicode_literals)
import argparse
from datetime import datetime
# from os import environ, chdir

# import pandas as pd
import pdmongo as pdm
import backtrader as bt

from polaristools.polarisbot import PolarisBot
from strategies import mystrategies


class PandasData_Extend(bt.feeds.PandasData):
    lines = (
        'open',
        'high',
        'low',
        'close',
        'volume',
    )
    params = (
        ('open_time', None),
        ('open', 0),
        ('high', 1),
        ('low', 2),
        ('close', 3),
        ('volume', 4),
    )


def add_data_to_cerebro(df_binary:str=None, sample:dict={}, args=None,):
    polaris = PolarisBot()
    arg = parse_inputs(args)
    
    symbol = arg.symbol.upper()
    timeframe = arg.timeframe
    filename = f'df_klines_{symbol}_{timeframe}'
    
    df_binary   = filename
    df = polaris.dataframeFromBinary(df_binary)
    
    if arg.sample_date:
        sample.update(**eval('dict(' + arg.sample_date + ')')) 
        df = df.loc[sample.get('start'):sample.get('end')]
    elif arg.sample_batch:
        df = df.iloc[-arg.sample_batch:]
    
    if timeframe == '1d':
        tframe = bt.TimeFrame.Days
        compression = 1
    else:
        tframe = bt.TimeFrame.Minutes
        compression = int(timeframe[:-1])
    
    # df = polaris.dataframeFromBinary(df_binary)
    
    # if sample:
        # df = df.loc[sample.get('start'):sample.get('end')]
    
    # datas0 = bt.feeds.PandasData(
    datas0 = PandasData_Extend(
        dataname = df,
        name = df_binary[10:],
        timeframe = tframe, 
        compression = compression,
    )
    return datas0

def run_cerebro(data, data_dual=None, args=None,):
    # DEFAULT CONFIG
    initial_cash=200.00
    sizer_pct=20
    comm_broker=0.005
    leverage_factor=1
    margin = 0.6
    
    arg = parse_inputs(args)
    # BOOLEAN FLAGS
    plot_bt = arg.plot
    verbose = arg.verbose
    write_csv = arg.writecsv
    
    csvname = arg.csvname # give a filename to csv.
    
    # *** CHOOSE AN ACTION ***
    logic_feed = arg.logic
    indicators = arg.indicators
    priceaction = arg.priceaction
    renko = arg.renko
    renko_dual = arg.renkodual
    heikinashi = arg.heikinashi
    optimization = arg.optimization
    
    strat_options = {
        'momentum':mystrategies.Momentum,
        'emacrosstriple':mystrategies.EmaCrossTriple,
        'aroon_plus_ma':mystrategies.AroonPlusMa,
    }
    
    plot_args = dict(style=arg.plotstyle)
    strat_params = arg.strat_params
    cerebro_params = arg.cerebro_params
    params_s = {}
    params_c = {}
    
    # *** INSTANTIATE CEREBRO ***
    cerebro = bt.Cerebro()
    
    # *** DATA FILTERS ***
    if renko or renko_dual:
        plot_args = dict(style='candle')
        filter_kwargs = dict(
            # hilo=False, autosize=20.0, align=1.0,
        )
        if renko_dual:
            cerebro.adddata(data)
            data1 = data.clone()
            data1.addfilter(bt.filters.Renko,**filter_kwargs)
            cerebro.adddata(data1)
        else:
            data.addfilter(bt.filters.Renko,**filter_kwargs)
        
    elif heikinashi:
        plot_args = dict(style='candle')
        filter_kwargs = dict()
        data.addfilter(
            bt.filters.HeikinAshi,
            **filter_kwargs
        )
    
    # *** ADD DATA
    if not renko_dual:
        cerebro.adddata(data)
    if data_dual is not None:
        # when is dual, this is the daily data. 
        # Previous has to be minutes.
        cerebro.adddata(data_dual)
    
    # *** RETRIEVE STRATEGY PARAMETERS FROM CLI.
    if strat_params is not None:
        params_s.update(**eval('dict(' + strat_params + ')'))
        # *** BORROW PARAMS FROM STRATEGY TO CEREBRO.
        leverage_factor = float(params_s.get('leverage_factor', 1))
    
    if cerebro_params is not None:
        params_c.update(**eval('dict(' + cerebro_params + ')'))
        initial_cash = float(params_c.get('initial_cash', initial_cash))
        sizer_pct = float(params_c.get('sizer_pct', sizer_pct))
        comm_broker = float(params_c.get('comm_broker', comm_broker))
    
    # *** BROKER CONFIGURATION
    # cerebro.broker = bt.brokers.BackBroker(slip_perc=0.005)  # 0.5%
    cerebro.broker.set_cash(initial_cash)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=sizer_pct)
    cerebro.broker.setcommission(
        commission = comm_broker,
        mult = leverage_factor,
    )
    
    # *** ADD ANALYZERS.
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='systemquality')
    
    # *** MISCELLANEOUS.
    if write_csv and not optimization:
        path = '/home/llagask/Trading/polaris_beta/backtest/backtrader_integration/logs'
        filename = f'{path}/{csvname}.log'
        cerebro.addwriter(bt.WriterFile,out=filename,csv=False,)
    if verbose:
        params_s.update({'verbose':True})
    
    if logic_feed is not None:
        mystrat = strat_options.get(logic_feed)
    
    # *** *** ADD STRATEGY *** ***
    if optimization:
        cerebro.optstrategy(mystrat,**params_s,)
    elif indicators:
        cerebro.addstrategy(mystrategies.Indicators, **params_s )
    elif renko or renko_dual or heikinashi or priceaction:
        cerebro.addstrategy(mystrategies.PriceAction, **params_s )
    else:
        cerebro.addstrategy(mystrat,**params_s,)
    
    # *** RUN CEREBRO ***
    cerebro.run()
    
    if plot_bt and not optimization:
        cerebro.plot(**plot_args)

def parse_inputs(pargs=None):
    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    bt_log = f'btlog_{timestamp}'
    
    parser = argparse.ArgumentParser(
        description="MAIN FUNCTIONALITIES: priceaction, renko, indicators"
    )
    
    # ***DATA ARGS
    parser.add_argument('--symbol',
        action='store',
        type=str,
        help='add a description later'
    )
    parser.add_argument('--timeframe',
        action='store',
        type=str,
        default='1d',
        help='available options: 1m,3m,5m,10m,15m,30m,60m,120m,240m'
    )
    parser.add_argument('--sample_date',
        action='store',
        type=str,
        default='',
        help="e.g: start='2022-01-01',end='2022-06-01' "
    )
    parser.add_argument('--sample_batch',
        action='store',
        type=int,
        default=500,
        help="Enter a positive integer. e.g:500"
    )
    ############################################################
    
    # ***CEREBRO CONFIG
    parser.add_argument('--cerebro_params',
        action='store',
        type=str,
        help='Add parameters as a single string. e.g: "initial_cash=1000, commision=0.005" ',
    )
    parser.add_argument('--plot',
        action='store_true',
        help='Plot results in a external window.'
    )
    parser.add_argument('--optimization',
        action='store_true',
        help='Run parameters optimization instead of backtest.'
    )
    parser.add_argument('--plotstyle',
        action='store',
        type=str,
        default='line',
        help='Options: line, bar, candle'
    )
    parser.add_argument('--verbose',
        action='store_true',
        help='Show backtest in stdout.'
    )
    parser.add_argument('--writecsv',
        action='store_true',
        help='Persist logs as csv file.'
    )
    parser.add_argument('--csvname',
        action='store',
        type=str,
        default=bt_log,
        help='Give a name to csv file. e.g: bt_log_01.'
    )
    parser.add_argument('--indicators',
        action='store_true',
        help='Show desired indicators.'
    )
    parser.add_argument('--priceaction',
        action='store_true',
        help='Show only price and volume.'
    )
    parser.add_argument('--renko',
        action='store_true',
        help='Show RENKO blocks.'
    )
    parser.add_argument('--renkodual',
        action='store_true',
        help='Show RENKO blocks against candlesticks.'
    )
    parser.add_argument('--heikinashi',
        action='store_true',
        help='Show OHLC as Heikin Ashi.'
    )
    ############################################################
    
    # ***STRATEGY PARAMS
    parser.add_argument('--logic',
        action='store',
        type=str,
        choices=['momentum','emacrosstriple','aroon_plus_ma'],
        help='Add a strategy for test.'
    )
    parser.add_argument('--strat_params',
        action='store',
        type=str,
        help='Add parameters as a single string. e.g: "period=100, lookback=5" ',
    )
    
    return parser.parse_args(pargs)


if __name__== '__main__':
    
    # *** PREPARE DATA FOR BACKTEST
    input_data = add_data_to_cerebro()

    # *** RUN BACKTEST WITH ALL PARAMETERS ***
    run_cerebro(data=input_data)