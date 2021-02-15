#!/bin/bash
# Set some default values:

outputVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long inputFixedLandmarkFilename:,inputMovingLandmarkFilename:,inputWeightFilename:,outputTransformFilename: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    -f | --inputFixedLandmarkFilename) inputFixedLandmarkFilename="$2" ; shift 2 ;;
    -m | --inputMovingLandmarkFilename) inputMovingLandmarkFilename="$2" ; shift 2 ;;
    -w | --inputWeightFilename) inputWeightFilename="$2" ; shift 2 ;;
    -o | --outputTransformFilename) outputTransformFilename="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "creating outputVolume : $outputVolume"

# Create a file for the outputVolume
echo "touching $outputTransformFilename"
touch "$outputTransformFilename"

# Append "resampled" to outputVolume
echo "landmarkInitializer" >> "$outputTransformFilename"
