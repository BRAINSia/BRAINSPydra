#!/bin/bash
# Set some default values:

outputVolume=unset

# Set which arguments will be considered valid arguments
PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long default:,createFiles:,input:,contents:,inputs:,verbose:,collapse-output-transforms:,dimensionality:,float:,initial-moving-transform:,initialize-transforms-per-stage:,interpolation:,output:,transform:,metric:,convergence:,smoothing-sigmas:,shrink-factors:,use-estimate-learning-rate-once:,use-histogram-matching:,masks:,winsorize-image-intensities:,write-composite-transform: -- "$@")


#PARSED_ARGUMENTS=$(getopt -n alphabet -o v:: --long : output: -- "$@")

# Extract the arguments into variables
eval set -- "$PARSED_ARGUMENTS"
while :
do
    case "$1" in
    --output) output="$2" ; shift 2;;
    --default) default="$2" ; shift 2;;
    --verbose) verbose="$2" ; shift 2 ;;
    --dimensionality) dimensionality="$2" ; shift 2 ;;
    --float) float="$2" ; shift 2 ;;
    --initial-moving-transform) initial_moving_transform="$2" ; shift 2 ;;
    --initialize-transforms-per-stage) initialize-transforms-per-stage="$2" ; shift 2 ;;
    --interpolation) interpolation="$2" ; shift 2 ;;
    --createFiles) set -f
              IFS=','
              createFiles=($2)
              shift 2 ;;
    --inputs) set -f
              IFS=','
              input=($2)
              shift 2 ;;
    --contents) set -f
              IFS=','
              contents=($2)
              shift 2 ;;
    --transform) transform="$2" ; shift 2 ;;
    --metric) metric="$2" ; shift 2 ;;
    --convergence) convergence="$2" ; shift 2 ;;
    --smoothing-sigmas) smoothing-sigmas="$2" ; shift 2 ;;
    --shrink-factors) shrink-factors="$2" ; shift 2 ;;
    --use-estimate-learning-rate-once) use-estimate-learning-rate-once="$2" ; shift 2 ;;
    --use-histogram-matching) use-histogram-matching="$2" ; shift 2 ;;
    --masks) masks="$2" ; shift 2 ;;
    --winsorize-image-intensities) winsorize-image-intensities="$2" ; shift 2 ;;
    --write-composite-transform) write-composite-transform="$2" ; shift 2 ;;
    --) shift; break ;;
   esac
 done

# Create a file for the outputVolume
#echo "touching $output"
#touch "$output"
#
## Append "resampled" to outputVolume
#echo "ants_registration" >> "$output"

for i in "${createFiles[@]}"; do
  echo "touching ${i}"
  touch "${i}"
done

touch "$output"
for i in "${contents[@]}"; do
  echo "${i}" >> "$output"
#  echo contents >> "${i}"
done
#for var in "$@"; do touch file"$var".txt; done