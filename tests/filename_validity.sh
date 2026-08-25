#!/bin/bash

# Every file in api/ must either be a five-digit ZIP code JSON file or one of
# the known bulk/website files.
OUTPUT="$(ls api/ | egrep -v '^([0-9]{5}\.json|all\.json|all\.csv|manifest\.json|index\.html|error-404\.json)$')"
if [ ${#OUTPUT} -ge 1 ]; then
	echo "The following filenames are invalid: $OUTPUT"
	exit 1
fi
