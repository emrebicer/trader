import os
import json
import datetime
import constants
import binance_helper 

def fill_empty_fields_with_default_config(current_config, default_config) -> dict:
    if current_config['base_currency'] and current_config['target_currency']:
        symbol = current_config['base_currency'] + current_config['target_currency']
    else:
        symbol = default_config['base_currency'] + default_config['target_currency']
    
    for key in default_config:
        if key not in current_config:
            current_config[key] = default_config[key]
            print(f'Updated `{key}` key in {symbol} config')
    return current_config

def load_config_file(default_config) -> list:
    final_config_files = []

    # If a config file exists on the fs, load it
    if os.path.isfile(os.path.join(os.getcwd(), constants.PRIMITIVE_SPOT_BOT_CONFIG_FILE)):
        with open(constants.PRIMITIVE_SPOT_BOT_CONFIG_FILE, 'r') as config_file:
            saved_config = json.loads(config_file.read())
            if type(saved_config) == dict:
                temp = saved_config
                saved_config = []
                saved_config.append(temp)
            
            for current_config in saved_config:
                final_config_files.append(fill_empty_fields_with_default_config(current_config, default_config))
            
    else:
        # Just start the bot with the default config file
        final_config_files.append(default_config)

    return final_config_files

def write_config_file(config):
    with open(constants.PRIMITIVE_SPOT_BOT_CONFIG_FILE, 'w') as config_file:
        config_file.write(json.dumps(config, indent=4))

def validate_config_file(config):
    
    if type(config) != list:
        raise Exception(f'Configuration error: the config file must be a list!')
    
    # Make sure each config has a unique symbol
    prev_symbols = []
    for current_config in config:
        current_symbol = current_config['base_currency'] + current_config['target_currency']
        if current_symbol in prev_symbols:
            raise Exception(f'{current_symbol} config duplicate')
        prev_symbols.append(current_symbol)

    expected_config_keys = {
        'enabled': bool,
        'base_currency': str,
        'target_currency': str,
        'buy_on_next_trade': bool,
        'last_operation_price': float,
        'profit_percent_buy': float,
        'profit_percent_sell': float,
        'hook_percent': float,
        'trade_with_percent_buy': bool,
        'trade_amount_buy': float,
        'trade_wealth_percent_buy': float,
        'trade_wealth_percent_sell': float,
        'loss_prevention': bool,
        'loss_prevention_percent': float,
        'avoid_buy_on_daily_increase': bool,
        'avoid_buy_on_daily_increase_percent': float,
        'avoid_buy_on_average_increase': bool,
        'avoid_buy_on_average_day_count': int,
        'last_trade_time_stamp': float,
        'update_lop_on_idle': bool, 
        'update_lop_on_idle_days': int 
    }

    # Check if an unknown key exists in the config file
    for current_config in config:
        for key in current_config:
            if key not in expected_config_keys:
                raise Exception(f'{key} was not expected in the config')
    
    for current_config in config:
        for key in expected_config_keys:
            if type(current_config[key]) is not expected_config_keys[key]:
                raise Exception(f'Configuration error: Type of "{key}" must be '
                f'{expected_config_keys[key]}, but it is a {type(current_config[key])}')

def log(message, dump_to_console):
    binance_helper.log(constants.PRIMITIVE_SPOT_BOT_LOG_FILE, message, dump_to_console)

def error_log(message, dump_to_console):
    binance_helper.error_log(constants.PRIMITIVE_SPOT_BOT_ERROR_LOG_FILE, message, dump_to_console)
