import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import json
import re

logger = logging.getLogger(__name__)

class CurrencyChecker:
    MARKETS = {
        'HK': 'NASDAQ',  # 港股使用 NASDAQ 市场
        'USA': 'NASDAQ', # 美股使用 NASDAQ 市场
        'SH': 'SHA',     # 上海证券交易所
        'SZ': 'SHE'      # 深圳证券交易所
    }

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }

    @staticmethod
    def get_stock_price(query):
        """
        使用确定的股票代码查询股价
        :param query: 完整的查询字符串，如 'NVDA:NASDAQ'
        :return: 股票价格或 None
        """
        try:
            url = f'https://www.google.com/finance/quote/{query}'
            logger.info(f"查询股价 URL: {url}")
            
            response = requests.get(url, headers=CurrencyChecker.HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            result = CurrencyChecker._extract_price(soup)
            
            if result and result['price']:
                logger.info(f"获取股票 {query} 价格: {result['price']}")
                return result['price']
            return None
            
        except Exception as e:
            logger.error(f'获取股票 {query} 价格失败: {str(e)}')
            return None

    @staticmethod
    def search_stock(code):
        """
        搜索新股票时遍历不同市场
        :param code: 股票代码
        :return: 包含市场和价格信息的字典列表
        """
        results = []
        for market, exchange in CurrencyChecker.MARKETS.items():
            try:
                query = f"{code}:{exchange}"
                price = CurrencyChecker.get_stock_price(query)
                if price is not None:
                    results.append({
                        'market': market,
                        'exchange': exchange,
                        'price': price,
                        'query': query
                    })
                    logger.info(f"在市场 {market} 找到股票 {code} 价格: {price}")
            except Exception as e:
                logger.error(f"搜索市场 {market} 的股票 {code} 时出错: {str(e)}")
                continue
        return results

    @staticmethod
    def get_exchange_rate(from_currency, to_currency='HKD'):
        """
        获取汇率
        :param from_currency: 源货币代码，如 'USD'
        :param to_currency: 目标货币代码，默认为 'HKD'
        :return: 汇率值或 None
        """
        try:
            url = f'https://www.google.com/finance/quote/{from_currency}-{to_currency}'
            logger.info(f"查询汇率 URL: {url}")
            
            response = requests.get(url, headers=CurrencyChecker.HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            result = CurrencyChecker._extract_price(soup)
            
            if result and result['price']:
                logger.info(f"获取汇率 {from_currency}/{to_currency}: {result['price']}")
                return result['price']
            return None
            
        except Exception as e:
            logger.error(f'获取汇率 {from_currency}/{to_currency} 失败: {str(e)}')
            return None

    @staticmethod
    def _check_price_exists(soup):
        """检查页面中是否存在价格元素"""
        # 检查主要价格元素
        price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
        if price_div:
            return True
            
        # 检查备用价格元素
        price_span = soup.find('div', {'data-last-price': True})
        if price_span and price_span.get('data-last-price'):
            return True
            
        return False

    @staticmethod
    def _find_all_price_elements(soup):
        """查找页面中所有可能包含价格的元素"""
        price_elements = []
        
        # 查找所有 div 和 span 元素
        for element in soup.find_all(['div', 'span']):
            # 获取元素的 class 属性
            classes = element.get('class', [])
            if classes:
                class_str = ' '.join(classes)
                logger.info(f"找到元素: {element.name}, class: {class_str}, text: {element.text.strip()}")
            
            # 检查是否包含价格相关的文本
            text = element.text.strip()
            if text and (text[0].isdigit() or text.startswith('$') or text.startswith('HK$')):
                price_elements.append({
                    'element': element,
                    'text': text,
                    'class': ' '.join(classes) if classes else None
                })
        
        return price_elements

    @staticmethod
    def _extract_price(soup):
        """从页面提取价格"""
        try:
            # 1. 首先尝试使用 data-last-price 属性（最准确的方式）
            price_div = soup.find('div', {'data-last-price': True})
            if price_div and price_div.get('data-last-price'):
                try:
                    price = float(price_div.get('data-last-price'))
                    if 0 < price < 1000000:
                        return {'price': price}
                except (ValueError, TypeError) as e:
                    logger.error(f"解析 data-last-price 属性时出错: {e}")

            # 2. 尝试查找主要价格元素
            price_element = soup.find('div', {'class': ['YMlKec', 'fxKbKc']})
            if price_element and price_element.parent:
                parent_classes = price_element.parent.get('class', [])
                if 'P6K39c' in parent_classes:
                    price_text = price_element.text.strip()
                    
                    # 移除货币符号和逗号
                    price_text = price_text.replace('$', '').replace(',', '').replace('HK$', '')
                    
                    # 如果包含空格（例如有额外的涨跌信息），只取第一个数字
                    if ' ' in price_text:
                        price_text = price_text.split()[0]
                    
                    try:
                        price = float(price_text)
                        if 0 < price < 1000000:
                            return {'price': price}
                    except (ValueError, TypeError) as e:
                        logger.error(f"解析主要价格文本时出错: {e}")

            logger.error("未找到有效的价格元素")
            return {'price': None}

        except Exception as e:
            logger.error(f"提取价格时出错: {str(e)}")
            return {'price': None}

    @staticmethod
    def get_historical_rate(currency_pair, date):
        """
        获取历史汇率
        :param currency_pair: 货币对（如 'USD/HKD'）或股票代码（如 '0981:HKG'）
        :param date: 日期（datetime对象或YYYY-MM-DD格式的字符串）
        :return: 该日期的汇率值或股票价格，或 None
        """
        try:
            # 确保日期格式正确
            if isinstance(date, str):
                target_date = datetime.strptime(date, '%Y-%m-%d')
            elif isinstance(date, datetime):
                target_date = date
            else:
                raise ValueError("日期格式不正确")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }

            # 构建URL
            if '/' in currency_pair:  # 汇率查询
                from_currency, to_currency = currency_pair.split('/')
                url = f'https://www.google.com/finance/quote/{from_currency}-{to_currency}?window=1Y'
            else:  # 股票查询
                url = f'https://www.google.com/finance/quote/{currency_pair}?window=1Y'

            logger.info(f"访问历史数据URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 尝试从页面提取历史数据
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找包含历史数据的脚本标签
            scripts = soup.find_all('script')
            data_pattern = re.compile(r'window.google.finance.data\s*=\s*({.*?});', re.DOTALL)
            
            historical_data = None
            target_date_str = target_date.strftime('%Y-%m-%d')
            
            for script in scripts:
                if script.string:
                    match = data_pattern.search(script.string)
                    if match:
                        data_json = match.group(1)
                        try:
                            data = json.loads(data_json)
                            if 'lines' in data and len(data['lines']) > 0:
                                points = data['lines'][0].get('points', [])
                                
                                # 查找目标日期的数据
                                for point in points:
                                    point_date = datetime.fromtimestamp(point[0]/1000).strftime('%Y-%m-%d')
                                    if point_date == target_date_str:
                                        historical_data = point[1]
                                        logger.info(f"找到历史数据: {target_date_str} = {historical_data}")
                                        return historical_data
                                
                        except json.JSONDecodeError:
                            continue

            if historical_data is None:
                logger.error(f"未找到 {target_date_str} 的历史数据")
                return None

        except Exception as e:
            logger.error(f'获取历史数据时出错: {str(e)}')
            return None 