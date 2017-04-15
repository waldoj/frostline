#!/bin/bash

FILE_LENGTH="$(wc -l zipcodes.csv |sed -e 's/^[ \t]*//' |cut -d " " -f 1)"
echo "Preliminary file length is $FILE_LENGTH"
FILE_LENGTH="$((FILE_LENGTH - 1))"
DIR_COUNT="$(ls api/ |wc -l)"

if [ "$FILE_LENGTH" -ne "$DIR_COUNT" ]; then
	echo "There are $FILE_LENGTH CSV entries, but $DIR_COUNT JSON files."
	exit 1
fi
