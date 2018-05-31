'''
    Holds all of the configurations for the project
    Call the class inside of new scripts and instantly
    import all known configurations
'''

import logging


class Configs():

    current_file = str(__file__).replace('.py', '')
    log_format = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging = logging.basicConfig(
        filename=__name__.replace('.py', '.log'),
        format=log_format
    )
