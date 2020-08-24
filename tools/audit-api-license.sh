#!/bin/bash

echo "---------- requirements.txt --------------"
for each in `cat requirements/requirements.txt| awk -F= '{print $1}' | tr -d "[]"`
do
    if [ ! -f docs/licenses/$each.txt ]; then
        echo No license for $each
    fi
done
echo "---------- end requirements.txt --------------"
