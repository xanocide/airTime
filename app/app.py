#!/usr/bin/env python3
'''
'''

from datetime import datetime

from flask import Flask, render_template
from lib.decorator import connect

app = Flask(__name__)


@app.route('/')
@connect('MONGO')
def dashboard(client):

    flight_count = client.scraping.flights.find({}).count()

    cheap_flights = list(client.scraping.flights.find(
        {'price': {'$ne': None}}).sort([
            ('timePulled', -1), ('price', 1)]).limit(15))

    best_deals = list(client.scraping.flights.find(
        {'price': {'$ne': None}}).sort([
            ('timePulled', -1), ('pricePerMile', 1)]).limit(15))

    last_run = list(
        client.scraping.flights.find({}).sort(
            'timePulled', -1).limit(1))[0]['timePulled']

    all_flights = list(client.scraping.flights.find({
        'price': {'$ne': None}, 'timePulled': last_run}))

    seconds_since_last_run = (datetime.now() - last_run).total_seconds()
    hours, remainder = divmod(seconds_since_last_run, 3600)
    minutes, seconds = divmod(remainder, 60)

    last_run = '{hours}{minutes}{seconds}'.format(
        hours=str(int(hours)) + 'h ' if hours else '',
        minutes=str(int(minutes)) + 'm ' if minutes else '',
        seconds=str(int(seconds)) + 's ' if seconds else ''
    )

    return render_template(
        'dashboard.html',
        flight_count=flight_count,
        cheap_flights=cheap_flights,
        best_deals=best_deals,
        all_flights=all_flights,
        last_run=last_run
    )


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=9000, debug=True)