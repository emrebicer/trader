
import os

LOG_FILE = 'binance_log.txt'

# Read the log file
log_file_exact_path = os.path.join(os.path.dirname(os.getcwd()), LOG_FILE)
with open(log_file_exact_path) as log_file:
    lines = log_file.readlines()

# ex -> BTCUSTD: {trades: ... , final_profit: ..., bought_count: ..., sold_count: ...}
profit_dict = {}

for line in lines:
    words = line.split(' ')
    if 'Bought' in words:
        symbol = words[5] + words[8]
        target_amount = float(words[7])

        if symbol in profit_dict:
            profit_dict[symbol]['trades'].append(line)
            profit_dict[symbol]['final_profit'] -= target_amount
            profit_dict[symbol]['bought_count'] += 1 
        else:
            profit_dict[symbol] = {
                'trades': [line],
                'final_profit': -1.0 * target_amount,
                'bought_count': 1,
                'sold_count': 0
            }
    elif 'Sold' in words:
        symbol = words[5] + words[8]
        target_amount = float(words[7])

        if symbol in profit_dict:
            profit_dict[symbol]['trades'].append(line)
            profit_dict[symbol]['final_profit'] += target_amount
            profit_dict[symbol]['sold_count'] += 1 
        else:
            profit_dict[symbol] = {
                'trades': [line],
                'final_profit': target_amount,
                'bought_count': 0,
                'sold_count': 1
            }

print('\n\nFound symbols:')
print(list(profit_dict.keys()))
total_final_profit = 0
print('--------------------------------')
for symbol in profit_dict:
    print(symbol)
    print(f"total trade count: {len(profit_dict[symbol]['trades'])}")
    print(f"bought: {profit_dict[symbol]['bought_count']} / sold: {profit_dict[symbol]['sold_count'] }")
    print(f"final profit -> {profit_dict[symbol]['final_profit']}")
    print('--------------------------------')

    total_final_profit += profit_dict[symbol]['final_profit']

print(f'Total profit: {total_final_profit} (Assuming all symbols end with the same asset)')


