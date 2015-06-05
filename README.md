# Frostline

A parser and resulting dataset for USDA plant hardiness zones.  It uses the ZIP-querying API built into [the U.S. Department of Agriculture’s Plant Hardiness Zone website](http://planthardiness.ars.usda.gov/) (e.g., `http://planthardiness.ars.usda.gov/PHZMWeb/ZipProxy.ashx?ZipCode=55555`) to retrieve the plant hardiness zone data for every ZIP code, one by one. Rate-limited to 1 query per second, this takes a little over 8 hours to run.

## Using it

`./frostline.py -z zipcodes.csv`

## Download the Resulting Data

* [CSV](hardiness_zones.csv) (1 MB)
* [SQLite](hardiness_zones.sqlite) (1.8 MB)

## Use the API

[The `/api/` directory](https://github.com/waldoj/frostline/tree/gh-pages/api) of the `gh-pages` branch of this repo constitutes a lightweight API. For example, request [`https://waldoj.github.io/frostline/api/20001.json`](https://waldoj.github.io/frostline/api/20001.json) to get the zone data for Washington DC:

```json
{
    "zone": "7a",
    "coordinates": {
        "lat": 38.89,
        "lon": -77.03
    }
}
```

Use whatever ZIP you like in place of `20001`.

## Map

You can generate a nice interactive map of the data. First convert the data to GeoJSON:

	node map.js

This creates `map.geojson`. Then view `map.html` in a browser. You will need to serve the map on a simple web server (not at a file: URL) so that it can access the GeoJSON file on disk (file: URLs block access to other files).

![Map of the U.S.](https://cloud.githubusercontent.com/assets/656758/8011208/c1b7ea48-0b84-11e5-967b-a496cdfe0fe0.jpg)
