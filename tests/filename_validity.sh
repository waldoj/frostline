#!/bin/bash

OUTPUT="$(ls api/ |egrep -v [0-9]{5}\.json)"
if [ ${#OUTPUT} -ge 1 ]
	then exit 1
fi
