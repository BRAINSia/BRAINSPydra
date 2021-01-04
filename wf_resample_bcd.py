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
    wf1 = pydra.Workflow(name="wf1", 
                        input_spec=["t1", "templateModel", "llsModel", "landmarkWeights", "landmarks", "output_dir"], 
                        cache_dir=output_dir)

    wf1.inputs.t1 =                   subject_t1s
    wf1.inputs.templateModel =        subject_templateModels
    wf1.inputs.llsModel =             subject_llsModels
    wf1.inputs.landmarkWeights =      subject_landmarkWeights
    wf1.inputs.landmarks =            subject_landmarks
    wf1.split(("t1", "templateModel", "llsModel", "landmarkWeights", "landmarks"))
 
    # Set the filenames of the outputs of BCD
    wf1.add(append_filename(name="outputLandmarksInInputSpaceName",
                           filename=wf1.lzin.t1,
                           append_str="_BCD_Original",
                           extension=".fcsv"))
    wf1.add(append_filename(name="outputResampledVolumeName",
                           filename=wf1.lzin.t1,append_str="_BCD_ACPC",
                           extension=".nii.gz"))
    wf1.add(append_filename(name="outputTransformName",
                           filename=wf1.lzin.t1,
                           append_str="_BCD_Original2ACPC_transform",
                           extension=".h5"))
    wf1.add(append_filename(name="outputLandmarksInACPCAlignedSpaceName",
                           filename=wf1.lzin.t1,
                           append_str="_BCD_ACPC_Landmarks",
                           extension=".fcsv"))
    wf1.add(append_filename(name="writeBranded2DImageName",
                           filename=wf1.lzin.t1,
                           append_str="_BCD_Branded2DQCimage",       
                           extension=".png"))

    # Set the inputs of BCD
    bcd = BRAINSConstellationDetector("BRAINSConstellationDetector").get_task()
    bcd.inputs.inputVolume =                       wf1.lzin.t1
    bcd.inputs.inputTemplateModel =                wf1.lzin.templateModel
    bcd.inputs.LLSModel =                          wf1.lzin.llsModel
    bcd.inputs.atlasLandmarkWeights =              wf1.lzin.landmarkWeights 
    bcd.inputs.atlasLandmarks =                    wf1.lzin.landmarks
    bcd.inputs.houghEyeDetectorMode =              1
    bcd.inputs.acLowerBound =                      80.000000
    bcd.inputs.interpolationMode =                 "Linear"
    bcd.inputs.outputLandmarksInInputSpace =       wf1.outputLandmarksInInputSpaceName.lzout.out 
    bcd.inputs.outputResampledVolume =             wf1.outputResampledVolumeName.lzout.out 
    bcd.inputs.outputTransform =                   wf1.outputTransformName.lzout.out 
    bcd.inputs.outputLandmarksInACPCAlignedSpace = wf1.outputLandmarksInACPCAlignedSpaceName.lzout.out 
    bcd.inputs.writeBranded2DImage =               wf1.writeBranded2DImageName.lzout.out 
    wf1.add(bcd)

    # Set the filename of the output of Resample
    wf1.add(append_filename(name="resampledOutputVolumeName", filename=wf1.lzin.t1, append_str="_resampled", extension=".nii.gz"))
 
    # Set the inputs of Resample
    resample = BRAINSResample("BRAINSResample").get_task()
    resample.inputs.inputVolume =       wf1.BRAINSConstellationDetector.lzout.outputResampledVolume
    resample.inputs.interpolationMode = "Linear"
    resample.inputs.pixelType =         "binary"
    resample.inputs.referenceVolume =   "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz" 
    resample.inputs.warpTransform =     "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5"
    resample.inputs.outputVolume =      wf1.resampledOutputVolumeName.lzout.out 
    wf1.add(resample)

    # Set the outputs of the entire workflow
    wf1.set_output(
        [
            ("outputLandmarksInInputSpace",       wf1.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume",             wf1.BRAINSConstellationDetector.lzout.outputResampledVolume),
            ("outputTransform",                   wf1.BRAINSConstellationDetector.lzout.outputTransform),
            ("outputLandmarksInACPCAlignedSpace", wf1.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
            ("writeBranded2DImage",               wf1.BRAINSConstellationDetector.lzout.writeBranded2DImage),
            ("resampledOutputVolume",             wf1.BRAINSResample.lzout.outputVolume),
        ]
    )
   
    wf2 = pydra.Workflow(name="wf2", input_spec=["output_file"])
    wf2.add(wf1)
    wf2.add(copy_from_cache(name="outputLandmarksInInputSpace",
                            cache_path=wf2.wf1.lzout.outputLandmarksInInputSpace,
                            output_dir=output_dir))
#    wf2.add(copy_from_cache(name="outputResampledVolume",
#                            cache_path=wf2.wf1.lzout.outputResampledVolume,
#                            output_dir=output_dir))
    wf2.set_output([("outputLandmarksInInputSpace", wf2.outputLandmarksInInputSpace.lzout.out,)])
#                     "outputResampledVolume", wf2.outputLandmarksInInputSpace.lzout.out)]) 
                           
   
    t0 = time.time() 
    # Run the pipeline
    with pydra.Submitter(plugin="cf") as sub:
        sub(wf2)
    result = wf2.result()
    print(result)
    print(f"total time: {time.time() - t0}")
    
#    with pydra.Submitter(plugin="cf") as sub:
#        sub(wf2)
#    result=wf2.result()
#    print(result)
