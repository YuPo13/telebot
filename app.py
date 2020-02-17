#import re
from flask import Flask, request
import telegram
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import plotly.express as px
import pandas as pd
import requests
from datetime import datetime, timedelta
from credentials import bot_token, bot_user_name, URL

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)


def get_rates():
    contents = requests.get('https://api.exchangeratesapi.io/latest?base=USD').json()
    return contents['rates']


def list_output(rates_obtained):
    list_rates = """"""
    for item in rates_obtained.items():
        list_rates += f"{item[0]}: {item[1]: .2f} \n"
    return list_rates


def calculate_amount(amount, ccy):
    rates = get_rates()
    result = amount * float(rates[f'{ccy}'])
    return result


def plot(ccy):
    today_date = datetime.today().strftime("%Y-%m-%d")
    week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    source = f"https://api.exchangeratesapi.io/history?start_at=" + week_ago + f"&end_at=" + today_date \
             + f"&base=USD&symbols=" + f"{ccy}"
    orig_data = requests.get(f'{source}').json()
    plot_data = orig_data["rates"]
    plot_final = sorted(plot_data.items(), key=lambda x: x[0])
    axis_x = []
    axis_y = []
    for element in plot_final:
        axis_x.append(element[0])
        axis_y.extend(list(element[1].values()))
    fig = px.line(x=axis_x, y=axis_y, labels={'x': 'Latest week dates', 'y': f'Amount of {ccy} per USD'})
    res = fig.show()
    return res


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat_id
    msg_id = update.message.message_id
    text = str(update.message.text.encode('utf-8').decode())
    print("Got message:", text)
    if text == "/start":
        bot_welcome = """
           Welcome to CurrencyExchange bot. 
           The bot is using European Central Bank data to provide you recent USD-based currency exchange rates.
           Please use following commands:
           /list   - to obtain full list of all currencies exchanged recently listed at ECB
           /exchange USD 10 to CAD - to calculate amount of destination currency (CAD in example) 
           equal to set amount of USD (10 in example)
           """
        bot.send_message(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)
    elif text == "/list":
        rates = get_rates()
        result = list_output(rates)
        bot.send_message(chat_id=chat_id, text=result, reply_to_message_id=msg_id)
    elif text.startswith("/exchange"):
        try:
            message = """
                /exchange command performs conversion of provided amount in USD to indicated currency.
                Example command format is: /exchange USD 10 to CAD 
                """
            exch_input = text.split()
            if len(exch_input) == 4:
                rates = get_rates()
                if exch_input[1] == "USD" and isinstance(exch_input[2], int) \
                        and exch_input[3] == "to" and exch_input[4] in rates:
                    result = calculate_amount(exch_input[2], exch_input[4])
                    message=f"USD {exch_input[2]} are {exch_input[4]}{result}"
            bot.send_message(chat_id=chat_id, text=message, reply_to_message_id=msg_id)
        except (ValueError, TypeError):
            bot.send_message(chat_id=chat_id, text="Your input was invalid. Start over again",
                             reply_to_message_id=msg_id)
            return "Wrong number format"
    elif text.startswith("/history"):
        try:
            exch_input = text.split()
            rates = get_rates()
            if exch_input[1].startswith("USD/") and text.endswith("for 7 days") and exch_input[1][-3:] in rates:
                result = plot(exch_input[1][-3:])
                bot.send_photo(chat_id=chat_id, text=f"{result}",
                                 reply_to_message_id=msg_id)
        except (ValueError, TypeError):
            bot.send_message(chat_id=chat_id, text="Your input was invalid. Start over again",
                             reply_to_message_id=msg_id)
            return "Wrong number format"

    else:
        unresolved_command = "There was a problem with the command you've used. " \
                             "Please enter /start to get info on commands available"
        bot.send_message(chat_id=chat_id, text=unresolved_command, reply_to_message_id=msg_id)
    return "ok"


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return '.'


if __name__ == '__main__':
    app.run(threaded=True)

# def main():
#     updater = Updater('895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4', use_context=True)
#     dp = updater.dispatcher
#     dp.add_handler(CommandHandler('list', list))
#     updater.start_polling()
#     updater.idle()
    #    https://430380db.ngrok.io
    #https://api.telegram.org/bot895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4/setWebHook?url=https://430380db.ngrok.io/
    #https://api.telegram.org/bot895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4/getWebhookInfo

# if __name__ == '__main__':
#     main()