import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import json
import re
from config.database import db
from models.exchange import ExchangeRate

logger = logging.getLogger(__name__)

class CurrencyChecker:
    MARKETS = {
        'HK': 'HKG',    # 香港交易所
        'USA': 'NASDAQ', # 纳斯达克
        'NYSE': 'NYSE',  # 纽约证券交易所
        'SH': 'SHA',     # 上海证券交易所
        'SZ': 'SHE'      # 深圳证券交易所
    }

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }

    @staticmethod
    def update_temporary_rates():
        """
        查询并更新所有标记为TEMPORARY的汇率记录
        使用实时汇率API更新，并将数据来源修改为EXCHANGE_RATES_API
        :return: 更新的记录数量
        """
        try:
            # 查询所有TEMPORARY汇率记录
            temp_rates = ExchangeRate.find_temporary_rates()
            
            if not temp_rates:
                logger.info("没有找到临时汇率记录")
                return 0
                
            updated_count = 0
            
            for rate in temp_rates:
                try:
                    currency = rate.currency
                    rate_date = rate.rate_date
                    
                    # 获取最新汇率
                    new_rate_value = CurrencyChecker.get_exchange_rate(currency)
                    
                    if new_rate_value:
                        # 更新汇率记录
                        rate.rate = new_rate_value
                        rate.source = 'EXCHANGE_RATES_API'
                        
                        if rate.save():
                            updated_count += 1
                            logger.info(f"已更新汇率: {currency} @ {rate_date}, 新汇率: {new_rate_value}")
                    else:
                        logger.warning(f"无法获取汇率: {currency}")
                        
                except Exception as e:
                    logger.error(f"更新汇率记录时出错: {str(e)}")
                    continue
                    
            return updated_count
            
        except Exception as e:
            logger.error(f"更新临时汇率记录失败: {str(e)}")
            return 0

    @staticmethod
    def get_stock_price(query):
        """
        使用确定的股票代码查询股价
        :param query: 完整的查询字符串，如 'NVDA:NASDAQ'
        :return: 股票价格或 None
        """
        try:
            if not query:
                logger.error('查询字符串为空')
                return None
            
            # 日志请求详情
            logger.info(f'正在查询股票价格: {query}')
            
            # 添加时间戳防止缓存
            timestamp = int(datetime.now().timestamp() * 1000)
            url = f'https://www.google.com/finance/quote/{query}?hl=zh&gl=CN&_={timestamp}'
            
            # 增强请求头，添加缓存控制
            headers = CurrencyChecker.HEADERS.copy()
            headers.update({
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'If-None-Match': '*',
                'If-Modified-Since': '0'
            })
            
            logger.info(f'请求URL: {url}')
            
            # 增加超时时间和重试
            for retry in range(3):
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if retry < 2:  # 如果不是最后一次重试
                        logger.warning(f'查询股票 {query} 超时或连接错误，正在重试 ({retry+1}/3): {str(e)}')
                        continue
                    else:
                        raise  # 最后一次重试仍失败，抛出异常
            
            # 检查响应内容
            if not response.text:
                logger.error(f'查询股票 {query} 返回空响应')
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查是否有价格元素
            if not CurrencyChecker._check_price_exists(soup):
                logger.warning(f'查询股票 {query} 未找到价格元素')
                # 保存响应内容以便调试
                logger.debug(f'响应内容: {response.text[:500]}...')
                return None
            
            # 提取价格
            result = CurrencyChecker._extract_price(soup)
            
            if result and result.get('price'):
                logger.info(f'成功获取股票 {query} 的价格: {result["price"]}')
                return result['price']
            
            logger.warning(f'股票 {query} 提取价格失败')
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f'查询股票 {query} HTTP错误: {str(e)}, 状态码: {e.response.status_code if hasattr(e, "response") else "未知"}')
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'查询股票 {query} 请求异常: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'获取股票 {query} 价格失败: {str(e)}', exc_info=True)
            return None

    @staticmethod
    def search_stock(code):
        """
        搜索新股票时遍历不同市场
        :param code: 股票代码
        :return: 包含市场和价格信息的字典列表
        """
        try:
            if not code:
                logger.warning("搜索股票时提供的代码为空")
                return []
            
            logger.info(f"开始搜索股票: {code}")
            results = []
            original_code = code
            
            # 如果输入的是纯数字，优先尝试港股市场
            if code.isdigit():
                codes_to_try = set()  # 使用集合去重
                
                # 处理不同长度的数字
                if len(code) <= 3:
                    # 补0到4位用于查询
                    codes_to_try.add(code.zfill(4))
                elif len(code) == 5 and code.startswith('0'):
                    # 如果是5位数且以0开头，尝试去掉前导0
                    codes_to_try.add(code[1:])
                elif len(code) == 4:
                    codes_to_try.add(code)
                
                logger.info(f"处理后的股票代码: {codes_to_try}")
                
                # 优先尝试港股市场
                for try_code in codes_to_try:
                    try:
                        timestamp = int(datetime.now().timestamp() * 1000)
                        query = f"{try_code}:HKG"
                        url = f'https://www.google.com/finance/quote/{query}?hl=zh&gl=CN&_={timestamp}'
                        
                        logger.info(f"尝试查询港股: {query}, URL: {url}")
                        
                        headers = CurrencyChecker.HEADERS.copy()
                        headers.update({
                            'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0',
                            'If-None-Match': '*',
                            'If-Modified-Since': '0'
                        })
                        
                        # 增加重试和超时设置
                        for retry in range(3):
                            try:
                                response = requests.get(url, headers=headers, timeout=15)
                                response.raise_for_status()
                                break
                            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                                if retry < 2:
                                    logger.warning(f"查询港股 {query} 超时或连接错误，正在重试 ({retry+1}/3): {str(e)}")
                                    continue
                                else:
                                    raise
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        result = CurrencyChecker._extract_price(soup)
                        
                        if result and result.get('price'):
                            price = result['price']
                            name_element = soup.find('div', {'class': 'zzDege'})
                            stock_name = name_element.text if name_element else try_code
                            
                            logger.info(f"找到港股: {try_code}, 名称: {stock_name}, 价格: {price}")
                            
                            results.append({
                                'market': 'HK',
                                'exchange': 'HKG',
                                'price': price,
                                'query': query,
                                'code_name': stock_name,
                                'code': original_code  # 保持原始代码
                            })
                            # 如果找到了港股，直接返回结果
                            if results:
                                return results
                    except Exception as e:
                        logger.error(f"搜索港股 {try_code} 时发生错误: {str(e)}")
                        continue

            # 如果没有找到港股或输入不是纯数字，遍历其他市场
            for market, exchange in CurrencyChecker.MARKETS.items():
                if market == 'HK' and results:  # 如果已经找到港股结果，跳过
                    continue
                
                try:
                    timestamp = int(datetime.now().timestamp() * 1000)
                    query = f"{original_code}:{exchange}"
                    url = f'https://www.google.com/finance/quote/{query}?hl=zh&gl=CN&_={timestamp}'
                    
                    logger.info(f"尝试查询市场 {market}: {query}, URL: {url}")
                    
                    headers = CurrencyChecker.HEADERS.copy()
                    headers.update({
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0',
                        'If-None-Match': '*',
                        'If-Modified-Since': '0'
                    })
                    
                    # 增加重试和超时设置
                    for retry in range(3):
                        try:
                            response = requests.get(url, headers=headers, timeout=15)
                            response.raise_for_status()
                            break
                        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                            if retry < 2:
                                logger.warning(f"查询市场 {market} 股票 {query} 超时或连接错误，正在重试 ({retry+1}/3): {str(e)}")
                                continue
                            else:
                                raise
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    result = CurrencyChecker._extract_price(soup)
                    
                    if result and result.get('price'):
                        price = result['price']
                        name_element = soup.find('div', {'class': 'zzDege'})
                        stock_name = name_element.text if name_element else original_code
                        
                        logger.info(f"找到市场 {market} 股票: {original_code}, 名称: {stock_name}, 价格: {price}")
                        
                        results.append({
                            'market': market,
                            'exchange': exchange,
                            'price': price,
                            'query': query,
                            'code_name': stock_name,
                            'code': original_code  # 保持原始代码
                        })
                except Exception as e:
                    logger.error(f"搜索市场 {market} 时发生错误: {str(e)}")
                    continue
            
            logger.info(f"搜索结果: 找到 {len(results)} 条记录")
            return results
        except Exception as e:
            logger.error(f"搜索股票时发生未处理的错误: {str(e)}", exc_info=True)
            return []

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
            response = requests.get(url, headers=CurrencyChecker.HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            result = CurrencyChecker._extract_price(soup)
            
            if result and result['price']:
                return result['price']
            return None
            
        except Exception as e:
            logger.error(f'获取汇率 {from_currency}/{to_currency} 失败: {str(e)}')
            return None

    @staticmethod
    def _check_price_exists(soup):
        """检查页面中是否存在价格元素"""
        price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
        if price_div:
            return True
            
        price_span = soup.find('div', {'data-last-price': True})
        if price_span and price_span.get('data-last-price'):
            return True
            
        return False

    @staticmethod
    def _find_all_price_elements(soup):
        """查找页面中所有可能包含价格的元素"""
        price_elements = []
        
        for element in soup.find_all(['div', 'span']):
            classes = element.get('class', [])
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
            price_div = soup.find('div', {'data-last-price': True})
            if price_div and price_div.get('data-last-price'):
                try:
                    price = float(price_div.get('data-last-price'))
                    if 0 < price < 1000000:
                        return {'price': price}
                except (ValueError, TypeError) as e:
                    logger.error(f"解析 data-last-price 属性时出错: {e}")

            price_element = soup.find('div', {'class': ['YMlKec', 'fxKbKc']})
            if price_element and price_element.parent:
                parent_classes = price_element.parent.get('class', [])
                if 'P6K39c' in parent_classes:
                    price_text = price_element.text.strip()
                    price_text = price_text.replace('$', '').replace(',', '').replace('HK$', '')
                    
                    if ' ' in price_text:
                        price_text = price_text.split()[0]
                    
                    try:
                        price = float(price_text)
                        if 0 < price < 1000000:
                            return {'price': price}
                    except (ValueError, TypeError) as e:
                        logger.error(f"解析主要价格文本时出错: {e}")

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
            if isinstance(date, str):
                target_date = datetime.strptime(date, '%Y-%m-%d')
            elif isinstance(date, datetime):
                target_date = date
            else:
                raise ValueError("日期格式不正确")

            if '/' in currency_pair:
                from_currency, to_currency = currency_pair.split('/')
                url = f'https://www.google.com/finance/quote/{from_currency}-{to_currency}?window=1Y'
            else:
                url = f'https://www.google.com/finance/quote/{currency_pair}?window=1Y'

            response = requests.get(url, headers=CurrencyChecker.HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
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
                                
                                for point in points:
                                    point_date = datetime.fromtimestamp(point[0]/1000).strftime('%Y-%m-%d')
                                    if point_date == target_date_str:
                                        historical_data = point[1]
                                        return historical_data
                                
                        except json.JSONDecodeError:
                            continue

            return None

        except Exception as e:
            logger.error(f'获取历史数据时出错: {str(e)}')
            return None 