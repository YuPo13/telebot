import re
from flask import Flask, request
import telegram
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests

from credentials import bot_token, bot_user_name, URL

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)


def get_rates():
    contents = requests.get('https://api.exchangeratesapi.io/latest?base=USD').json()
    rates = contents['rates']
    return rates


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat_id
    msg_id = update.message.message_id
    text = update.message.text.encode('utf-8').decode()
    if text == "/start":
        bot_welcome = """
           Welcome to CurrencyExchange bot. 
           The bot is using European Central Bank data to provide you recent USD-based currency exchange rates.
           Please use following commands:
           /list   - to obtain full list of all currencies exchanged recently listed at ECB
           """
        bot.send_message(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)

    elif text == "/list":
        rates = get_rates()
        bot.send_message(chat_id=chat_id, text=rates, reply_to_message_id=msg_id)

    else:
        bot.send_message(chat_id=chat_id, text="There was a problem in the name you used, please enter different name",
                         reply_to_message_id=msg_id)
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