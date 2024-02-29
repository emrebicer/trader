# Trader
This project aims to make a profit by trading cryptocurrencies automatically. The project provides several useful functionalities for binance users. You can use the library to create your own bot or use a pre-written bot that is included in the repository.

***Please Note***: I am not experienced OR educated within the field of finance, and this project was started as a hobby. So, unfortunately, these pre-written bots can't guarantee profit and even make you lose money. Please use it at your own risk.

## Signal spot bot
After spending some time within the crypto market, I have realized that the a logical way to estimate if the price will go higher or lower is to look at indicators. Thus, I have implemented several indicators: RSI, Bollinger bands, and moving average. By looking at these indicator results, I aim to have a strong prediction on the market price movement for the given asset, and according to this prediction, the bot will buy or sell the desired asset. Unfortunately in such a volatile market, it can't guarantee profits.

## Usage of the Signal spot bot
- Create a file; **binance_api_keys.json** at the root of the project, and enter your binance api key and secret key.
```json
{
    "api_key": "<API_KEY_OBTAINED_FROM_BINANCE>",
    "secret_key": "<SECRET_KEY_OBTAINED_FROM_BINANCE>"
}
```
- Create a config file named **config_signal_spot_bot.json** for the bot at the root of the project. If you don't provide a config file, the bot will generate a default one automatically. Note that you can provide different configurations for different symbols. An example config file would be;
```json
[
    {
        "enabled": true,
        "base_currency": "BTC",
        "target_currency": "USDT",
        "buy_on_next_trade": true,
        "trade_amount_buy": 50.0,
        "trade_wealth_percent_sell": 100.0,
        "last_operation_price": -1.0,
        "prevent_loss": true,
        "hook_percent": 1.0
    },
    {
        "enabled": true,
        "base_currency": "BNB",
        "target_currency": "USDT",
        "buy_on_next_trade": true,
        "trade_amount_buy": 30.0,
        "trade_wealth_percent_sell": 100.0,
        "last_operation_price": -1.0,
        "prevent_loss": true,
        "hook_percent": 1.0
    }
]
```
The default config dictionary is as following;
```python
default_config = {
    'enabled': True, # If true actively trade with this config, else dismiss
    'base_currency': 'BTC', # First currency asset in the symbol
    'target_currency': 'USDT', # Second currency asset in the symbol, want to maximize this asset
    'buy_on_next_trade': True, # Buy `base_currency` at the next trade
    'trade_amount_buy': 15.0, # Constant amount of `target_currency` to use while buying `base_currency`
    'trade_wealth_percent_sell': 100.0, # The percent of the account balance to be traded while selling `base_currency`
    'last_operation_price': -1.0, # Previous trade price, if there is no trade (-1), set to current price
    'prevent_loss': True, # If True never sell cheaper
    'hook_percent': 1.0 # Hooking is the idea of holding the tx until the given percent of change happens (greedily try to maximize profit)
}
```
- Lastly, you can use docker to run the bot or you can direcly run with python3. Dependencies are **requests** and **rich** for the TUI. So make sure you have those packages installed locally and then you can directly run **signal_spot_bot.py**.
``` bash
python3 -m pip install requests rich
python3 signal_spot_bot.py
```
- Or build a docker countainer and run the image;
 ``` bash
# Build container
docker build -t ssb .
# Run container
docker run -it -d -v "$(pwd):/app/" ssb
```
### Notifications on Telegram (Optional)
You can get notifications on telegram whenever the bot buys or sells an asset.
In order to do so, you need to do the followings;
- Create a bot on telegram (see https://core.telegram.org/bots)
- Create a file called **telegram_bot_api_keys.json** at the root of the project and fill it with your **api_token**;
``` json
{
    "api_token": "<your_telegram_api_token>"
}
```
- Finally, run the bot with the *--telegram <telegram_chat_id>* flag;
``` bash
# e.g.
python3 signal_spot_bot.py -t "your_telegram_chat_id"
```

### Notifications on Discord (Optional)
You can get notifications on a discord channel whenever the bot buys or sells an asset.
In order to do so, you need to do the followings;
- Create a bot on discord (see https://discord.com/developers/applications)
- Invite the bot to your discord server
- Create a file called **discord_bot_api_keys.json** at the root of the project and fill it with your **api_token**;
``` json
{
    "api_token": "<your_discord_api_token>"
}
```
- Finally, run the bot with the *--discord <discord_channel_id>* flag;
``` bash
# e.g.
python3 signal_spot_bot.py -d "your_discord_channel_id"
```

