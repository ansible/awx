#!/bin/bash

printf "READY\n";

while read line; do
  echo "Processing Event: $line" >&2;
  kill -SIGQUIT $PPID
done < /dev/stdin
