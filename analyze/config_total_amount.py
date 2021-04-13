
"""
Calculates total amount to spend on enabled symbols
"""

import os
import json

CONFIG_FILE = 'binance_trader_config.json'

# Read the config file
config_file_exact_path = os.path.join(os.path.dirname(os.getcwd()), CONFIG_FILE)
with open(config_file_exact_path) as config_file:
    config = json.load(config_file)

amounts = []

for cfg in config:
    if cfg['enabled']:
        if cfg['trade_with_percent_buy']:
            symbol = cfg['base_currency'] + cfg['target_currency']
            print(f'{symbol} is enabled and trades with percent ({cfg["trade_wealth_percent_buy"]}%)')
        else:
            amounts.append(cfg['trade_amount_buy'])


if len(amounts) == 0:
    print('No config that uses amount')
else:
    print(f'Found {len(amounts)} symbols with a total amount of: {sum(amounts)}')
