#!/usr/bin/env python3
'''
    Scrapes expedia for flight data

Steps:
    - Load expedia webpage for desired trip information
    - Parse HTML to find flight data
    - Store flight data into mongo
'''

import logging
from datetime import datetime
import math

from bs4 import BeautifulSoup
import pandas as pd

from lib import utils
from lib.decorator import connect


class expediaScraper():
    '''
        Scrapes expedia for travel information by airport code,
        departure date, return date, and number of travelers
    '''

    def __init__(
        self, from_code, to_codes, departure_date, return_date,
        adults=1, children=0
    ):

        self.from_code = from_code
        self.to_codes = to_codes
        self.departure_date = departure_date
        self.return_date = return_date
        self.adults = adults
        self.children = children
        self.airport_information = self.pull_airport_codes()
        self.run_time = datetime.utcnow()

        self.flight_link = (
            "https://www.expedia.com/Flights-Search?trip="
            "roundtrip&leg1=from:{from_code},to:{to_code},"
            "departure:{departure_date}TANYT&leg2=from:{from_code},"
            "to:{to_code},departure:{return_date}TTANYT&passengers=children:"
            "{children},adults:{adults}&mode=search")

    def price_per_mile(self, distance, price):
        '''
            Calculates price per mile
        '''

        if price and distance:
            return round((price / distance), 2)
        return None

    @connect('MONGO')
    def pull_airport_codes(client, self):

        return pd.DataFrame(
            list(client.airports.airportCodes.find({}))).set_index(
                '_id').to_dict('index')

    def scrape_flights(self):
        '''
            Scrapes an expedia webpage for flight information
            to be saved for later use
        '''

        self.urls = {}

        for code in self.to_codes[0:5]:

            url = self.flight_link.format(
                from_code=self.from_code,
                to_code=code,
                departure_date=self.departure_date,
                return_date=self.return_date,
                children=self.children,
                adults=self.adults
            )

            self.urls[url] = {
                'from': self.from_code,
                'to': code
            }

        url_chunks = utils.chunk_list(list(self.urls.keys()), 300)
        chunk_count = math.ceil((len(list(self.urls.keys())) / 300))

        for i in range(chunk_count):

            logging.info(
                '\n\n~~~~! PARSING URL CHUNK {i} / {total} !~~~~\n\n'
                .format(i=(i + 1), total=chunk_count))

            responses = utils.async_load_responses(next(url_chunks))

            for response in responses:
                for url, resp in response.items():
                    self.find_api_endpoint(resp)
                    self.html_flight_parser(url, resp)

    def find_api_endpoint(self, response):

        try:
            html = response.text.encode('UTF-8').decode('latin-1')
        except Exception:
            pass
        import pdb; pdb.set_trace()  # breakpoint 165ae67a //

    def html_flight_parser(self, url, response):
        '''
            Parses flight HTML to find flight data and stores
            the data into mongo.
        '''

        try:
            html = response.text.encode('UTF-8').decode('latin-1')
            soup = BeautifulSoup(html, 'html.parser')
            flight_container = soup.find('ul', {'id': 'flightModuleList'})
            flight = list(flight_container.find_all(
                'li', {'class': "flight-module segment offer-listing"}))[0]
        except Exception:
            logging.error('Cannot parse HTML for flights, no data available')
            flight = None

        if flight:

            try:
                departure_time = flight.find(
                    'span', {'data-test-id': 'departure-time'}
                ).text.strip()
            except Exception:
                departure_time = None

            try:
                arrival_time = flight.find(
                    'span', {'data-test-id': 'arrival-time'}).text.strip()
            except Exception:
                arrival_time = None

            try:
                airline = flight.find(
                    'div', {'data-test-id': 'airline-name'}).text.strip()
            except Exception:
                airline = None

            try:
                price = int(flight.find(
                    'span', {"data-test-id": "listing-price-dollars"}
                ).text.strip().lstrip('$').replace(',', ''))
            except Exception:
                price = None

            try:
                flight_time = flight.find(
                    'span', {'data-test-id': 'duration'}).text.strip()
            except Exception:
                flight_time = None

            try:
                layovers = int([
                    i.get('data-test-num-stops') for i in flight.find(
                        'div',
                        {'class': 'fluid-content inline-children'}
                    ).find_all('span') if i.get(
                        'data-test-num-stops') is not None][0])
            except Exception:
                layovers = None

            try:
                seats_left = int(''.join(
                    [i for i in flight.find(
                        'span', {'data-test-id': 'seats-left'}
                    ).text.strip() if i.isdigit()]))
            except Exception:
                seats_left = None

            from_code = self.urls[url].get('from')
            to_code = self.urls[url].get('to')

            origin_information = self.airport_information.get(
                from_code, {})
            destination_information = self.airport_information.get(
                to_code, {})

            origin_point = [
                origin_information.get('latitude'),
                origin_information.get('longitude')
            ]

            destination_point = [
                destination_information.get('latitude'),
                destination_information.get('longitude')
            ]

            distance = utils.haversine_distance(
                origin_point, destination_point, miles=True
            )

            document = {
                'departureLocation': (
                    origin_information.get('city', '') + ', ' +
                    origin_information.get('country', '')
                ),
                'destinationLocation': (
                    destination_information.get('city', '') + ', ' +
                    destination_information.get('country', '')
                ),
                'departureAirportCode': origin_information.get('code'),
                'destinationAirportCode': destination_information.get(
                    'code'),
                'departureAirportName': origin_information.get(
                    'airportName'),
                'destinationAirportName': destination_information.get(
                    'airportName'),
                'distance': distance,
                'destinationLatLong': destination_point,
                'departureLatLong': origin_point,
                'departureDate': self.departure_date,
                'returnDate': self.return_date,
                'departureTime': departure_time,
                'arrivalTime': arrival_time,
                'airline': airline,
                'seatsLeft': seats_left,
                'price': price,
                'pricePerMile': self.price_per_mile(distance, price),
                'duration': flight_time,
                'layovers': layovers,
                'timePulled': self.run_time,
                'source': 'expedia',
                'link': url
            }

            logging.info(
                'Found from {leave} to {arrive} price: {price}!'
                .format(
                    leave=self.urls[url].get('from'),
                    arrive=self.urls[url].get('to'),
                    price=price
                ))

            if document:
                utils.insert_documents_to_mongo(
                    db='scraping',
                    collection='flights',
                    docs=[document])
