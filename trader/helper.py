import os
import json
import datetime
import requests
import trader.constants

def fill_empty_fields_with_default_config(current_config, default_config) -> dict:
    if current_config['base_currency'] and current_config['target_currency']:
        symbol = current_config['base_currency'] + current_config['target_currency']
    else:
        symbol = default_config['base_currency'] + default_config['target_currency']
    
    for key in default_config:
        if key not in current_config:
            current_config[key] = default_config[key]

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
    date = datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')
    log_message = f'{date} --- {message}'
    with open(filename, 'a') as log_file:
        log_file.write(f'{log_message}\n')
    if dump_to_console:
        print(message)

def error_log(filename, message, dump_to_console):
    log(filename, message, dump_to_console)

def notify_on_telegram(api_token, chat_id, message):
    """
        Send the <message> to the <chat_id> over telegram.
        You need to provide the <api_token> in order to access to the telegram api.
    """

    # Send the message
    response = requests.get(f'{trader.constants.TELEGRAM_BOT_API_BASE_ENDPOINT}{api_token}/sendMessage'
        f'?chat_id={chat_id}&text={message}')
    
    response_json = response.json()
    if response.status_code != 200:
        raise Exception(f'Failed to get -> notify_on_telegram, response:{response.text}')

    return response_json

def notify_on_discord(api_token, channel_id, message):
    """
        Send the <message> to the channel with <channel_id> over discord.
        You need to provide the <api_token> in order to access to the discord api.
    """

    data = {
        'embeds': [{
            'title': 'A new trade! 💸',
            'description': f'{message}'
        }]
    }

    # Set the authorization header
    headers = {
        'Authorization': f'Bot {api_token}'
    }

    # Send the message
    response = requests.post(f'{trader.constants.DISCORD_BOT_API_BASE_ENDPOINT}'
        f'/channels/{channel_id}/messages', headers = headers, json = data)

    response_json = response.json()
    if response.status_code != 200:
        raise Exception(f'Failed to post-> notify_on_discord, response:{response.text}')

    return response_json
