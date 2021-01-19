#!/bin/bash
# Set some default values:


# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long inputVolumes:,outputVolumes:,atlasDefinition:,atlasToSubjectTransform:,atlasToSubjectTransformType:,debuglevel:,filterIteration:,filterMethod:,inputVolumeTypes:,interpolationMode:,maxBiasDegree:,maxIterations:,outputDir:,outputDirtyLabels:,outputFormat:,outputLabels:,posteriorTemplate:,purePlugsThreshold:,restoreState:,saveState:,useKNN: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --inputVolumes)  inputVolumes="$2"  ; shift 2 ;;
    --atlasDefinition)  atlasDefinition="$2"  ; shift 2 ;;
    --atlasToSubjectTransform) atlasToSubjectTransform="$2" ; shift 2 ;;
    --atlasToSubjectTransformType)         atlasToSubjectTransformType="$2"         ; shift 2 ;;
    --debuglevel)     debuglevel="$2"     ; shift 2 ;;
    --filterIteration)  filterIteration="$2"  ; shift 2 ;;
    --filterMethod) filterMethod="$2" ; shift 2 ;;
    --inputVolumeTypes)         inputVolumeTypes="$2"         ; shift 2 ;;
    --interpolationMode)     interpolationMode="$2"     ; shift 2 ;;
    --maxBiasDegree)  maxBiasDegree="$2"  ; shift 2 ;;
    --maxIterations) maxIterations="$2" ; shift 2 ;;
    --outputDir)         outputDir="$2"         ; shift 2 ;;
    --outputDirtyLabels)     outputDirtyLabels="$2"     ; shift 2 ;;
    --outputFormat)  outputFormat="$2"  ; shift 2 ;;
    --outputLabels) outputLabels="$2" ; shift 2 ;;
    --outputVolumes)     outputVolumes="$2"     ; shift 2 ;;
    --posteriorTemplate)         posteriorTemplate="$2"         ; shift 2 ;;
    --purePlugsThreshold)     purePlugsThreshold="$2"     ; shift 2 ;;
    --restoreState)     restoreState="$2"     ; shift 2 ;;
    --saveState)     saveState="$2"     ; shift 2 ;;
    --useKNN)     useKNN="$2"     ; shift 2 ;;
    --) shift; break ;;
   esac
 done

echo "creating outputVolume : $outputVolumes"

# Create a file for the outputVolume
echo "touching $outputVolumes"
touch "$outputVolumes"
touch "$outputLabels"
#touch "$atlasToSubjectTransform"

# Add the contents of the inputVolume to the top of outputVolume
#cat "$inputVolumes" >> "$outputVolumes"

# Append "resampled" to outputVolume
#echo "abc" >> "$outputVolumes"

#echo "creating outputVolume : $inputVolumes"
#
## Create a file for the outputVolume
#echo "touching $inputVolumes"
#touch "$inputVolumes"
#
## Add the contents of the inputVolume to the top of outputVolume
##cat "$inputVolumes" >> "$outputVolumes"
#
## Append "resampled" to outputVolume
#echo "abc" >> "$inputVolumes"