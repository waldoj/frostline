#!/bin/bash

FILE_LENGTH="$(wc -l zipcodes.csv |cut -d " " -f 4)"
FILE_LENGTH=$(($FILE_LENGTH - 1))
DIR_COUNT="$(ls api/ |wc -l)"

if [ "$FILE_LENGTH" -ne "$DIR_COUNT" ]
	then exit 1
fi
