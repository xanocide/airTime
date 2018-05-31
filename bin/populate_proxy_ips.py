#!/usr/bin/env python3
'''
    Grabs proxy ips from https://www.sslproxies.org/
    and tests them for useability

    Steps:
        -Pull proxy IPs from sslproxies
        -Test the proxy
        -Store working proxies in mongo

    Usage:
        $./populate_proxy_ips.py

'''

import logging
import requests
import concurrent.futures
import asyncio

from bs4 import BeautifulSoup

from lib.decorator import connect, execute

file_name = (
    '../log/' +
    str(__file__).replace('.py', '').replace('./', '') +
    '.log'
)
logging.basicConfig(filename=file_name, level=logging.INFO)


@execute
def main():

    proxies = get_proxy_ips()
    test_proxies_and_load_to_mongo(proxies)


def get_proxy_ips():
    '''
        Retrives proxy ips from sslproxies.org to be tested for
        usability
    '''

    logging.info('Getting proxy IPs from https://sslproxies.org')

    reponse = requests.get(
        'https://www.sslproxies.org/').text

    soup = BeautifulSoup(reponse, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    proxies = []

    for row in proxies_table.tbody.find_all('tr'):

        scraped_data = row.find_all('td')

        if scraped_data[4].string.lower() == 'elite proxy':

            url = (
                "https://" +
                scraped_data[0].string + ':' +
                scraped_data[1].string
            )

            proxies.append(url)

    logging.info('Testing {len} potential proxies'.format(
        len=len(proxies)))

    return proxies


def async_test_proxies(proxies):
    '''
        Asynchronously test proxy IP connections to
        expedia
    '''

    logging.info(
        'Starting to test connections to {number} proxies'
        .format(number=len(proxies)))

    def return_response(proxy):

        try:
            response = requests.get(
                'https://www.expedia.com',
                proxies={'https': proxy},
                timeout=60
            )
            if response.status_code == requests.codes.ok:
                logging.info(
                    'PROXY: {proxy} GOOD CONNECTION, PROXY SAVED'
                    .format(proxy=proxy))
                return proxy
        except Exception:
            logging.info('PROXY: {proxy} BAD CONNECTION'.format(proxy=proxy))

    async def _gather_tasks(loop, proxies):

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            tasks = [loop.run_in_executor(
                executor,
                return_response,
                proxy) for proxy in proxies
            ]
        return await asyncio.gather(*tasks)

    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(_gather_tasks(loop, proxies))

    return [i for i in responses if i is not None]


@connect('MONGO')
def test_proxies_and_load_to_mongo(client, proxies):
    '''
        Makes a connection with the proxy ip
        to ensure it is usable
    '''

    good_proxy_ips = async_test_proxies(proxies)

    client.scraping.proxyIps.update(
        {'_id': 'proxyIps'},
        {'$set': {'ipList': good_proxy_ips}}
    )


if __name__ == '__main__':

    main()
