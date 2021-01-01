import pydra
from pathlib import Path
import nest_asyncio
import time
from shutil import copyfile
import json
import os
import glob

import attr
from nipype.interfaces.base import (
    Directory,
    File,
)
from pydra import ShellCommandTask
from pydra.engine.specs import SpecInfo, ShellSpec

from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename 

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)

if __name__ == "__main__":
    # Set the location of the cache and clear its contents before running 
    output_dir = "/localscratch/Users/cjohnson30/output_dir"
    os.system(f'rm -rf {output_dir}/*')
     
    # Get the subject data listed in the subject_jsons.json file 
    subject_t1s = []
    subject_templateModels = []
    subject_llsModels = []
    subject_landmarkWeights = []
    subject_landmarks = []
    with open('/localscratch/Users/cjohnson30/BRAINSPydra/subject_jsons.json') as json_file:
        data = json.load(json_file)
        for subject in data:
            subject_t1s.append(data[subject]["t1"])
            subject_templateModels.append(data[subject]["templateModel"])
            subject_llsModels.append(data[subject]["llsModel"])
            subject_landmarkWeights.append(data[subject]["landmarkWeights"])
            subject_landmarks.append(data[subject]["landmarks"])
   
 
    nest_asyncio.apply()

    # Create the inputs to the workflow
    wf = pydra.Workflow(name="wf", 
                        input_spec=["t1", "templateModel", "llsModel", "landmarkWeights", "landmarks", "output_dir"], 
                        cache_dir=output_dir)

    wf.inputs.t1 =                   subject_t1s
    wf.inputs.templateModel =        subject_templateModels
    wf.inputs.llsModel =             subject_llsModels
    wf.inputs.landmarkWeights =      subject_landmarkWeights
    wf.inputs.landmarks =            subject_landmarks
    wf.split(("t1", "templateModel", "llsModel", "landmarkWeights", "landmarks"))
 
    # Set the filenames of the outputs of BCD
    wf.add(append_filename(name="outputLandmarksInInputSpaceName",
                           filename=wf.lzin.t1,
                           append_str="_BCD_Original",
                           extension=".fcsv"))
    wf.add(append_filename(name="outputResampledVolumeName",
                           filename=wf.lzin.t1,append_str="_BCD_ACPC",
                           extension=".nii.gz"))
    wf.add(append_filename(name="outputTransformName",
                           filename=wf.lzin.t1,
                           append_str="_BCD_Original2ACPC_transform",
                           extension=".h5"))
    wf.add(append_filename(name="outputLandmarksInACPCAlignedSpaceName",
                           filename=wf.lzin.t1,
                           append_str="_BCD_ACPC_Landmarks",
                           extension=".fcsv"))
    wf.add(append_filename(name="writeBranded2DImageName",
                           filename=wf.lzin.t1,
                           append_str="_BCD_Branded2DQCimage",       
                           extension=".png"))

    # Set the inputs of BCD
    bcd = BRAINSConstellationDetector("BRAINSConstellationDetector").get_task()
    bcd.inputs.inputVolume =                       wf.lzin.t1
    bcd.inputs.inputTemplateModel =                wf.lzin.templateModel
    bcd.inputs.LLSModel =                          wf.lzin.llsModel
    bcd.inputs.atlasLandmarkWeights =              wf.lzin.landmarkWeights 
    bcd.inputs.atlasLandmarks =                    wf.lzin.landmarks
    bcd.inputs.houghEyeDetectorMode =              1
    bcd.inputs.acLowerBound =                      80.000000
    bcd.inputs.interpolationMode =                 "Linear"
    bcd.inputs.outputLandmarksInInputSpace =       wf.outputLandmarksInInputSpaceName.lzout.out 
    bcd.inputs.outputResampledVolume =             wf.outputResampledVolumeName.lzout.out 
    bcd.inputs.outputTransform =                   wf.outputTransformName.lzout.out 
    bcd.inputs.outputLandmarksInACPCAlignedSpace = wf.outputLandmarksInACPCAlignedSpaceName.lzout.out 
    bcd.inputs.writeBranded2DImage =               wf.writeBranded2DImageName.lzout.out 
    wf.add(bcd)

    # Set the filename of the output of Resample
    wf.add(append_filename(name="resampledOutputVolumeName", filename=wf.lzin.t1, append_str="_resampled", extension=".nii.gz"))
 
    # Set the inputs of Resample
    resample = BRAINSResample("BRAINSResample").get_task()
    resample.inputs.inputVolume =       wf.BRAINSConstellationDetector.lzout.outputResampledVolume
    resample.inputs.interpolationMode = "Linear"
    resample.inputs.pixelType =         "binary"
    resample.inputs.referenceVolume =   "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz" 
    resample.inputs.warpTransform =     "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5"
    resample.inputs.outputVolume =      wf.resampledOutputVolumeName.lzout.out 
    wf.add(resample)

    # Set the outputs of the entire workflow
    wf.set_output(
        [
            ("outputLandmarksInInputSpace",       wf.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume",             wf.BRAINSConstellationDetector.lzout.outputResampledVolume),
            ("outputTransform",                   wf.BRAINSConstellationDetector.lzout.outputTransform),
            ("outputLandmarksInACPCAlignedSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
            ("writeBranded2DImage",               wf.BRAINSConstellationDetector.lzout.writeBranded2DImage),
            ("resampledOutputVolume",             wf.BRAINSResample.lzout.outputVolume),
        ]
    )
    
    t0 = time.time() 
    # Run the pipeline
    with pydra.Submitter(plugin="cf") as sub:
        sub(wf)
    result = wf.result()
    print(result)
    print(f"total time: {time.time() - t0}")
