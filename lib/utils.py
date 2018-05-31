#!/usr/bin/env python3
'''
    A place to store utility functions that can be used
    in multiple scripts throughout the project
'''

import logging
import asyncio
import concurrent.futures
import random
import math
import sys
import requests

import uvloop
import dryscrape

from lib.decorator import connect

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@connect('MONGO')
def insert_documents_to_mongo(client, db, collection, docs, overwrite=False):
    '''
        Inserts a list of mongo documents to a collection

    Args:
        db(string): target database
        collection(string): target collection
        docs(list of dicts): documents to write to mongo
        overwrite(bool): overwrite documents in target collection

    Returns:
        Writes documents to a mongo database
    '''

    logging.info(
        'Inserting {number} documents to mongo {db}.{collection}'
        .format(number=len(docs), db=db, collection=collection))

    if overwrite:
        for doc in docs:
            client[db][collection].update(
                {'_id': doc['_id']}, doc, upsert=True)
    else:
        client[db][collection].insert_many(docs)

    return logging.info('Mongo documents inserted succesfully!')


@connect('MONGO')
def get_proxies_from_mongo(client):
    '''
        Pulls proxy IPs that are stored in mongo
    '''

    logging.info('Pulling proxy IPs from mongo')

    return [i.get('ipList') for i in list(
        client.scraping.proxyIps.find({}))][0]


def async_load_responses(urls):
    '''
        Asynchronously loads HTML responses from web pages

    Args:
        urls(list): List of urls to generate a response for
        proxies(list): List of proxies to use to generate a response

    Returns:
        Dictionary {url: response} for each response that is returned
        as 200
    '''

    proxies = get_proxies_from_mongo()

    def return_response(url, proxy):
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537'
                    '.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
                )}
            response = requests.get(
                url, headers=headers, proxies={'https': proxy}, timeout=60)
            if response.status_code == requests.codes.ok:
                logging.info(
                    'Getting response: {url}'.format(url=url) +
                    ' using proxy: {proxy}'.format(proxy=proxy))
                return {url: response}
        except Exception:
            logging.info('Response with {proxy} timed out!'.format(
                proxy=proxy))

    async def _gather_tasks(loop, urls, proxies):

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            tasks = [loop.run_in_executor(
                executor,
                return_response,
                url, random.choice(proxies)) for url in urls
            ]
        return await asyncio.gather(*tasks)

    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(_gather_tasks(loop, urls, proxies))

    return [i for i in responses if i is not None]


def chunk_list(list_, chunk_size):
    '''
        Chunks a list into a generator

    Args:
        list(list): A list to chunk into a generator
        chunk_size(int): Size of chunks to be made out of list

    Returns:
        Generator of chunks of the input list
    '''

    for i in range(0, len(list_), chunk_size):
        yield list_[i:i + chunk_size]


def haversine_distance(pointa, pointb, miles=False):
    '''
        Returns the distance between two decimal degrees points

    Arguments:
        pointa(list): latitude, longitude of point from
        pointb(list): latitude, longitude of point to
        miles(bool): optional to return disrance in miles

    Returns:
        Distance between two points in kilometers or miles
    '''

    x, y, a, b = pointa[0], pointa[1], pointb[0], pointb[1]

    if x is None or y is None or a is None or b is None:
        return None

    if miles:
        radius = 3959
    else:
        radius = 6371

    lat = math.radians(a - x)
    lon = math.radians(b - y)
    a = math.sin(lat / 2)**2 + math.cos(
        math.radians(x)) * math.cos(math.radians(a)) * math.sin(lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d
