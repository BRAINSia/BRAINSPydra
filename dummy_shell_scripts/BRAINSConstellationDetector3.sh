#!/bin/bash
# Set some default values:

outputVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long inputVolume:,outputLandmarksInInputSpace:,outputResampledVolume:,outputTransform:,outputLandmarksInACPCAlignedSpace:,writeBranded2DImage: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --inputVolume)   inputVolume="$2"   ; shift 2 ;;
    --outputLandmarksInInputSpace)   outputLandmarksInInputSpace="$2"   ; shift 2 ;;
    --outputResampledVolume)             outputResampledVolume="$2"             ; shift 2 ;;
    --outputTransform) outputTransform="$2" ; shift 2 ;;
    --outputLandmarksInACPCAlignedSpace)       outputLandmarksInACPCAlignedSpace="$2"       ; shift 2 ;;
    --writeBranded2DImage)  writeBranded2DImage="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "touching $outputLandmarksInInputSpace"
echo "touching $outputResampledVolume"
echo "touching $outputTransform"
echo "touching $outputLandmarksInACPCAlignedSpace"
echo "touching $writeBranded2DImage"

# Create output files with the names specified
touch "$outputLandmarksInInputSpace"
touch "$outputResampledVolume"
touch "$outputTransform"
touch "$outputLandmarksInACPCAlignedSpace"
touch "$writeBranded2DImage"

# Add the contents of the inputVolume to the beginning of each output file
cat "$inputVolume" >> "$outputLandmarksInInputSpace"
cat "$inputVolume" >> "$outputResampledVolume"
cat "$inputVolume" >> "$outputTransform"
cat "$inputVolume" >> "$outputLandmarksInACPCAlignedSpace"
cat "$inputVolume" >> "$writeBranded2DImage"


# Append "bcd" to each file
echo "bcd" >> "$outputLandmarksInInputSpace"
echo "bcd" >> "$outputResampledVolume"
echo "bcd" >> "$outputTransform"
echo "bcd" >> "$outputLandmarksInACPCAlignedSpace"
echo "bcd" >> "$writeBranded2DImage"