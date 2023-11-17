#!/bin/bash

FILE_LENGTH="$(wc -l combined_zipcodes.csv |sed -e 's/^[ \t]*//' |cut -d " " -f 1)"
FILE_LENGTH="$((FILE_LENGTH - 1))"
#### NEXT UP: SUBTRACT number of zipcodes with no PHZ data: 2536
DIR_COUNT="$(ls api/ |wc -l)"

if [ "$FILE_LENGTH" -ne "$DIR_COUNT" ]; then
	echo "There are $FILE_LENGTH CSV entries, but $DIR_COUNT JSON files."
	exit 1
fi
