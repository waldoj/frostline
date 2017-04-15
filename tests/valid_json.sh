#!/bin/bash

for json in api/*.json; do php -r "if ( ! \$foo=json_decode(file_get_contents('$json')) ) echo \"$json\n\";"; done
