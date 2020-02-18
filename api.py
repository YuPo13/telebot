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


class DownloadsTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rates_downloaded = db.Column(db.JSON)
    time_requested = db.Column(db.DateTime, default=datetime.utcnow)


class DownloadsSchema(ModelSchema):
    class Meta:
        model = DownloadsTable


downloads_schema = DownloadsSchema()
downloads_db = []

for items in rates.items():
    rate_obj = DownloadsTable()
    rate_obj.rates_downloaded = rates
    downloads_db.append(rate_obj)

db.create_all()
db.session.bulk_save_objects(downloads_db)
db.session.commit()