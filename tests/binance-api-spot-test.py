import unittest
from polaristools.polarisbot import BinanceConnection

binance = BinanceConnection()

''' 
    binance spot user account and
    market data, ideally separated.
    '''

class BinanceApiTest(unittest.TestCase):
    def setUp(self):
        pass
    
    # *** SPOT ENDPOINTS***
    def test_systemStatus(self):
        self.assertIsInstance(binance.systemStatus(),str)
    
    def test_allCoinsInfo(self):
        self.assertIsInstance(binance.allCoinsInfo(),list)
    
    def test_accountStatus(self):
        self.assertIsInstance(binance.accountStatus(),dict)
    
    def test_accountApiTradingStatus(self):
        self.assertIsInstance(binance.accountApiTradingStatus(),dict)
    
    # def test_(self):
    #     self.assertIsInstance(,dict)
    
    # def test_(self):
    #     self.assertIsInstance(,dict)
    
    def tearDown(self):
        pass
    
if __name__== '__main__':
    unittest.main()
