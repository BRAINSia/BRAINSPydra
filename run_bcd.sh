#!/bin/bash

SESS_OUTPUT_DIR=/localscratch/Users/cjohnson30/output_dir
OUT_FILE_BASE=out_file
INPUT_VOL=/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples/sub-012716_ses-15544_run-004_T1w.nii.gz

cmd=$(echo BRAINSConstellationDetector \
--LLSModel \/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5 \
--acLowerBound 80.000000 \
--atlasLandmarkWeights \Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts \
--atlasLandmarks /Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv \
--houghEyeDetectorMode 1 \
--inputTemplateModel /Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl \
--inputVolume /Shared/sinapse/chdi_bids/PREDICTHD_BIDS_DEFACE/sub-697343/ses-50028/anat/sub-697343_ses-50028_run-002_rec-physicalACPC_T1w.nii.gz \
--interpolationMode Linear \
--outputLandmarksInACPCAlignedSpace ${SESS_OUTPUT_DIR}/${OUT_FILE_BASE}_BCD_ACPC_Landmarks.fcsv \
--outputLandmarksInInputSpace ${SESS_OUTPUT_DIR}/${OUT_FILE_BASE}_BCD_Original.fcsv \
--outputResampledVolume ${SESS_OUTPUT_DIR}/${OUT_FILE_BASE}_BCD_ACPC.nii.gz \
--outputTransform ${SESS_OUTPUT_DIR}/${OUT_FILE_BASE}_BCD_Original2ACPC_transform.h5 \
--writeBranded2DImage ${SESS_OUTPUT_DIR}/${OUT_FILE_BASE}_BCD_Branded2DQCimage.png \
--inputVolume ${INPUT_VOL})
echo "RUNNING: $cmd"
eval $cmd

