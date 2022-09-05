from datetime import datetime

import backtrader as bt
import backtrader.indicators as btind

''' 
    <CODE_SNIPETS>
    
    ord_long = self.buy_bracket(
        limitprice = self.takeprofit_long,
        price      = close,
        stopprice  = self.stoploss_long,
        valid      = None,)
    
    self.takeprofit_long = close * (1+self.params.tp_k/100)
    self.stoploss_long = close * (1-self.params.sl_k/100)
    
    '''

class OverUnderMovAv(bt.Indicator):
    ''' CUSTOM INDICATORS. LATER '''
    lines = ('overunder',)
    params = dict(period=20, movav=btind.MovAv.Simple)

    plotinfo = dict(
        # Add extra margins above and below the 1s and -1s
        plotymargin=0.15,

        # Plot a reference horizontal line at 1.0 and -1.0
        plothlines=[1.0, -1.0],

        # Simplify the y scale to 1.0 and -1.0
        plotyticks=[1.0, -1.0])

    # Plot the line "overunder" (the only one) with dash style
    # ls stands for linestyle and is directly passed to matplotlib
    plotlines = dict(overunder=dict(ls='--'))

    def _plotlabel(self):
        # This method returns a list of labels that will be displayed
        # behind the name of the indicator on the plot

        # The period must always be there
        plabels = [self.p.period]

        # Put only the moving average if it's not the default one
        plabels += [self.p.movav] * self.p.notdefault('movav')

        return plabels

    def __init__(self):
        movav = self.p.movav(self.data, period=self.p.period)
        self.l.overunder = bt.Cmp(movav, self.data)

class BaseStratsCustom(bt.Strategy):
    params = dict(
        verbose = False,
        
        futures_like = True,
        enter_long = False,
        enter_short = False,
        
        ema = 100,
        aroon_timeperiod=14,
        
        leverage_factor = 1.0,
        margin = 0.6,
        
        tp_k = 2,
        sl_k = 2,
        trail = None,
    )
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        message = f'#({len(self)}) {dt.isoformat()} {txt}'
        print(message)
    
    def __init__(self):
        self.aroon = bt.talib.AROON(self.data.high, self.data.low, timeperiod=self.p.aroon_timeperiod)
        self.ema = bt.talib.EMA(timeperiod=self.p.ema)
        
        self.cross_up = bt.ind.CrossUp(self.aroon.aroonup, self.aroon.aroondown)
        self.cross_down = bt.ind.CrossDown(self.aroon.aroonup, self.aroon.aroondown)
        
        self.market_direction = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Rejected]:
            self.log('## ORDER REJECTED FROM BROKER ##')
        if order.status in [order.Completed]:
            if self.params.verbose:
                order_type = 'BUY EXECUTED'*order.isbuy() or 'SELL EXECUTED'*order.issell()
                message = f'##{order_type}## Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                self.log(message)
            else:
                return
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.market_direction = None
            if self.params.verbose:
                price_pctch = 100 * (self.data.close[0]-trade.price)/trade.price
                message = f'OPERATION PROFIT GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}, BARS ELAPSED: {trade.barlen}, Price change: {price_pctch:.2f}%'
                self.log(message)
        else:
            return
    
    def check_margin_call(self,leverage,margin,entryprice,next_price, market):
        perc_var_leveraged = ((next_price-entryprice)/entryprice) * leverage
        if market=='bull' and (perc_var_leveraged < 0) and abs(perc_var_leveraged) >= margin:
            return True
        elif market=='bear' and (perc_var_leveraged > 0) and abs(perc_var_leveraged) >= margin:
            return True
        else:
            return False
    
    def start(self):
        message = f'INITIAL BALANCE {self.broker.get_cash():.2f} usdt' 
        if self.params.verbose:
            self.log(message)
    
    def stop(self):
        message = f'FINAL BALANCE {self.broker.get_value():.2f} usdt'
        if self.params.verbose:
            self.log(message)
    
    def next(self):
        # volume = self.data.volume[0]
        close = self.data.close[0]
        ema = self.ema[0]
        
        leverage = self.params.leverage_factor
        margin = self.params.margin
        entryprice = self.position.price
        
        # ***** ***** BULL MARKET ***** *****
        condition_long = self.params.enter_long and (close > ema) and (self.cross_up)
        if (not self.position) and condition_long:
            # If an order is rejected by the broker this logic will fail.
            # This variable could generate a flag that comunicate right state to notify_order method.
            self.market_direction = 'bull' 
            
            order = self.buy(
                exectype=bt.Order.Limit,
                price=close,
                # valid=datetime.datetime.now() + datetime.timedelta(days=3)),
            )
        
        # ***** ***** BEAR MARKET ***** *****
        condition_short = self.params.enter_short and (close < ema) and (self.cross_down)
        if (not self.position) and condition_short:
            # If an order is rejected by the broker this logic will fail.
            # This variable could generate a flag that comunicate right state to notify_order method.
            self.market_direction = 'bear'
            
            order = self.sell(
                    exectype=bt.Order.Limit,
                    price=close,
                    # valid=datetime.datetime.now() + datetime.timedelta(days=3)),
                )
        
        # ***** ***** EXIT MARKET ***** *****
        if self.position: #AND FUTURES LIKE
            if self.check_margin_call(leverage, margin, entryprice, next_price=close, market=self.market_direction,):
                self.close()
                if self.params.verbose:
                    self.log('POSITION CLOSED BY MARGIN CALL !!')
            
            # *** EXIT LONG ***
            elif self.market_direction=='bull' \
                and (close<ema) and self.cross_down:
                
                self.close()
            
            # *** EXIT SHORT ***
            elif self.market_direction=='bear' \
                and self.cross_up:
                # and (close<ema) \
                
                self.close()


