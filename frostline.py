#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import requests
from codecs import iterdecode
from csv import DictReader, DictWriter
from contextlib import closing
from datetime import datetime, timezone

# The vintage of the USDA/PRISM source data. Surfaced in manifest.json and on
# the homepage so consumers can tell 2012 zones from 2023 zones.
SOURCE_VINTAGE = '2023'
SOURCE_URL = 'https://prism.oregonstate.edu/phzm/'

zone_files = [
    'https://prism.oregonstate.edu/phzm/data/2023/phzm_us_zipcode_2023.csv',
    'https://prism.oregonstate.edu/phzm/data/2023/phzm_ak_zipcode_2023.csv',
    'https://prism.oregonstate.edu/phzm/data/2023/phzm_hi_zipcode_2023.csv',
    'https://prism.oregonstate.edu/phzm/data/2023/phzm_pr_zipcode_2023.csv'
]


class Coordinates:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


class ZipData:
    def __init__(self, zone, temperature_range, coordinates):
        self.zone = zone
        self.temperature_range = temperature_range
        self.coordinates = coordinates


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ZipData):
            return {'zone': obj.zone, 'temperature_range': obj.temperature_range, 'coordinates': obj.coordinates}
        if isinstance(obj, Coordinates):
            return {'lat': obj.lat, 'lon': obj.lon}
        return json.JSONEncoder.default(self, obj)


def make_zip_to_zone_dict(iter_lines, zipcode_to_location):
    return {i['zipcode']: ZipData(i['zone'], i['trange'], zipcode_to_location.get(i['zipcode']))
            for i in DictReader(iter_lines)}


def zone_uris_to_dict(url, zipcode_to_location):
    with closing(requests.get(url, stream=True)) as r:
        return make_zip_to_zone_dict(iterdecode(r.iter_lines(), 'utf-8'), zipcode_to_location)


def write_bulk_files(records, uncovered_count):
    """Write the bulk dataset and the coverage manifest into api/.

    `records` is a sorted list of (zipcode, ZipData) for ZIPs that have both
    PHZ data and coordinates -- i.e. exactly the ZIPs that get a .json file.

    Coordinates are emitted as floats here, unlike the per-ZIP files, which
    keep them as strings for backwards compatibility.
    """
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # all.json -- one object keyed by ZIP code
    bulk = {
        zipcode: {
            'zone': data.zone,
            'temperature_range': data.temperature_range,
            'coordinates': {
                'lat': float(data.coordinates.lat),
                'lon': float(data.coordinates.lon),
            },
        }
        for zipcode, data in records
    }
    with open('api/all.json', 'w') as file:
        json.dump({
            'source': 'USDA Plant Hardiness Zone Map, via PRISM Climate Group',
            'source_url': SOURCE_URL,
            'source_vintage': SOURCE_VINTAGE,
            'generated': generated,
            'license': 'MIT',
            'count': len(bulk),
            'zipcodes': bulk,
        }, file)

    # all.csv -- flat table for spreadsheet and stats users
    with open('api/all.csv', 'w', newline='') as csvfile:
        writer = DictWriter(
            csvfile,
            fieldnames=['zipcode', 'zone', 'temperature_range', 'latitude', 'longitude'])
        writer.writeheader()
        for zipcode, data in records:
            writer.writerow({
                'zipcode': zipcode,
                'zone': data.zone,
                'temperature_range': data.temperature_range,
                'latitude': data.coordinates.lat,
                'longitude': data.coordinates.lon,
            })

    # manifest.json -- metadata plus the full list of covered ZIPs, so that
    # clients can check coverage without making 40,000 requests
    with open('api/manifest.json', 'w') as file:
        json.dump({
            'source': 'USDA Plant Hardiness Zone Map, via PRISM Climate Group',
            'source_url': SOURCE_URL,
            'source_vintage': SOURCE_VINTAGE,
            'generated': generated,
            'license': 'MIT',
            'repository': 'https://github.com/waldoj/frostline',
            'endpoints': {
                'zipcode': 'https://phzmapi.org/{zipcode}.json',
                'bulk_json': 'https://phzmapi.org/all.json',
                'bulk_csv': 'https://phzmapi.org/all.csv',
                'manifest': 'https://phzmapi.org/manifest.json',
            },
            'count': len(records),
            'zipcodes_without_phz_data': uncovered_count,
            'zipcodes': [zipcode for zipcode, _ in records],
        }, file)

    print(f"wrote bulk files for {len(records)} zipcodes")

def main():

    with open('combined_zipcodes.csv', 'r') as zipcodes:
        zipcode_to_location = {
            i['zipcode']: Coordinates(lat=i['latitude'], lon=i['longitude'])
            for i in DictReader(zipcodes)}

    # See if we already have the source data, otherwise retrieve from PRISM website
    if os.path.isfile(zones_filename := 'zones.csv'):
        with open(zones_filename, 'rb') as zones:
            zip_to_zone = make_zip_to_zone_dict(
                zones.readlines(), zipcode_to_location)
    else:
        zip_to_zone = {k: v for zf in zone_files for k,
                       v in zone_uris_to_dict(zf, zipcode_to_location).items()}

    print(
        f"number of zipcodes with no PHZ data: {len(zipcode_to_location.keys() - zip_to_zone.keys())}")
    # Save this as an environment variable for use in a test
    os.environ['FROSTLINE_NULL_ZIPS'] = str(len(zipcode_to_location.keys() - zip_to_zone.keys()))
    print(
        f"zipcodes with PHZ data but no location: {zip_to_zone.keys() - zipcode_to_location.keys()}")

    os.makedirs('api', exist_ok=True)

    # output only the zipcodes for which we have coordinates
    for zipcode, data in ((z, d) for z, d in zip_to_zone.items() if d.coordinates):
        with open(f"api/{zipcode}.json", 'w') as file:
            file.write(json.dumps(data, cls=CustomJSONEncoder))

    write_bulk_files(records, null_zips)

if __name__ == "__main__":
    main()


# utility to combine the partial zipcode location csv files
def combine_zipcode_files():
    # create a base dict of zipcode locations with this dataset
    with open('zipcodes.csv', 'r') as zipcodes:
        zipcode_to_location = {
            i['zipcode']: Coordinates(lat=i['latitude'], lon=i['longitude'])
            for i in DictReader(zipcodes)}

    # overwrite any zipcodes in that dataset with this more reliable (but still incomplete) one
    with open('us-zip-code-latitude-and-longitude.csv', 'r') as zipcodes:
        zipcode_to_location.update({
            i['Zip']: Coordinates(lat=i['Latitude'], lon=i['Longitude'])
            for i in DictReader(zipcodes, delimiter=';')})

    with open('combined_zipcodes.csv', 'w', newline='') as csvfile:
        fieldnames = ['zipcode', 'latitude', 'longitude']
        writer = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for zipcode, coords in zipcode_to_location.items():
            writer.writerow(
                {fieldnames[0]: zipcode, fieldnames[1]: coords.lat, fieldnames[2]: coords.lon})
