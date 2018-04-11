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
import yaml

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
    if os.path.isfile(source_data):
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


# Export the ZIP data to JSON, to create a static API.
def create_zip_api():

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

# Establish stub JSON files for each zone, to be aliased for coordinates.
def create_zone_json():

    # We need the YAML listing PHZs.
    source_data = 'zones.yml'
    if os.path.isfile(source_data):
        zones = open(source_data, 'r')
    else:
        print source_data + "could not be found."
        sys.exit(1)

    # Create the /api/ directory, if it doesn't exist.
    if not os.path.exists('api'):
        os.makedirs('api')

    # Iterate through each PHZ and generate a JSON file.
    for zone, temps in yaml.load(zones).items():
        phz = {}
        phz['zone'] = zone;
        phz['temperature_range'] = temps;
        
        # Write this to a stub file.
        file = open('api/' + zone + ".json", 'w')
        file.write(json.dumps(phz))
        file.close()

# Convert an ASC file to a seris of filesystem aliases (symbolic links).
def create_coord_api(asc_file):

    if os.path.isfile(asc_file) is False:
        print asc_file + "could not be found."
        sys.exit(1)

    # Read in PHZ data.
    zones = {}
    phz = open('zones.yml', 'r')
    for zone, temps in yaml.load(phz).items():
        zones[zone] = {}
        temps = temps.split(' to ')
        zones[zone]['low'] = temps[0]
        zones[zone]['high'] = temps[1]

    with open(asc_file) as f:

        # Iterate through each row in the file.
        row_num=0
        map = {}
        for row in enumerate(f):

            # Remove cruft.
            fields = row[1].rstrip()

            # Extract header data about the file.
            if row_num < 6:
                value = fields.split(' ')[1]
                if row_num == 2:
                    map['x_corner'] = float(value)
                elif row_num == 3:
                    map['y_corner'] = float(value)
                elif row_num == 4:
                    map['cell_size'] = float(value)
                elif row_num == 5:
                    map['nodata_value'] = value
                row_num+=1
                continue

            # Now parse actual data.
            column_num=0
            fields = fields.split(' ')
            for field in fields:

                # If this field has no value, skip it.
                if field == map['nodata_value']:
                    continue
                
                # Figure out what zone this field is in.
                place = {}
                place['temp'] = (int(field) / 100 * (9/5)) + 32
                for zone, temps in zones.items():
                    if float(place['temp']) >= float(temps['low']) and float(place['temp']) <= float(temps['high']):
                        place['zone'] = zone
                        break

                # Assign this field to a latitude and longitude.
                place['lon'] = round(map['x_corner'] + map['cell_size'] * column_num, 2)
                place['lat'] = round(map['y_corner'] + map['cell_size'] * row_num, 2)

                # Create a symlink, naming the file for the coordinates.
                filename = 'api/' + str(place['lon']) + ',' + str(place['lat']) + '.json'
                try:
                    os.symlink(place['zone'] + '.json', filename)
                except OSError:
                    pass

                column_num+=1

            row_num+=1

if __name__ == "__main__":
    main()
    create_zip_api()
    create_zone_json()
    create_coord_api('phm_us_grid/phm_us.asc')