# VISUALIZATION ######################################
class PriceAction(bt.Strategy):
    def __init__(self):
        pass
    def next(self):
        pass

class Indicators(bt.Strategy):
    params = dict(
        adx=False,
        adx_period=14,
        
        atr=False,
        atr_period=14,
        
        rsi=False,    
        rsi_period=14,
        
        roc=False,
        roc_period=10,
        
        rocp=False,
        rocp_period=10,
        
        rocr=False,
        rocr_period=10,
        
        macd=False,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        
        bbands=False,
        bbands_period=5,
        bbands_nbdevup=2.0,
        bbands_nbdevdn=2.0,
        bbands_matype=0,
        
        # ema=False,
        ema_slow=False,
        ema_mid=False,
        ema_fast=False,
        
        obv=False,
        obv_price='close',
        
        psar=False,
        psar_acceleration=0.02, 
        psar_maximum=0.2,
        
        stochrsi=False,
        stochrsi_timeperiod= 14,
        stochrsi_fastk_period= 5,
        stochrsi_fastd_period= 3,
        stochrsi_fastd_matype= 0,
        
        aroon=False,
        aroon_timeperiod=14,
        
        pattern_doji=False,
        
        crossup=False,
        crossdown=False,
    )
    
    def __init__(self):
        if self.p.pattern_doji:
            self.pattern_doji = bt.talib.CDLDOJI(
                self.data.open,
                self.data.high,
                self.data.low,
                self.data.close,
            )
        if self.p.aroon:
            self.aroon = bt.talib.AROON(
                self.data.high,
                self.data.low,
                timeperiod = self.p.aroon_timeperiod,
            )
        if self.p.stochrsi:
            self.stochrsi = bt.talib.STOCHRSI(
                self.data.close,
                stochrsi_timeperiod = self.p.stochrsi_timeperiod,
                stochrsi_fastk_period = self.p.stochrsi_fastk_period,
                stochrsi_fastd_period = self.p.stochrsi_fastd_period,
                stochrsi_fastd_matype = self.p.stochrsi_fastd_matype,
            )
        if self.p.psar:
            self.psar = bt.talib.SAR(
                self.data.high,
                self.data.low,
                psar_acceleration=self.p.acceleration, 
                psar_maximum=self.p.maximum
            )
        if self.p.adx:
            self.adx = bt.talib.ADX(
                self.data.high,
                self.data.low,
                self.data.close,
                timeperiod=self.p.adx_period
            )
        if self.p.atr:
            self.atr = bt.talib.ATR(
                self.data.high,
                self.data.low,
                self.data.close,
                timeperiod=self.p.atr_period
            )
        if self.p.rsi:
            self.rsi = bt.talib.RSI(timeperiod=self.p.rsi_period)
        if self.p.roc:
            self.roc = bt.talib.ROC(timeperiod=self.p.roc_period)
        if self.p.rocp:
            self.rocp = bt.talib.ROCP(timeperiod=self.p.rocp_period)
        if self.p.rocr:
            self.rocr = bt.talib.ROCR(timeperiod=self.p.rocr_period)
        if self.p.macd:
            self.macd = bt.talib.MACD(
                fastperiod = self.p.macd_fast,
                slowperiod = self.p.macd_slow,
                signalperiod = self.p.macd_signal,
            )
        if self.p.bbands:
            self.bbands = bt.talib.BBANDS(
                self.data.close,
                timeperiod = self.p.bbands_period,
                nbdevup = self.p.bbands_nbdevup,
                nbdevdn = self.p.bbands_nbdevdn,
                matype = self.p.bbands_matype,
            )
        if self.p.obv:
            price={'open':self.data.open,'high':self.data.high,'low':self.data.low,'close':self.data.close}
            self.obv = bt.talib.OBV(
                price.get(self.p.obv_price), 
                self.data.volume
            )
        if self.p.ema_slow:
            self.ema_slow = bt.talib.EMA(timeperiod=self.p.ema_slow)
        if self.p.ema_mid:
            self.ema_mid = bt.talib.EMA(timeperiod=self.p.ema_mid)
        if self.p.ema_fast:
            self.ema_fast = bt.talib.EMA(timeperiod=self.p.ema_fast)
        
        if self.p.crossup:
            self.cross_up = bt.ind.CrossUp(self.aroon.aroonup, self.aroon.aroondown)
        if self.p.crossdown:
            self.cross_down = bt.ind.CrossDown(self.aroon.aroonup, self.aroon.aroondown)

    def next(self):
        pass


