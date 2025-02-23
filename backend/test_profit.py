import json
from datetime import datetime

def process_transactions(transactions):
    """处理交易数据，模拟前端的数据处理逻辑"""
    print(f"\n处理 {len(transactions)} 条交易记录...")
    
    # 初始化数据结构
    result = {
        'market_stats': {},
        'holding_stocks': {},
        'closed_stocks': {},
        'transaction_details': {}
    }
    
    # 按股票分组处理交易
    stock_groups = {}
    for trans in transactions:
        stock_key = f"{trans['market']}-{trans['stock_code']}"
        if stock_key not in stock_groups:
            stock_groups[stock_key] = []
            print(f"\n发现新股票: {stock_key} ({trans['stock_name']})")
        stock_groups[stock_key].append(trans)
    
    print(f"\n共发现 {len(stock_groups)} 支股票")
    
    # 处理每支股票的数据
    for stock_key, stock_transactions in stock_groups.items():
        market = stock_transactions[0]['market']
        stock_code = stock_transactions[0]['stock_code']
        stock_name = stock_transactions[0]['stock_name']
        
        print(f"\n处理股票: {market}-{stock_code} ({stock_name})")
        print(f"交易记录数: {len(stock_transactions)}")
        
        # 计算股票统计数据
        current_quantity = 0
        total_buy = 0
        total_sell = 0
        total_fees = 0
        realized_profit = 0
        
        # 按日期排序交易记录
        stock_transactions.sort(key=lambda x: x['transaction_date'])
        
        for trans in stock_transactions:
            print(f"\n  交易日期: {trans['transaction_date']}")
            print(f"  交易类型: {trans['transaction_type']}")
            print(f"  交易数量: {trans['total_quantity']}")
            print(f"  交易金额: {trans['total_amount']:.2f}")
            print(f"  手续费: {trans['total_fees']:.2f}")
            
            if trans['transaction_type'] == 'BUY':
                current_quantity += trans['total_quantity']
                total_buy += trans['total_amount']
                print(f"  买入后持仓: {current_quantity}")
                print(f"  当前成本: {trans['current_avg_cost']}")
            else:  # SELL
                print(f"  卖出前持仓: {current_quantity}")
                print(f"  上次买入均价: {trans['prev_avg_cost']}")
                current_quantity -= trans['total_quantity']
                total_sell += trans['total_amount']
                # 计算已实现盈亏
                sell_profit = (trans['total_amount'] - 
                             (trans['total_quantity'] * trans['prev_avg_cost']) - 
                             trans['total_fees'])
                realized_profit += sell_profit
                print(f"  卖出后持仓: {current_quantity}")
                print(f"  本次盈亏: {sell_profit:.2f}")
            
            total_fees += trans['total_fees']
        
        # 计算持仓盈亏
        last_buy_price = stock_transactions[-1]['last_buy_price']
        market_value = current_quantity * last_buy_price if current_quantity > 0 else 0
        holding_profit = market_value - (current_quantity * last_buy_price) if current_quantity > 0 else 0
        
        print(f"\n股票 {stock_key} 统计:")
        print(f"当前持仓: {current_quantity}")
        print(f"总买入: {total_buy:.2f}")
        print(f"总卖出: {total_sell:.2f}")
        print(f"总手续费: {total_fees:.2f}")
        print(f"已实现盈亏: {realized_profit:.2f}")
        print(f"持仓盈亏: {holding_profit:.2f}")
        
        # 构建股票统计数据
        stock_stats = {
            'market': market,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'current_quantity': current_quantity,
            'total_buy': total_buy,
            'total_sell': total_sell,
            'total_fees': total_fees,
            'realized_profit': realized_profit,
            'holding_profit': holding_profit,
            'total_profit': realized_profit + holding_profit,
            'profit_rate': ((realized_profit + holding_profit) / total_buy * 100) if total_buy > 0 else 0,
            'transactions': stock_transactions
        }
        
        # 分类到持仓或已清仓
        if current_quantity > 0:
            result['holding_stocks'][stock_key] = stock_stats
            print("归类为: 持仓股票")
        else:
            result['closed_stocks'][stock_key] = stock_stats
            print("归类为: 已清仓股票")
        
        # 更新市场统计
        if market not in result['market_stats']:
            print(f"\n初始化市场 {market} 统计数据")
            result['market_stats'][market] = {
                'transaction_count': 0,
                'total_buy': 0,
                'total_sell': 0,
                'total_fees': 0,
                'realized_profit': 0,
                'holding_profit': 0,
                'total_profit': 0,
                'profit_rate': 0,
                'holding_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'holding_profit': 0,
                    'total_profit': 0,
                    'profit_rate': 0
                },
                'closed_stats': {
                    'count': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'realized_profit': 0,
                    'profit_rate': 0
                }
            }
        
        # 更新市场统计数据
        market_stats = result['market_stats'][market]
        market_stats['transaction_count'] += len(stock_transactions)
        market_stats['total_buy'] += total_buy
        market_stats['total_sell'] += total_sell
        market_stats['total_fees'] += total_fees
        market_stats['realized_profit'] += realized_profit
        market_stats['holding_profit'] += holding_profit
        market_stats['total_profit'] = market_stats['realized_profit'] + market_stats['holding_profit']
        market_stats['profit_rate'] = (market_stats['total_profit'] / market_stats['total_buy'] * 100 
                                     if market_stats['total_buy'] > 0 else 0)
        
        # 更新持仓/已清仓统计
        if current_quantity > 0:
            holding_stats = market_stats['holding_stats']
            holding_stats['count'] += 1
            holding_stats['total_buy'] += total_buy
            holding_stats['total_sell'] += total_sell
            holding_stats['total_fees'] += total_fees
            holding_stats['realized_profit'] += realized_profit
            holding_stats['holding_profit'] += holding_profit
            holding_stats['total_profit'] = holding_stats['realized_profit'] + holding_stats['holding_profit']
            holding_stats['profit_rate'] = (holding_stats['total_profit'] / holding_stats['total_buy'] * 100 
                                          if holding_stats['total_buy'] > 0 else 0)
        else:
            closed_stats = market_stats['closed_stats']
            closed_stats['count'] += 1
            closed_stats['total_buy'] += total_buy
            closed_stats['total_sell'] += total_sell
            closed_stats['total_fees'] += total_fees
            closed_stats['realized_profit'] += realized_profit
            closed_stats['profit_rate'] = (closed_stats['realized_profit'] / closed_stats['total_buy'] * 100 
                                         if closed_stats['total_buy'] > 0 else 0)
    
    return result

def main():
    print("开始读取API响应文件...")
    try:
        with open('api_response.json', 'r', encoding='utf-8') as f:
            print("成功打开文件")
            content = f.read()
            print(f"文件内容长度: {len(content)} 字节")
            
            api_response = json.loads(content)
            print("\n成功解析JSON数据")
            print(f"API响应状态: {api_response.get('success', False)}")
            
            if 'data' in api_response and 'transactions' in api_response['data']:
                transactions = api_response['data']['transactions']
                print(f"成功获取交易记录，共 {len(transactions)} 条")
                
                # 处理交易数据
                result = process_transactions(transactions)
                
                # 打印结果
                print("\n=== 测试数据处理结果 ===")
                print("\n1. 市场统计:")
                print(json.dumps(result['market_stats'], indent=2, ensure_ascii=False))
                print("\n2. 持仓股票:")
                print(json.dumps(result['holding_stocks'], indent=2, ensure_ascii=False))
                print("\n3. 已清仓股票:")
                print(json.dumps(result['closed_stocks'], indent=2, ensure_ascii=False))
            else:
                print("API响应中没有找到交易数据")
                return
    except FileNotFoundError:
        print("找不到API响应文件")
        return
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    main() 