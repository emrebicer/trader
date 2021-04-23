import os
import json
import datetime
import trader.constants


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

def load_config_file(file_name, default_config) -> list:
    final_config_files = []

    # If a config file exists on the fs, load it
    if os.path.isfile(os.path.join(os.getcwd(), file_name)):
        with open(file_name, 'r') as config_file:
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

def write_config_file(file_name, config):
    with open(file_name, 'w') as config_file:
        config_file.write(json.dumps(config, indent=4))

def validate_config_file(config, expected_config_keys):
    
    if type(config) != list:
        raise Exception(f'Configuration error: the config file must be a list!')
    
    # Make sure each config has a unique symbol
    prev_symbols = []
    for current_config in config:
        current_symbol = current_config['base_currency'] + current_config['target_currency']
        if current_symbol in prev_symbols:
            raise Exception(f'{current_symbol} config duplicate')
        prev_symbols.append(current_symbol)

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

def log(filename, message, dump_to_console):
    date = datetime.datetime.now()
    log_message = f'{date} - {message}'
    with open(filename, 'a') as log_file:
        log_file.write(f'{log_message}\n')
    if dump_to_console:
        print(message)

def error_log(filename, message, dump_to_console):
    log(filename, message, dump_to_console)