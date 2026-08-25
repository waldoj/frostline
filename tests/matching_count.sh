#!/bin/bash

# The number of per-ZIP JSON files should equal the number of ZIP codes in
# combined_zipcodes.csv, less those with no PHZ data. The latter count is
# recorded in manifest.json when the data is built.
CSV_COUNT="$(wc -l < combined_zipcodes.csv |sed -e 's/^[ \t]*//')"
CSV_COUNT="$((CSV_COUNT - 1))"

NULL_ZIPS="$(python3 -c "import json; print(json.load(open('api/manifest.json'))['zipcodes_without_phz_data'])")"
EXPECTED="$((CSV_COUNT - NULL_ZIPS))"

DIR_COUNT="$(ls api/ |egrep '^[0-9]{5}\.json$' |wc -l |sed -e 's/^[ \t]*//')"

if [ "$EXPECTED" -ne "$DIR_COUNT" ]; then
	echo "Expected $EXPECTED JSON files, but found $DIR_COUNT."
	exit 1
fi
