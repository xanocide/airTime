#!/usr/bin/env python3

'''
    Scrapes travel websites for travel data
'''

import logging

from lib.decorator import connect, execute
from classes.expedia import expediaScraper

file_name = (
    '../log/' +
    str(__file__).replace('.py', '').replace('./', '') +
    '.log'
)
logging.basicConfig(filename=file_name, level=logging.INFO)


@execute
def main(
    departure_location, departure_date, return_date,
    num_adults, num_children, destination_location=None
):

    if not destination_location:
        locations = pull_all_airports(departure_location)
        airport_codes = [i['code'] for i in locations]
    else:
        airport_codes = [destination_location]

    expedia_obj = expediaScraper(
        from_code=departure_location,
        to_codes=airport_codes,
        departure_date=departure_date,
        return_date=return_date,
    ).scrape_flights()


@connect('MONGO')
def pull_all_airports(client, departure_location):
    '''
        Pulls all airport codes stored in mongo except for
        the departure location
    '''

    logging.info('Pulling airport codes from mongo')

    airports = list(
        client.airports.airportCodes.find({
            'code': {'$ne': departure_location}}))

    return airports


if __name__ == '__main__':

    main(
        departure_location="PHL",
        departure_date="07/25/2018",
        return_date="07/29/2018",
        num_adults=2,
        num_children=0
    )
