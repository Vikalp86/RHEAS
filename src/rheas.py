""" RHEAS module for main functionality.

.. module:: rheas
   :synopsis: Module for executing the RHEAS system

.. moduleauthor:: Kostas Andreadis <kandread@jpl.nasa.gov>

"""

import sys
import config
import nowcast
import forecast
import argparse
import psycopg2 as pg
import rpath
import datasets


def parseArgs():
    """Parses command line arguments and prints help messages."""
    parser = argparse.ArgumentParser(description='Runs RHEAS simulation.')
    parser.add_argument('config', help='configuration file')
    parser.add_argument('-d', metavar='DB', help='name of database to connect')
    parser.add_argument('-u', help='update database', action='store_true')
    args = parser.parse_args()
    return args.config, args.d, args.u


def update(dbname, configfile, bbox=None):
    """Fetch datasets and update database."""
    conf = datasets.readDatasetList(configfile)
    try:
        bbox = map(lambda s: conf.getfloat('domain', s), [
                   'minlon', 'minlat', 'maxlon', 'maxlat'])
    except:
        bbox = None
    for name in conf.sections():
        if name != 'domain':
            try:
                mod = __import__("datasets.{0}".format(name), fromlist=[name])
            except:
                mod = None
            if mod is None:
                # download generic datasets
                datasets.download(name, dbname, bbox)
            else:
                dt = mod.dates(dbname)
                mod.download(dbname, dt, bbox)


def run():
    """Main RHEAS routine."""
    config_filename, dbname, db_update = parseArgs()
    if dbname is None:
        dbname = "rheas"
    try:
        pg.connect("dbname={0}".format(dbname))
    except:
        print("Cannot connect to database {0}. Please restart it by running \n {1}/pg_ctl -D {2}/postgres restart".format(
            dbname, rpath.bins, rpath.data))
        sys.exit()
    # check if database update is requested
    if db_update:
        print "Updating database!"
        update(dbname, config_filename)
    else:
        options = config.loadFromFile(config_filename)
        # check what simulations have been requested
        if "nowcast" in options:
            nowcast.execute(dbname, options)
        if "forecast" in options:
            forecast.execute(dbname, options)


if __name__ == '__main__':
    run()
