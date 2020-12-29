import pydra
from pathlib import Path
import nest_asyncio
import time

import attr
from nipype.interfaces.base import (
    Directory,
    File,
)
from pydra import ShellCommandTask
from pydra.engine.specs import SpecInfo, ShellSpec

from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector

#from resample_cmd import fill_resample_task
from bcd_cmd import fill_bcd_task

if __name__ == '__main__':
    subject1_json = {"in": {"t1": ["/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-052823_ses-43817_run-002_T1w.nii.gz",
                                   "/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-066260_ses-21713_run-002_T1w.nii.gz"], 
                            "ref": "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz", 
                            "transform": "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5"},
                     "out":{"output_dir": "/localscratch/Users/cjohnson30/output_dir"}}

    resample = BRAINSResample()
    bcd = BRAINSConstellationDetector()
    bcd.task = fill_bcd_task()

    resample.task.inputs.inputVolume = subject1_json["in"]["t1"]
    resample.task.inputs.referenceVolume = subject1_json["in"]["ref"]
    resample.task.inputs.warpTransform = subject1_json["in"]["transform"]
    
 
    wf = pydra.Workflow(name="wf", input_spec=["cmd1", "cmd2"])
    
    wf.inputs.cmd1 = "BRAINSResample"
    wf.inputs.cmd2 = "BRAINSConstellationDetector"
   
    # Set the inputs for Resample 
    resample.task.inputs.interpolationMode = "Linear"
    resample.task.inputs.pixelType = "binary"
    resample.task.inputs.outputVolume = f"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w_resampled.nii.gz" 
    resample.task.inputs.outputVolume = [
        f"/localscratch/Users/cjohnson30/output_dir/{Path(x).with_suffix('').with_suffix('').name}_resampled.nii.gz"
        for x in subject1_json['in']['t1']
    ]
    # Add the resample task to the pipeline 
    wf.add(resample.task.split(("inputVolume", "outputVolume")))
    
    # Set the inputs for BCD                  
    bcd.task.inputs.inputTemplateModel = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl",
    bcd.task.inputs.LLSModel = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5",
    bcd.task.inputs.acLowerBound = 80.000000,
    bcd.task.inputs.atlasLandmarkWeights = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts",
    bcd.task.inputs.atlasLandmarks = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv",
    bcd.task.inputs.houghEyeDetectorMode = 1,
    bcd.task.inputs.interpolationMode = "Linear" 
    bcd.task.inputs.resultsDir = subject1_json["out"]["output_dir"]
#    bcd.task.inputs.inputVolume = wf.BRAINSResample.lzout.outputVolume
#    bcd.task.inputs.outputLandmarksInInputSpace =  [
#        f"{bcd.task.inputs.resultsDir}/{Path(x).with_suffix('').with_suffix('').name}_BCD_Original.fcsv"
#        for x in subject1_json['in']['t1'] 
#    ]
#    bcd.task.inputs.outputResampledVolume = [
#        f"{bcd.task.inputs.resultsDir}/{Path(x).with_suffix('').with_suffix('').name}_BCD_ACPC.nii.gz"
#        for x in subject1_json['in']['t1']
#    ]
#    bcd.task.inputs.outputTransform = [
#        f"{bcd.task.inputs.resultsDir}/{Path(x).with_suffix('').with_suffix('').name}_BCD_Original2ACPC_transform.h5"
#        for x in subject1_json['in']['t1']
#    ]
#    bcd.task.inputs.outputLandmarksInACPCAlignedSpace = [
#        f"{bcd.task.inputs.resultsDir}/{Path(x).with_suffix('').with_suffix('').name}_BCD_ACPC_Landmarks.fcsv"
#        for x in subject1_json['in']['t1']
#    ]
#    bcd.task.inputs.outputLandmarksInInputSpace = f"{bcd.task.inputs.resultsDir}/sub-052823_ses-43817_run-002_T1w_BCD_Original.fcsv"
#    bcd.task.inputs.outputResampledVolume = f"{bcd.task.inputs.resultsDir}/sub-052823_ses-43817_run-002_T1w_BCD_ACPC.nii.gz"
#    bcd.task.inputs.outputTransform = f"{bcd.task.inputs.resultsDir}/sub-052823_ses-43817_run-002_T1w_BCD_Original2ACPC_transform.h5"
#    bcd.task.inputs.outputLandmarksInACPCAlignedSpace = "sub-052823_ses-43817_run-002_T1w_BCD_ACPC_Landmarks.fcsv" #f"{bcd.task.inputs.resultsDir}/sub-052823_ses-43817_run-002_T1w_BCD_ACPC_Landmarks.fcsv"
    # Add the bcd task to the pipeline
    wf.add(bcd.task.split((
            "inputVolume",
            "outputLandmarksInACPCAlignedSpace",
            "outputLandmarksInInputSpace",
            "outputResampledVolume",
            "outputTransform"))) 
    
    wf.set_output(
        [
            ("outVol", wf.BRAINSResample.lzout.outputVolume),
            ("outputLandmarksInACPCAlignedSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
            ("outputLandmarksInInputSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume", wf.BRAINSConstellationDetector.lzout.outputResampledVolume),
            ("outputTransform", wf.BRAINSConstellationDetector.lzout.outputTransform),
        ]
    )
    
    with pydra.Submitter(plugin="cf") as sub:
        sub(wf)
    result = wf.result()
    print(result)
