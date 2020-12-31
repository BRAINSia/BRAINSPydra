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

if __name__ == "__main__":
    subject1_json = {
        "in": {
            "t1":              "/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-066260_ses-21713_run-002_T1w.nii.gz", 
            "templateModel":   "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl",
            "llsModel":        "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5",
            "landmarkWeights": "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts",
            "landmarks":       "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv",
        },
        "out": {"output_dir": "/localscratch/Users/cjohnson30/output_dir"},
    }
       

    wf = pydra.Workflow(name="wf", input_spec=["t1", "templateModel", "llsModel", "landmarkWeights", "landmarks", "output_dir"], output_spec=["output_dir"])
    wf.inputs.t1 =                   subject1_json["in"]["t1"]                
    wf.inputs.templateModel =        subject1_json["in"]["templateModel"]
    wf.inputs.llsModel =             subject1_json["in"]["llsModel"]
    wf.inputs.landmarkWeights =      subject1_json["in"]["landmarkWeights"]
    wf.inputs.landmarks =            subject1_json["in"]["landmarks"]
    wf.inputs.output_dir =           subject1_json["out"]["output_dir"]  

    bcd = BRAINSConstellationDetector("BRAINSConstellationDetector").get_task()
    bcd.inputs.inputVolume =                       wf.inputs.t1
    bcd.inputs.inputTemplateModel =                wf.inputs.templateModel
    bcd.inputs.LLSModel =                          wf.inputs.llsModel
    bcd.inputs.atlasLandmarkWeights =              wf.inputs.landmarkWeights 
    bcd.inputs.atlasLandmarks =                    wf.inputs.landmarks
    bcd.inputs.houghEyeDetectorMode =              1
    bcd.inputs.acLowerBound =                      80.000000
    bcd.inputs.interpolationMode =                 "Linear"
    bcd.inputs.outputLandmarksInInputSpace =       f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_Original.fcsv"
    bcd.inputs.outputResampledVolume =             f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_ACPC.nii.gz"
    bcd.inputs.outputTransform =                   f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_Original2ACPC_transform.h5"
    bcd.inputs.outputLandmarksInACPCAlignedSpace = f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_ACPC_Landmarks.fcsv"
    bcd.inputs.writeBranded2DImage =               f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_Branded2DQCimage.png"
    wf.add(bcd)
 
    resample = BRAINSResample("BRAINSResample").get_task()
    resample.inputs.inputVolume =                  wf.BRAINSConstellationDetector.lzout.outputResampledVolume
    resample.inputs.referenceVolume =              "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz" 
    resample.inputs.warpTransform =                "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5"
    resample.inputs.interpolationMode =            "Linear"
    resample.inputs.pixelType =                    "binary"
    resample.inputs.outputVolume =                 f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_resampled.nii.gz" 
    wf.add(resample)
 
    wf.set_output(
        [
            ("resampled", wf.BRAINSResample.lzout.outputVolume),
            (
                "outputLandmarksInACPCAlignedSpace",
                wf.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace,
            ),
            (
                "outputLandmarksInInputSpace",
                wf.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace,
            ),
            (
                "outputResampledVolume",
                wf.BRAINSConstellationDetector.lzout.outputResampledVolume,
            ),
            ("outputTransform", wf.BRAINSConstellationDetector.lzout.outputTransform),
        ]
    )

    with pydra.Submitter(plugin="cf") as sub:
        sub(wf)
    result = wf.result()
    print(result)
