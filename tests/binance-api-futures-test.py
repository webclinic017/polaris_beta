import unittest
from polaristools.polarisbot import BinanceConnection

binance = BinanceConnection()

''' 
    Binance futures market data.
    '''

class BinanceApiTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_futuresTestConnectivity(self):
        self.assertIsInstance(binance.futuresTestConnectivity(),dict)
    
    def test_futuresCheckserverTime(self):
        self.assertIn('serverTime',binance.futuresCheckserverTime())
    
    def test_futuresExchangeInformation(self):
        self.assertIsInstance(binance.futuresExchangeInformation(),dict)
    
    def test_futuresOrderBook(self):
        self.assertIsInstance(binance.futuresOrderBook(symbol='BNBUSDT'),dict)
    
    def test_futuresMarkPrice(self):
        self.assertIsInstance(binance.futuresMarkPrice(symbol='ADAUSDT'),dict)
    
    def test_futuresGetFundingRateHistory(self):
        self.assertIsInstance(binance.futuresGetFundingRateHistory(symbol='ADAUSDT'),list)
    
    def test_futuresTickerPriceChangeStatistics24h(self):
        self.assertIsInstance(binance.futuresTickerPriceChangeStatistics24h(),list)
    
    def test_futuresSymbolPriceTicker(self):
        self.assertIsInstance(binance.futuresSymbolPriceTicker(),list)
    
    def test_futuresOpenInterest(self):
        self.assertIsInstance(binance.futuresOpenInterest(symbol='ADAUSDT'),dict)
    
    def test_futuresOpenInterestStatistics(self):
        self.assertIsInstance(binance.futuresOpenInterestStatistics(symbol='ADAUSDT', period='5m'),list)
    
    def test_futuresTopTraderLongShortRatio(self):
        self.assertIsInstance(binance.futuresTopTraderLongShortRatio(ep_type='positions', symbol='ADAUSDT', period='5m'),list)
    
    def test_futuresLongShortRatio(self):
        self.assertIsInstance(binance.futuresLongShortRatio(symbol='ADAUSDT', period='5m'),list)
    
    def test_futuresTakerBuySellVolume(self):
        self.assertIsInstance(binance.futuresTakerBuySellVolume(symbol='ADAUSDT', period='5m'),list)
    
    def tearDown(self):
        pass
    
if __name__== '__main__':
    unittest.main()
