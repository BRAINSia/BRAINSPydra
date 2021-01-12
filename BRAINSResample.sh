#!/bin/bash

function BRAINSResample
{
cp $1 "${1%$2}_resampled$2" 
return "${1%$2}_resampled$2"
}
#mv $1 "${1%$2}_resampled$2"