# TRADING STRATEGIES ######################################
class AroonPlusMa(bt.Strategy):
    params = dict(
            verbose = False,
            
            futures_like = True,
            enter_long = False,
            enter_short = False,
            
            ema = 100,
            aroon_timeperiod=14,
            
            leverage_factor = 1.0,
            margin = 0.6,
            
            tp_k = 2,
            sl_k = 2,
            trail = None,
        )
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        message = f'#({len(self)}) {dt.isoformat()} {txt}'
        print(message)        
    
    def __init__(self):
        self.aroon = bt.talib.AROON(
            self.data.high,
            self.data.low,
            timeperiod = self.p.aroon_timeperiod,
        )
        self.ema = bt.talib.EMA(timeperiod=self.p.ema)
        
        self.cross_up = bt.ind.CrossUp(self.aroon.aroonup, self.aroon.aroondown)
        self.cross_down = bt.ind.CrossDown(self.aroon.aroonup, self.aroon.aroondown)
        
        self.market_direction = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Rejected]:
            self.log('## ORDER REJECTED FROM BROKER ##')
        if order.status in [order.Completed]:
            if self.params.verbose:
                order_type = 'BUY EXECUTED'*order.isbuy() or 'SELL EXECUTED'*order.issell()
                message = f'##{order_type}## Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                self.log(message)
            else:
                return
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.market_direction = None
            if self.params.verbose:
                price_pctch = 100 * (self.data.close[0]-trade.price)/trade.price
                message = f'OPERATION PROFIT GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}, BARS ELAPSED: {trade.barlen}, Price change: {price_pctch:.2f}%'
                self.log(message)
        else:
            return
    
    def check_margin_call(self,leverage,margin,entryprice,next_price, market):
        perc_var_leveraged = ((next_price-entryprice)/entryprice) * leverage
        if market=='bull' and (perc_var_leveraged < 0) and abs(perc_var_leveraged) >= margin:
            return True
        elif market=='bear' and (perc_var_leveraged > 0) and abs(perc_var_leveraged) >= margin:
            return True
        else:
            return False
    
    def start(self):
        message = f'INITIAL BALANCE {self.broker.get_cash():.2f} usdt' 
        if self.params.verbose:
            self.log(message)
        
    def stop(self):
        message = f'FINAL BALANCE {self.broker.get_value():.2f} usdt'
        if self.params.verbose:
            self.log(message)
    
    def next(self):
        # volume = self.data.volume[0]
        close = self.data.close[0]
        ema = self.ema[0]
        
        leverage = self.params.leverage_factor
        margin = self.params.margin
        entryprice = self.position.price
        
        # ***** ***** BULL MARKET ***** *****
        condition_long = self.params.enter_long and (close > ema) and (self.cross_up)
        if (not self.position) and condition_long:
            # If an order is rejected by the broker this logic will fail.
            # This variable could generate a flag that comunicate right state to notify_order method.
            self.market_direction = 'bull' 
            
            order = self.buy(
                exectype=bt.Order.Limit,
                price=close,
                # valid=datetime.datetime.now() + datetime.timedelta(days=3)),
            )
        
        # ***** ***** BEAR MARKET ***** *****
        condition_short = self.params.enter_short and (close < ema) and (self.cross_down)
        if (not self.position) and condition_short:
            # If an order is rejected by the broker this logic will fail.
            # This variable could generate a flag that comunicate right state to notify_order method.
            self.market_direction = 'bear'
            
            order = self.sell(
                    exectype=bt.Order.Limit,
                    price=close,
                    # valid=datetime.datetime.now() + datetime.timedelta(days=3)),
                )
        
        # ***** ***** EXIT MARKET ***** *****
        if self.position: #AND FUTURES LIKE
            if self.check_margin_call(leverage, margin, entryprice, next_price=close, market=self.market_direction,):
                self.close()
                if self.params.verbose:
                    self.log('POSITION CLOSED BY MARGIN CALL !!')
            
            # *** EXIT LONG ***
            elif self.market_direction=='bull' \
                and (close<ema) and self.cross_down:
                
                self.close()
            
            # *** EXIT SHORT ***
            elif self.market_direction=='bear' \
                and self.cross_up:
                # and (close<ema) \
                
                self.close()

