import pydra
import os
from pathlib import Path
from BIDSFilename import *

def run_bcd():
	os.system("bash run_bcd.sh")	



	

@pydra.mark.task
def run_bcd(input_vol):
	SESS_OUTPUT_DIR="/localscratch/Users/cjohnson30/output_dir"
	INPUT_VOL=input_vol
	filename_dict = BIDSFilename(input_vol).attribute_dict
	file_id = f'sub-{filename_dict["sub"]}_ses-{filename_dict["ses"]}_run-{filename_dict["run"]}'
	OUT_FILE_BASE = file_id

	cmd = "BRAINSConstellationDetector"
	args = ["--LLSModel", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5", \
        "--acLowerBound", "80.000000", \
        "--atlasLandmarkWeights", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts", \
        "--atlasLandmarks", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv", \
        "--houghEyeDetectorMode", "1", \
        "--inputTemplateModel", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl", \
        "--inputVolume", "/Shared/sinapse/chdi_bids/PREDICTHD_BIDS_DEFACE/sub-697343/ses-50028/anat/sub-697343_ses-50028_run-002_rec-physicalACPC_T1w.nii.gz", \
        "--interpolationMode", "Linear", \
        "--outputLandmarksInACPCAlignedSpace", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_ACPC_Landmarks.fcsv", \
        "--outputLandmarksInInputSpace", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Original.fcsv", \
        "--outputResampledVolume", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_ACPC.nii.gz", \
        "--outputTransform", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Original2ACPC_transform.h5", \
        "--writeBranded2DImage", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Branded2DQCimage.png", \
        "--inputVolume", f"{INPUT_VOL}"]

	shelly = pydra.ShellCommandTask(name="shelly", executable=cmd, args=args)
	with pydra.Submitter(plugin="cf") as sub:
		sub(shelly)
	print(shelly.result())
p = Path("/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples/")
all_t1 = p.glob("*")
input_vols = list(all_t1)
task1 = run_bcd(input_vol="/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples/sub-012716_ses-15544_run-004_T1w.nii.gz")
#task1 = run_bcd(input_vol=input_vols)
#task1.split("input_vol")
task1()
print(task1.result())
# cmd = ["bash", "/localscratch/Users/cjohnson30/BRAINSPydra/run_bcd.sh"]

# cmd = "BRAINSConstellationDetector"
# args = "/localscratch/Users/cjohnson30/BRAINSPydra/run_bcd.sh"
# 
# 
# SESS_OUTPUT_DIR="/localscratch/Users/cjohnson30/output_dir"
# OUT_FILE_BASE="out_file"
# 
# p = Path("/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples/")
# all_t1 = p.glob("*")
# 
# for t1 in all_t1:
# 	filename_dict = BIDSFilename(t1).attribute_dict
# 	file_id = f'sub-{filename_dict["sub"]}_ses-{filename_dict["ses"]}_run-{filename_dict["run"]}'
# 	OUT_FILE_BASE = file_id
# 	INPUT_VOL="/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples/sub-012716_ses-15544_run-004_T1w.nii.gz"
# 	INPUT_VOL=t1
# 	print(OUT_FILE_BASE, INPUT_VOL)
# 
# 	cmd = "BRAINSConstellationDetector"
# 	args = ["--LLSModel", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5", \
# 	"--acLowerBound", "80.000000", \
# 	"--atlasLandmarkWeights", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts", \
# 	"--atlasLandmarks", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv", \
# 	"--houghEyeDetectorMode", "1", \
# 	"--inputTemplateModel", "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl", \
# 	"--inputVolume", "/Shared/sinapse/chdi_bids/PREDICTHD_BIDS_DEFACE/sub-697343/ses-50028/anat/sub-697343_ses-50028_run-002_rec-physicalACPC_T1w.nii.gz", \
# 	"--interpolationMode", "Linear", \
# 	"--outputLandmarksInACPCAlignedSpace", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_ACPC_Landmarks.fcsv", \
# 	"--outputLandmarksInInputSpace", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Original.fcsv", \
# 	"--outputResampledVolume", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_ACPC.nii.gz", \
# 	"--outputTransform", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Original2ACPC_transform.h5", \
# 	"--writeBranded2DImage", f"{SESS_OUTPUT_DIR}/{OUT_FILE_BASE}_BCD_Branded2DQCimage.png", \
# 	"--inputVolume", f"{INPUT_VOL}"]
# 
# 	shelly = pydra.ShellCommandTask(name="shelly", executable=cmd, args=args)
# 	with pydra.Submitter(plugin="cf") as sub:
# 		sub(shelly)
# 	print(shelly.result())

#run_bcd()
#bcd_task = run_bcd_pydra()
#bcd_task.result()
