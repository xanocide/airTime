#!/usr/bin/env python3
'''
'''

import pandas as pd

from lib import utils
from lib.decorator import connect


def main():

    path = 'airports.csv'

    df_airports = pd.read_csv(path).drop(
        columns=['index', 'number1', 'number2', 'letter', 'region', 'type', 'bullshit', 'other_code'])

    df_airports['_id'] = df_airports.code

    write_df_to_mongo(df_airports)


@connect('MONGO')
def pull_mongo_airports(client):

    return list(client.airports.airportCodes.find({}))


def write_df_to_mongo(df):

    utils.insert_documents_to_mongo(
        db='airports',
        collection='airportCodes',
        docs=df.to_dict('records'),
        overwrite=True)


if __name__ == '__main__':

    main()
