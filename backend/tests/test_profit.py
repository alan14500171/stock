import unittest
from routes.profit import get_profit_stats, refresh_stock_prices
from flask import Flask, session
from services.currency_checker import CurrencyChecker
from unittest.mock import patch, MagicMock

class TestProfit(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        session['user_id'] = 1

    def tearDown(self):
        self.app_context.pop()

    @patch('routes.profit.db')
    @patch('routes.profit.checker')
    def test_profit_calculation(self, mock_checker, mock_db):
        # 模拟数据库返回的持仓数据
        mock_db.fetch_all.return_value = [
            {
                'market': 'USA',
                'code': 'NVDA',
                'stock_name': '英伟达',
                'full_name': 'NVDA:NASDAQ',
                'quantity': 100,
                'total_buy': 13399.00,
                'total_sell': 0,
                'total_fees': 33.50,
                'total_buy_hkd': 13399.00,
                'total_sell_hkd': 0,
                'total_fees_hkd': 33.50
            },
            {
                'market': 'USA',
                'code': 'KC',
                'stock_name': '金山云',
                'full_name': 'KC:NASDAQ',
                'quantity': 500,
                'total_buy': 10586.00,
                'total_sell': 1744.00,
                'total_fees': 60.85,
                'total_buy_hkd': 10586.00,
                'total_sell_hkd': 1744.00,
                'total_fees_hkd': 60.85
            }
        ]

        # 模拟股价查询返回
        def mock_get_stock_price(query):
            prices = {
                'NVDA:NASDAQ': 134.395,
                'KC:NASDAQ': 20.67
            }
            return prices.get(query)

        mock_checker.get_stock_price.side_effect = mock_get_stock_price
        mock_checker.get_exchange_rate.return_value = 1.0

        # 测试刷新现价
        with self.app.test_request_context():
            response = refresh_stock_prices()
            data = response.get_json()

            self.assertTrue(data['success'])
            updated_stocks = data['data']['updated_stocks']

            # 验证 NVDA 的计算
            nvda = next(s for s in updated_stocks if s['code'] == 'NVDA')
            self.assertEqual(nvda['quantity'], 100)
            self.assertEqual(nvda['price'], 134.395)
            self.assertAlmostEqual(nvda['market_value'], 13439.50, places=2)
            self.assertAlmostEqual(nvda['unrealized_profit'], 7.00, places=2)  # 13439.50 - 13399.00 - 33.50
            self.assertAlmostEqual(nvda['profit_rate'], 0.05, places=2)

            # 验证 KC 的计算
            kc = next(s for s in updated_stocks if s['code'] == 'KC')
            self.assertEqual(kc['quantity'], 500)
            self.assertEqual(kc['price'], 20.67)
            self.assertAlmostEqual(kc['market_value'], 10335.00, places=2)
            self.assertAlmostEqual(kc['realized_profit'], -8902.85, places=2)  # 1744.00 - 10586.00 - 60.85
            self.assertAlmostEqual(kc['unrealized_profit'], 10335.00, places=2)
            self.assertAlmostEqual(kc['total_profit'], 1432.15, places=2)
            self.assertAlmostEqual(kc['profit_rate'], 13.53, places=2)

            # 验证市场统计
            profit_stats = data['data']['profit_stats']
            market_stats = profit_stats['market_stats']['USA']
            
            # 验证市场总计
            self.assertAlmostEqual(market_stats['market_value'], 23774.50, places=2)  # 13439.50 + 10335.00
            self.assertAlmostEqual(market_stats['total_profit'], -21302.92, places=2)
            self.assertAlmostEqual(market_stats['profit_rate'], -16.01, places=2)

            # 验证持仓统计
            holding_stats = market_stats['holding_stats']
            self.assertEqual(holding_stats['count'], 2)
            self.assertAlmostEqual(holding_stats['market_value'], 23774.50, places=2)
            self.assertAlmostEqual(holding_stats['total_profit'], -20801.85, places=2)
            self.assertAlmostEqual(holding_stats['profit_rate'], -86.73, places=2)

if __name__ == '__main__':
    unittest.main() 