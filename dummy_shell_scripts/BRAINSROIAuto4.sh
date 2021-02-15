#!/bin/bash
# Set some default values:

outputVolume=unset
outputROIMaskVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long outputVolume:,inputVolume:,outputROIMaskVolume: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --outputVolume) outputVolume="$2" ; shift 2 ;;
    --outputROIMaskVolume) outputROIMaskVolume="$2" ; shift 2 ;;
    --inputVolume) inputVolume="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done


# Create a file for the outputVolume
if [ "$outputVolume" != unset ];
then
  touch "$outputVolume"
fi

if [ "$outputROIMaskVolume" != unset ];
then
  touch "$outputROIMaskVolume"
fi

# Add the contents of the inputVolume to the top of outputVolume
#cat "$inputVolume" >> "$outputVolume"

# Append "resampled" to outputVolume
#echo "roi_auto" >> "$outputVolume"
