from app import db
from datetime import datetime


class RatesTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(4), unique=True)
    rate = db.Column(db.Numeric)
    time_requested = db.Column(db.DateTime, default=datetime.utcnow)