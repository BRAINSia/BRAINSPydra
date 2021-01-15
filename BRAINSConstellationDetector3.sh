#!/bin/bash
# Set some default values:

outputVolume=unset

PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long outputLandmarksInInputSpace:,outputResampledVolume:,outputTransform:,outputLandmarksInACPCAlignedSpace:,writeBranded2DImage: -- "$@")

eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
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

touch "$outputLandmarksInInputSpace"
touch "$outputResampledVolume"
touch "$outputTransform"
touch "$outputLandmarksInACPCAlignedSpace"
touch "$writeBranded2DImage"

echo "bcd" >> "$outputLandmarksInInputSpace"
echo "bcd" >> "$outputResampledVolume"
echo "bcd" >> "$outputTransform"
echo "bcd" >> "$outputLandmarksInACPCAlignedSpace"
echo "bcd" >> "$writeBranded2DImage"