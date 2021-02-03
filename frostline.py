#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests
from codecs import iterdecode
from csv import DictReader, DictWriter
from contextlib import closing

zone_files = [
    'http://www.prism.oregonstate.edu/projects/public/phm/phm_us_zipcode.csv',
    'http://www.prism.oregonstate.edu/projects/public/phm/phm_ak_zipcode.csv',
    'http://www.prism.oregonstate.edu/projects/public/phm/phm_hi_zipcode.csv',
    'http://www.prism.oregonstate.edu/projects/public/phm/phm_pr_zipcode.csv'
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
    print(
        f"zipcodes with PHZ data but no location: {zip_to_zone.keys() - zipcode_to_location.keys()}")

    os.makedirs('api', exist_ok=True)

    # output only the zipcodes for which we have coordinates
    for zipcode, data in ((z, d) for z, d in zip_to_zone.items() if d.coordinates):
        with open(f"api/{zipcode}.json", 'w') as file:
            file.write(json.dumps(data, cls=CustomJSONEncoder))


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
