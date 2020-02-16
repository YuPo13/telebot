from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
from bottle import run, post, request as bottle_request


def get_rates():
    contents = requests.get('https://api.exchangeratesapi.io/latest?base=USD').json()
    rates = contents['rates']
    return rates


def list(bot, update):
    rates python= get_rates()
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, message=rates)


def main():
    data = bottle_request.json
    print(data)
    run(host='localhost', port=8080, debug=True)
    updater = Updater('895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('list', list))
    updater.start_polling()
    updater.idle()
    #    https://430380db.ngrok.io
    #https://api.telegram.org/bot895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4/setWebHook?url=https://430380db.ngrok.io/
    #https://api.telegram.org/bot895124509:AAGcYHgIeEud4BJKa6zbzxCwkq2WxQIhlN4/getWebhookInfo

if __name__ == '__main__':
    main()