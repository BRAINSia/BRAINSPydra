#!/bin/bash
# Set some default values:

outputVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long cleanLabelVolume:,dirtyLabelVolume:,foregroundPriors:,inputProbabilityVolume:,nonAirRegionMask:,priorLabelCodes: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --cleanLabelVolume) cleanLabelVolume="$2" ; shift 2 ;;
    --dirtyLabelVolume) dirtyLabelVolume="$2" ; shift 2 ;;
    --foregroundPriors) foregroundPriors="$2" ; shift 2 ;;
    --inputProbabilityVolume) inputProbabilityVolume="$2" ; shift 2 ;;
    --nonAirRegionMask) nonAirRegionMask="$2" ; shift 2 ;;
    --priorLabelCodes) priorLabelCodes="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

touch "$dirtyLabelVolume"
touch "$cleanLabelVolume"


# Append "resampled" to outputVolume
echo "roi_auto" >> "$outputVolume"

echo "$foregroundPriors" >> "$dirtyLabelVolume"
echo "$inputProbabilityVolume" >> "$dirtyLabelVolume"
echo "$nonAirRegionMask" >> "$dirtyLabelVolume"
echo "$priorLabelCodes" >> "$dirtyLabelVolume"

echo "$foregroundPriors" >> "$cleanLabelVolume"
echo "$inputProbabilityVolume" >> "$cleanLabelVolume"
echo "$nonAirRegionMask" >> "$cleanLabelVolume"
echo "$priorLabelCodes" >> "$cleanLabelVolume"

