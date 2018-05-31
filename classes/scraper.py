#!/usr/bin/env python3
'''
'''

import logging
import requests
import random

from lib.decorator import connect


class scraper(object):
    '''
        Base scraping class holding functions to be used with every
        scraper
    '''

    @connect('MONGO')
    def pull_proxy_ips(client, self):
        '''
            Pulls proxy IPs from mongo
        '''

        return [i.get('ipList') for i in list(
            client.scraping.proxyIps.find({}))][0]

    def load_webpage(self, link):
        '''
            Chooses a random proxy to load the webpage with
            if a proxy does not work, continue looping through
            proxy ips until it finds one that works
        '''

        while True:

            if not self.proxies:
                raise Exception(
                    'Not able to load webpage, expended proxy '
                    'list without a successful connection.')

            random_proxy = random.choice(self.proxies)

            try:
                response = requests.get(
                    link, proxies={'https': random_proxy})

                if response.status_code == requests.codes.ok:
                    return response
            except Exception:
                logging.info('Bad proxy: {proxy}'.format(
                    proxy=random_proxy))

            self.proxies.remove(random_proxy)
