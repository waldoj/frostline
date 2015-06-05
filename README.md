# Frostline

A parser and resulting dataset for USDA plant hardiness zones.  It uses the ZIP-querying API built into [the U.S. Department of Agriculture’s Plant Hardiness Zone website](http://planthardiness.ars.usda.gov/) (e.g., `http://planthardiness.ars.usda.gov/PHZMWeb/ZipProxy.ashx?ZipCode=55555`) to retrieve the plant hardiness zone data for every ZIP code, one by one. Rate-limited to 1 query per second, this takes a little over 8 hours to run.

## Download the Resulting Data

* [CSV](hardiness_zones.csv) (1 MB)
* [SQLite](hardiness_zones.sqlite) (1.8 MB)
