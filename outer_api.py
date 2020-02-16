from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from marshmallow import Schema, fields
from marshmallow_sqlalchemy import ModelSchema
from datetime import datetime
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


exchange_rates_api_res = requests.get('https://api.exchangeratesapi.io/latest?base=USD')
rates = exchange_rates_api_res.json()["rates"]


class RatesTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(4), unique=True)
    rate = db.Column(db.Numeric)
    time_requested = db.Column(db.DateTime, default=datetime.utcnow)


class RatesSchema(ModelSchema):
    class Meta:
        model = RatesTable


rates_schema = RatesSchema()

#employee = Rates(**rates)
rates_db = []

for items in rates.items():
    rate_obj = RatesTable()
    rate_obj.currency = items[0]
    rate_obj.rate = items[1]
    rates_db.append(rate_obj)

db.drop_all()
db.create_all()
db.session.bulk_save_objects(rates_db)
db.session.commit()
