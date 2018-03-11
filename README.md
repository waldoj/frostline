# Frostline

A parser for USDA plant hardiness zones. That data is provided in bulk by [the PRISM Climate Group at Oregon State University](http://www.prism.oregonstate.edu/projects/plant_hardiness_zones.php). This combines the four bulk files with ZIP location data, and creates a JSON file for each ZIP, functioning as a static API.

Note that _not every U.S. ZIP code is part of this dataset._ The source data, provided by PRISM, simply does not include every ZIP.

The resulting data is used to create an API at phzmapi.org, in format `ZIPCODE.json`, e.g. [`https://phzmapi.org/20001.json`](https://phzmapi.org/20001.json).

![Map of the U.S.](https://cloud.githubusercontent.com/assets/656758/8011208/c1b7ea48-0b84-11e5-967b-a496cdfe0fe0.jpg)

(Per PRISM Climate Group's Terms of Service, note that the above map is not the official USDA Plant Hardiness Zone Map.)

## Run It Yourself

`./frostline.py`

## Map The Data

You can generate a nice interactive map of the data. First convert the data to GeoJSON:

```
node map.js
```

This creates `map.geojson`. Then view `map.html` in a browser. You will need to serve the map on a simple web server (not at a `file://` URL) so that it can access the GeoJSON file on disk (`file://` URLs block access to other files). That was used by Josh Tauberer to generate the above map.

## Plant Hardiness Zones

This is the national standard for knowing which plants will grow where. It’s determined based on the average annual minimum temperature over the prior 30 years, with each zone comprising a 10°F band. There are 26 zones in all. The standard was developed by the U.S., but other countries have adopted the same standard. Companies that sell plants, seeds, roots, and bulbs  (e.g., Burpee) use these zones to help customers understand what will thrive in their area, and to decide when to ship orders to help them to thrive. For more information, see [the Wikipedia entry](http://en.wikipedia.org/wiki/Hardiness_zone) or the [USDA’s explanation](http://planthardiness.ars.usda.gov/PHZMWeb/About.aspx).
