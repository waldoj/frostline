#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csvkit
import os
import errno
import glob
import sys
import time
import math
import sqlite3
import urllib
import urllib2
import json
import argparse
import time

parser = argparse.ArgumentParser(
    description="A tool to turn USDA Plant Hardiness Zone files into an API",
    epilog="https://github.com/waldoj/frostline/")
parser.add_argument('-v', '--verbose', help="verbose mode", action='store_true')
args = parser.parse_args()
verbose = args.verbose


def main():

    # Make sure that we can connect to the database.
    try:
        db = sqlite3.connect('hardiness_zones.sqlite')
    except sqlite3.error, e:
        print "Count not connect to SQLite, with error %s:" % e.args[0]
        sys.exit(1)

    # See if we already have the source data.
    source_data = 'zones.csv'
    if os.path.isfile('zones.csv'):
        pass
    else:
        sources = ['http://www.prism.oregonstate.edu/projects/public/phm/phm_us_zipcode.csv',
                    'http://www.prism.oregonstate.edu/projects/public/phm/phm_ak_zipcode.csv',
                    'http://www.prism.oregonstate.edu/projects/public/phm/phm_hi_zipcode.csv',
                    'http://www.prism.oregonstate.edu/projects/public/phm/phm_pr_zipcode.csv']
        zonefile = urllib.URLopener()
        i=1
        for source in sources:
            try:
                zonefile.retrieve(source, str(i) + '.csv')
            except Exception,e:
                print "Fatal error: Could not download source file. ", e
                sys.exit()
            i += 1

    # Create a SQLite cursor.
    cursor = db.cursor()

    # See if the zip database table already exists.
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='zip'")
    exists = cursor.fetchone()

    # If the database table doesn't exist, create it.
    if exists is None:
        cursor.execute("CREATE TABLE zip(zipcode TEXT PRIMARY KEY NOT NULL, "
            + "zone TEXT, temperatures TEXT, city TEXT, state TEXT, latitude INTEGER, longitude INTEGER)")
        db.commit()

        # Import the CSV file into the database
        with open('zipcodes.csv','rb') as zips:
            dr = csvkit.DictReader(zips)
            to_db = [(i['zipcode'], i['city'], i['state'], i['latitude'], i['longitude']) for i in dr]
        cursor.executemany("INSERT INTO zip (zipcode, city, state, latitude, longitude) VALUES (?, ?, ?, ?, ?);", to_db)
        db.commit()

    # Now load our climate data.
    zone_files = [1, 2, 3, 4]
    for zone_file in zone_files:
        with open(str(zone_file) + '.csv','rb') as zips:
            dr = csvkit.DictReader(zips)
            to_db = [(i['zone'], i['trange'], i['zipcode']) for i in dr]
        cursor.executemany("UPDATE zip SET zone=?, temperatures=? WHERE zipcode=?;", to_db)
        db.commit()
        os.remove(str(zone_file) + '.csv')

    # Close our database connection.
    db.close()


# Export the results to JSON, to create a static API.
def create_api():

    # Connect to the database, which we already know exists.
    db = sqlite3.connect('hardiness_zones.sqlite')
    db.row_factory = sqlite3.Row

    # Create a SQLite cursor.
    cursor = db.cursor()

    # Create the /api/ directory, if it doesn't exist.
    if not os.path.exists('api'):
        os.makedirs('api')

    # Iterate through all records.
    cursor.execute("SELECT zipcode, zone, temperatures, latitude, longitude FROM zip")
    for zip in cursor:

        # Save the record to a file.
        file = open("api/" + zip['zipcode'] + ".json", 'w')

        # Hideously manipulate the dict.
        record = dict()
        record['coordinates'] = dict()
        record['coordinates']['lat'] = zip['latitude']
        record['coordinates']['lon'] = zip['longitude']
        record['zone'] = zip['zone']
        record['temperature_range'] = zip['temperatures']

        # Write the contents and close the file.
        file.write(json.dumps(record))
        file.close()

if __name__ == "__main__":
    main()
    create_api()
