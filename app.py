"""
This module describes the behaviour of telegram bot created for currency exchange rate notifications
"""
import matplotlib.pyplot as plt
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import telegram
import requests
from marshmallow_sqlalchemy import ModelSchema
from datetime import datetime, timedelta
from .env import bot_token, URL


app = Flask(__name__)
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


exchange_rates_api_res = requests.get('https://api.exchangeratesapi.io/latest?base=USD')
rates = exchange_rates_api_res.json()["rates"]


class DownloadsTable(db.Model):
    """
    This class describes the table structure for currency exchange rates data to be maintained
    """
    id = db.Column(db.Integer, primary_key=True)
    rates_downloaded = db.Column(db.JSON)
    time_requested = db.Column(db.DateTime, default=datetime.utcnow)


class DownloadsSchema(ModelSchema):
    class Meta:
        model = DownloadsTable


downloads_schema = DownloadsSchema()
downloads_db = []


if db:
    db.drop_all()
else:
    rate_obj = DownloadsTable()
    rate_obj.rates_downloaded = rates
    downloads_db.append(rate_obj)
    db.create_all()
    db.session.bulk_save_objects(downloads_db)
    db.session.commit()


def get_rates():
    """
    This function requests USD-based currency exchange data from European Central Bank and saves it into local database.
    :return: dictionary with USD-based currency exchange rates
    """
    contents = requests.get('https://api.exchangeratesapi.io/latest?base=USD').json()
    rates = contents["rates"]
    return rates


def list_output(rates_obtained):
    """
    This function produces currencies exchange rate listing with appropriate layout for telegram bot request '/list'
    :param rates_obtained: dictionary with currency codes and their USD-based exchange rates
    :return: string with formatted listing of currency codes and their USD-based exchange rates
    """
    return "\n".join(f"{key}: {value: .2f}" for key, value in rates_obtained.items())


def plot(ccy):
    """
    This function produces chart of requested currency rate for recent 7 days
    for telegram bot request '/exchange USD [amount] to [currency code]'
    :param ccy: requested currency code
    :return: image file name with plot of requested currency 7-days USD-based exchange rates dynamics chart
    """
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
    fig, ax = plt.subplots()
    ax.plot(axis_x, axis_y)
    ax.set(xlabel='7-days period', ylabel=f'{ccy} per USD')
    ax.grid()
    pict_name = "Weekly_trend.png"
    fig.savefig(pict_name)
    return pict_name


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    """
    This function describes the behaviour of telegram bot according to request sent by user
    """
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
           /history USD/CAD for 7 days - to obtain chart with destination currency (CAD in example) rate to USD 
           for recent 7 days period
           """
        bot.send_message(chat_id=chat_id, text=bot_welcome, reply_to_message_id=msg_id)
    elif text == "/list":
        rates = get_rates()
        result = list_output(rates)
        bot.send_message(chat_id=chat_id, text=result, reply_to_message_id=msg_id)
    elif text.startswith("/exchange"):
        try:
            exch_input = text.split()
            rates = get_rates()
            if exch_input[4] not in rates:
                bot.send_message(chat_id=chat_id, text="Destination currency is not listed by ECB",
                                 reply_to_message_id=msg_id)
            elif exch_input[1] == "USD" and exch_input[2].isdigit() and exch_input[3] == "to":
                result = float(exch_input[2]) * float(rates[exch_input[4]])
                exch_res = f"USD{exch_input[2]} = {exch_input[4]}{result}"
                bot.send_message(chat_id=chat_id, text=exch_res, reply_to_message_id=msg_id)
            else:
                bot.send_message(chat_id=chat_id, text="""
                Invalid input. Please conform to request format:
                /exchange USD /amount figure/ to /3-letter currency code in capital/
                E.g. /exchange USD 100 to EUR
                """, reply_to_message_id=msg_id)
        except (ValueError, TypeError, SyntaxError, IndexError):
            bot.send_message(chat_id=chat_id, text="Your input was invalid. Start over again",
                             reply_to_message_id=msg_id)
            return "Wrong number format"
    elif text.startswith("/history"):
        try:
            exch_input = text.split()
            rates = get_rates()
            if exch_input[1].startswith("USD/") and text.endswith("for 7 days") and exch_input[1][-3:] in rates:
                result = plot(exch_input[1][-3:])
                bot.send_document(chat_id=chat_id, document=open(f'{result}', 'rb'))
        except (ValueError, TypeError, IndexError, SyntaxError):
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
    """
    This function sets webhook
    """
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
