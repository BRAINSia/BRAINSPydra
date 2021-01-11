#!/bin/bash
# Set some default values:

outputVolume=unset

PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long outputVolume:,inputVolume: -- "$@")

eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    -o | --outputVolume) outputVolume="$2" ; shift 2 ;;
    -i | --inputVolume) inputVolume="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "creating outputVolume : $outputVolume"

echo "touching $outputVolume"
touch "$outputVolume"
cat "$inputVolume" >> "$outputVolume"
echo "resampled" >> "$outputVolume"
