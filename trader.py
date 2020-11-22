import time
import os
import json
from common import get_current_ratio

def load_config_file():
    # Check if the config file exists
    if os.path.isfile(os.path.join(os.getcwd(), config_file_name)):
        with open(config_file_name, 'r') as config_file:
            global config
            config = json.loads(config_file.read())
            print('Config is read from fs: ', config)        
    else:
        print('No config file was found')

def write_config_file():
    with open(config_file_name, 'w') as config_file:
        config_file.write(json.dumps(config))
        print('Wrote config to the fs')        

# Initial config, if there is no config file
# on the fs, will use this configuration
config = dict(
    BASE_CURRENCY = 'USD',
    TARGET_CURRENCY = 'BTC',
    last_trade_ratio = -1,
    trade_margin = 0.5,
    buy_on_next_trade = True,
    initial_money = 1000
)

config['current_money'] = config['initial_money']
config_file_name = 'config.txt'

# Load from fs, if exists
load_config_file()


while True:
    current_ratio = get_current_ratio(config['BASE_CURRENCY'], config['TARGET_CURRENCY'])
    if config['last_trade_ratio'] == -1:
        config['last_trade_ratio'] = current_ratio
        write_config_file()
        continue

    print((config['last_trade_ratio'] - current_ratio))
    
    if abs(config['last_trade_ratio'] - current_ratio) > config['trade_margin']:
        did_trade = False
        if config['buy_on_next_trade'] and current_ratio < config['last_trade_ratio']:
            # Buy
            did_trade = True
            config['current_money'] = config['current_money'] / current_ratio
            print('-------------------------------------------------')
            print(f'Bought {config["TARGET_CURRENCY"]} at {current_ratio} ratio ({time.strftime("%H:%M:%S", time.localtime())})')
            print(f'Current money: {config["current_money"]:.2f} {config["TARGET_CURRENCY"]}')
        elif not config['buy_on_next_trade'] and current_ratio > config['last_trade_ratio']:
            # Sell
            did_trade = True
            config['current_money'] = config['current_money'] * current_ratio
            print('-------------------------------------------------')
            print(f'Bought {config["BASE_CURRENCY"]} at {current_ratio} ratio ({time.strftime("%H:%M:%S", time.localtime())})')
            print(f'Current money: {config["current_money"]:.2f} {config["BASE_CURRENCY"]}')

        if did_trade:
            config['buy_on_next_trade'] = not config['buy_on_next_trade']
            config['last_trade_ratio'] = current_ratio
            write_config_file()
    
    time.sleep(5)