class EmaCrossTriple(bt.Strategy):
    params = dict(
        verbose = False,
        
        futures_like = True,
        enter_long = False,
        enter_short = False,
        
        ema_slow = 200,
        ema_mid = 70,
        ema_fast = 25,
        
        leverage_factor = 1.0,
        margin = 0.6,
        
        tp_k = 2,
        sl_k = 2,
        trail = None,
    )
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        message = f'#({len(self)}) {dt.isoformat()} {txt}'
        print(message)
    
    def __init__(self):
        self.ema_slow = bt.talib.EMA(timeperiod=self.params.ema_slow)
        self.ema_mid = bt.talib.EMA(timeperiod=self.params.ema_mid)
        self.ema_fast = bt.talib.EMA(timeperiod=self.params.ema_fast)
        
        self.cross_up = bt.ind.CrossUp(self.ema_fast,self.ema_mid)
        self.cross_down = bt.ind.CrossDown(self.ema_fast,self.ema_mid)
        
        self.takeprofit_long = None
        self.takeprofit_short = None
        self.stoploss_long = None
        self.stoploss_short = None
        
        self.market_direction = None
        self.entry_volume = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Rejected]:
            self.log('## ORDER REJECTED FROM BROKER ##')
        if order.status in [order.Completed]:
            if self.params.verbose:
                order_type = 'BUY EXECUTED'*order.isbuy() or 'SELL EXECUTED'*order.issell()
                message = f'##{order_type}## Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                self.log(message)
            else:
                return
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.market_direction = None
            if self.params.verbose:
                price_pctch = 100 * (self.data.close[0]-trade.price)/trade.price
                message = f'OPERATION PROFIT GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}, BARS ELAPSED: {trade.barlen}, Price change: {price_pctch:.2f}%'
                self.log(message)
        else:
            return
    
    def check_margin_call(self,leverage,margin,entryprice,next_price, market):
        perc_var_leveraged = ((next_price-entryprice)/entryprice) * leverage
        if market=='bull' and (perc_var_leveraged < 0) and abs(perc_var_leveraged) >= margin:
            return True
        elif market=='bear' and (perc_var_leveraged > 0) and abs(perc_var_leveraged) >= margin:
            return True
        else:
            return False
    
    def start(self):
        message = f'INITIAL BALANCE {self.broker.get_cash():.2f} usdt' 
        if self.params.verbose:
            self.log(message)
        
    def stop(self):
        message = f'FINAL BALANCE {self.broker.get_value():.2f} usdt'
        if self.params.verbose:
            self.log(message)
    
    def next(self):
        low = self.data.low[0]
        high = self.data.high[0]
        close = self.data.close[0]
        # volume = self.data.volume[0]
        
        leverage = self.params.leverage_factor
        margin = self.params.margin
        entryprice = self.position.price
        
        # * BULL MARKET *
        condition_long = (self.ema_mid[0] > self.ema_slow[0]) and (self.cross_up)
        enter_long = not self.position and (self.params.enter_long and condition_long)
        if enter_long:
            self.market_direction = 'bull' #If an order is rejected by the broker this logic will fail.
            self.takeprofit_long = close * (1+self.params.tp_k/100)
            self.stoploss_long = close * (1-self.params.sl_k/100)
            
            ord_long = self.buy_bracket(
                limitprice = self.takeprofit_long,
                price      = close,
                stopprice  = self.stoploss_long,
                valid      = None,
            )
        
        # * BEAR MARKET *
        condition_short = (self.ema_mid[0] < self.ema_slow[0]) and (self.cross_down)
        enter_short = not self.position and (self.params.enter_short and condition_short)
        if enter_short:
            self.market_direction = 'bear' #If an order is rejected by the broker this logic will fail.
            self.takeprofit_short = close * (1-self.params.tp_k/100)
            self.stoploss_short = close * (1+self.params.sl_k/100)
            self.entry_volume = self.data.volume[0]
            
            ord_short = self.sell_bracket(
                limitprice = self.takeprofit_short,
                price      = close,
                stopprice  = self.stoploss_short,
                valid      = None,
            )
        
        # * EXIT MARKET *
        if self.position:
            # Next_price should be 'LOW' when market is bear and 'HIGH' when bull.
            # Method logic is weak because money loses could are bigger than real funds.
            if self.check_margin_call(
                                    leverage,
                                    margin,
                                    entryprice,
                                    next_price=close,
                                    market=self.market_direction
                                    ):
                if self.params.verbose:
                    self.log('POSITION CLOSED BY MARGIN CALL !!')
                self.close()

