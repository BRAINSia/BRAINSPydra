#!/bin/bash
# Set some default values:

outputVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long outputVolume:,inputVolume: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --outputVolume) outputVolume="$2" ; shift 2 ;;
    --inputVolume) inputVolume="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "creating outputVolume : $outputVolume"

# Create a file for the outputVolume
echo "touching $outputVolume"
touch "$outputVolume"

# Add the contents of the inputVolume to the top of outputVolume
cat "$inputVolume" >> "$outputVolume"

# Append "resampled" to outputVolume
echo "resampled" >> "$outputVolume"
