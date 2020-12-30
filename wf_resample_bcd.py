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

# from resample_cmd import fill_resample
# from bcd_cmd import fill_bcd

if __name__ == "__main__":
    subject1_json = {
        "in": {
            "t1": "/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-066260_ses-21713_run-002_T1w.nii.gz",
            "ref": "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz",
            "transform": "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5",
        },
        "out": {"output_dir": "/localscratch/Users/cjohnson30/output_dir"},
    }

    resample = BRAINSResample("BRAINSResample").get_task()
    bcd = BRAINSConstellationDetector()
    wf = pydra.Workflow(name="wf", input_spec=["t1", "ref", "transform", "output_dir"])
    wf.inputs.t1 = subject1_json["in"]["t1"]
    wf.inputs.ref = subject1_json["in"]["ref"]
    wf.inputs.transform = subject1_json["in"]["transform"]
    wf.inputs.output_dir = subject1_json["out"]["output_dir"]

    resample.inputs.inputVolume = wf.inputs.t1
    resample.inputs.referenceVolume = wf.inputs.ref
    resample.inputs.warpTransform = wf.inputs.transform
    resample.inputs.interpolationMode = "Linear"
    resample.inputs.pixelType = "binary"
    resample.inputs.outputVolume = "sub-066260_ses-21713_run-002_T1w_resampled.nii.gz"

    bcd = BRAINSConstellationDetector("BRAINSConstellationDetector").get_task()
    bcd.inputs.inputVolume = wf.inputs.t1  # wf.BRAINSResample.lzout.outputVolume
    bcd.inputs.inputTemplateModel = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/T1_50Lmks.mdl"
    bcd.inputs.LLSModel = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/LLSModel_50Lmks.h5"
    bcd.inputs.acLowerBound = 80.000000
    bcd.inputs.atlasLandmarkWeights = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_weights_50Lmks.wts"
    bcd.inputs.atlasLandmarks = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/Atlas/20141004_BCD/template_landmarks_50Lmks.fcsv"
    bcd.inputs.houghEyeDetectorMode = 1
    bcd.inputs.interpolationMode = "Linear"
    bcd.inputs.outputLandmarksInInputSpace = f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_Original.fcsv"
    bcd.inputs.outputResampledVolume = f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_ACPC.nii.gz"
    bcd.inputs.outputTransform = f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_Original2ACPC_transform.h5"
    bcd.inputs.outputLandmarksInACPCAlignedSpace = f"{Path(wf.inputs.t1).with_suffix('').with_suffix('').name}_BCD_ACPC_Landmarks.fcsv"

    wf.add(
        bcd
    )  # .split(("inputVolume", "outputLandmarksInACPCAlignedSpace", "outputLandmarksInInputSpace", "outputResampledVolume", "outputTransform")))

    #    wf.set_output([("outVol", wf.BRAINSResample2.lzout.outputVolume)])
    wf.set_output(
        [
            #            ("outVol", wf.BRAINSResample.lzout.outputVolume),
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
