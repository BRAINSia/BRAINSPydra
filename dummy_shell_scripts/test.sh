#!/bin/bash

PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long output: -- "$@")

eval set -- "$PARSED_ARGUMENTS"
while :
do
  case "$1" in
  --output) set -f
        IFS=','
        outputs=($2)
        shift 2 ;;
  --) shift; break ;;
  esac
done

for i in "${outputs[@]}"; do
  echo "touching ${i}"
  touch "${i}"
  echo "ants_registration" >> "${i}"
done
#for var in "$@"; do touch file"$var".txt; done