class Momentum(bt.Strategy):
    params = dict(
        verbose = False,
        
        futures_like = True,
        enter_long = False,
        enter_short = False,
        
        ema_slow = 200,
        ema_mid = 70,
        ema_fast = 25,
        
        rsi = 14,
        
        leverage_factor = 1.0,
        margin = 0.6,
        
        tp_k = 2,
        sl_k = 2,
        trail = None,
    )
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        message = f'#({len(self)}) {dt.isoformat()} {txt}'
        print(message)
    
    def __init__(self):
        # self.ema_slow = bt.talib.EMA(timeperiod=self.params.ema_slow)
        # self.ema_mid = bt.talib.EMA(timeperiod=self.params.ema_mid)
        # self.ema_fast = bt.talib.EMA(timeperiod=self.params.ema_fast)
        
        # self.cross_up = bt.ind.CrossUp(self.ema_fast,self.ema_mid)
        # self.cross_down = bt.ind.CrossDown(self.ema_fast,self.ema_mid)
        
        self.rsi = bt.talib.RSI(timeperiod=self.params.rsi)
        
        self.takeprofit_long = None
        self.takeprofit_short = None
        
        self.stoploss_long = None
        self.stoploss_short = None
        
        self.market_direction = None
        self.entry_volume = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Rejected]:
            self.log('## ORDER REJECTED FROM BROKER ##')
        if order.status in [order.Completed]:
            if self.params.verbose:
                order_type = 'BUY EXECUTED'*order.isbuy() or 'SELL EXECUTED'*order.issell()
                message = f'##{order_type}## Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                self.log(message)
            else:
                return
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.market_direction = None
            if self.params.verbose:
                price_pctch = 100 * (self.data.close[0]-trade.price)/trade.price
                message = f'OPERATION PROFIT GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}, BARS ELAPSED: {trade.barlen}, Price change: {price_pctch:.2f}%'
                self.log(message)
        else:
            return
    
    def check_margin_call(self,leverage,margin,entryprice,next_price, market):
        perc_var_leveraged = ((next_price-entryprice)/entryprice) * leverage
        if market=='bull' and (perc_var_leveraged < 0) and abs(perc_var_leveraged) >= margin:
            return True
        elif market=='bear' and (perc_var_leveraged > 0) and abs(perc_var_leveraged) >= margin:
            return True
        else:
            return False
    
    def start(self):
        message = f'INITIAL BALANCE {self.broker.get_cash():.2f} usdt' 
        if self.params.verbose:
            self.log(message)
    
    def stop(self):
        message = f'FINAL BALANCE {self.broker.get_value():.2f} usdt'
        if self.params.verbose:
            self.log(message)
    
    def next(self):
        low = self.data.low[0]
        high = self.data.high[0]
        close = self.data.close[0]
        # volume = self.data.volume[0]
        
        leverage = self.params.leverage_factor
        margin = self.params.margin
        entryprice = self.position.price
        
        # * BULL MARKET *
        
        
        # * BEAR MARKET *
        
        # * EXIT MARKET *


if __name__== '__main__':
    pass