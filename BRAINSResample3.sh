#!/bin/bash
# Set some default values:

outputVolume=unset

PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long outputVolume:,delta: -- "$@")

eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    -v | --outputVolume) outputVolume="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "creating outputVolume : $outputVolume"

touch "$outputVolume"
#echo "resampled" >> $1
