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
    description="A scraper for USDA Plant Hardiness Zone data",
    epilog="https://github.com/waldoj/frostline/")
parser.add_argument('-z', '--zipfile', help="the ZIP Code CSV file", metavar="zips.csv", required=True)
parser.add_argument('-v', '--verbose', help="verbose mode", action='store_true')
args = parser.parse_args()
verbose = args.verbose
zipfile = args.zipfile

def main():

    # We keep track of how many consecutive errors the API throws, to stop if there are too many.
    api_error_count = 0

   # Make sure that we can connect to the database.
    try:
        db = sqlite3.connect('hardiness_zones.sqlite')
    except sqlite3.error, e:
        print "Count not connect to SQLite, with error %s:" % e.args[0]
        sys.exit(1)

    # Create a SQLite cursor.
    cursor = db.cursor()

    # See if the zip table already exists.
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='zip'")
    exists = cursor.fetchone()

    # Start iterating through our list of ZIP codes.
    with open(zipfile, 'rb') as csvfile:

        # Iterate through the lines in our input file.
        csvreader = csvkit.DictReader(csvfile)
        for record in csvreader:

            # Note the time at which we started reading this record, to make sure that we don't hit
            # the API more than per second.
            start_time = time.time()

            # If this ZIP is already stored in the database, skip to the next ZIP.
            cursor.execute("SELECT 1 FROM zip WHERE zipcode = ?", (record['zipcode'],))
            exists = cursor.fetchone()
            if exists is not None:
                if verbose:
                    print "ZIP already retrieved"
                else:
                    sys.stdout.write('…')
                    sys.stdout.flush()
                continue

            # Encode the field as a key/value pair, for our query.
            url_parameters = {}
            url_parameters['ZipCode'] = record['zipcode']
            url_parameters = urllib.urlencode(url_parameters)

            # Assemble the URL.
            request_url = 'http://planthardiness.ars.usda.gov/PHZMWeb/ZipProxy.ashx?' \
                + url_parameters

            # Fetch that URL.
            try:
                response = urllib2.urlopen(request_url)
            except urllib2.URLError as e:
                sys.stdout.write('‽')
                sys.stdout.flush()
                api_error_count += 1
                if api_error_count == 10:
                    print "Too many API errors: halting."
                    sys.exit()
                continue

            # Since this worked, reset the API error count to zero.
            api_error_count = 0

            # Get the text returned by the server.
            hardiness = response.read()

            # If no zone data was returned by the server, then report this as a failure and skip to
            # the next ZIP.
            if "Zone " not in hardiness:
                if verbose:
                    print "API returned no data for that ZIP"
                    print hardiness
                else:
                    sys.stdout.write('✗')
                    sys.stdout.flush()
                api_error_count += 1
                if api_error_count == 10:
                    print "Too many API errors: halting."
                    sys.exit()
                continue

            # The server returns a string like "Zone 12b :  55 to 60  (F)" -- we only want the
            # "12b" bit.
            tmp = hardiness.split()
            hardiness = tmp[1]

            # Insert the ZIP, hardiness zone, city, state, latitude, and longitude into the DB.
            cursor.execute("INSERT INTO zip VALUES(?, ?, ?, ?, ?, ?)", \
                (record['zipcode'], hardiness, record['city'], record['state'], \
                record['latitude'], record['longitude']))
            db.commit()

            # Report success to the terminal.
            if verbose:
                print "ZIP " + record['zipcode'] + " hardiness " + hardiness
            else:
                sys.stdout.write('✓')
                sys.stdout.flush()

            # Pause long enough that 1 second has elapsed for this loop, to avoid hammering the API.
            if time.time() - start_time < 1:
                time.sleep(1 - (time.time() - start_time))

    # Close our database connection.
    db.close()

if __name__ == "__main__":
    main()
