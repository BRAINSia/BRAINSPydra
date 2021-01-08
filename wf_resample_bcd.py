import pydra
from pathlib import Path
import nest_asyncio
import time
from shutil import copyfile
import json
import os
import glob
from configparser import ConfigParser

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
def get_subject(subject_list):
    return subject_list

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    print(f"filename: {filename}")
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename 

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    print(f"cache_path: {cache_path}")
    print(f"output_dir: {output_dir}")
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path

if __name__ == "__main__":
    nest_asyncio.apply()
    config = ConfigParser()
    config.read("config.ini")

    # Set the location of the cache and clear its contents before running 
    output_dir = config["OUTPUT"]["output_dir"]
    cache_dir = config["OUTPUT"]["cache_dir"]
    os.system(f'rm -rf {cache_dir}/*') # Only deleting cache now as the pipeline is being developed and tested

    subject_t1s = []
    with open(config["SOURCE"]["subject_jsons_file"]) as json_file:
        data = json.load(json_file)
        for subject in data:
            subject_t1s.append(data[subject]["t1"]) 

    # Create the outer workflow that interfaces witht the source and sink nodes
    outer = pydra.Workflow(name="outer", input_spec=["t1_list"], t1_list=subject_t1s, cache_dir=cache_dir)
 
    # Get the subject data listed in the subject_jsons.json file 
    source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"],)
    source_node.split("t1_list", t1_list=outer.lzin.t1_list)
    source_node.add(get_subject(name="get_subject", subject_list=source_node.lzin.t1_list))    
    source_node.set_output([("t1", source_node.get_subject.lzout.out)])

    # Define the workflow
    wf = pydra.Workflow(name="wf",input_spec=["t1"], t1=source_node.lzout.t1)
    #                              output_spec # outputs from the set_output, autogenerated paths of cache)
    # Set the filenames of the outputs of BCD
    wf.add(append_filename(name="outputLandmarksInInputSpace",       filename=wf.lzin.t1, append_str="_BCD_Original",                extension=".fcsv"))
    wf.add(append_filename(name="outputResampledVolume",             filename=wf.lzin.t1, append_str="_BCD_ACPC",                    extension=".nii.gz"))
    wf.add(append_filename(name="outputTransform",                   filename=wf.lzin.t1, append_str="_BCD_Original2ACPC_transform", extension=".h5"))
    wf.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=wf.lzin.t1, append_str="_BCD_ACPC_Landmarks",          extension=".fcsv"))
    wf.add(append_filename(name="writeBranded2DImage",               filename=wf.lzin.t1, append_str="_BCD_Branded2DQCimage",        extension=".png"))

    # Set the inputs of BCD
    bcd = BRAINSConstellationDetector("BRAINSConstellationDetector").get_task()
    bcd.inputs.inputVolume =                       wf.lzin.t1
    bcd.inputs.inputTemplateModel =                config["BCD"]["inputTemplateModel"]
    bcd.inputs.LLSModel =                          config["BCD"]["LLSModel"]
    bcd.inputs.atlasLandmarkWeights =              config["BCD"]["atlasLandmarkWeights"]
    bcd.inputs.atlasLandmarks =                    config["BCD"]["atlasLandmarks"]
    bcd.inputs.houghEyeDetectorMode =              config["BCD"]["houghEyeDetectorMode"]
    bcd.inputs.acLowerBound =                      config["BCD"]["acLowerBound"]
    bcd.inputs.interpolationMode =                 config["BCD"]["interpolationMode"]
    bcd.inputs.outputLandmarksInInputSpace =       wf.outputLandmarksInInputSpace.lzout.out 
    bcd.inputs.outputResampledVolume =             wf.outputResampledVolume.lzout.out 
    bcd.inputs.outputTransform =                   wf.outputTransform.lzout.out 
    bcd.inputs.outputLandmarksInACPCAlignedSpace = wf.outputLandmarksInACPCAlignedSpace.lzout.out 
    bcd.inputs.writeBranded2DImage =               wf.writeBranded2DImage.lzout.out 
    wf.add(bcd)

    # Set the filename of the output of Resample
    wf.add(append_filename(name="resampledOutputVolume", filename=wf.lzin.t1, append_str="_resampled", extension=".nii.gz"))
 
    # Set the inputs of Resample
    resample = BRAINSResample("BRAINSResample").get_task()
    resample.inputs.inputVolume =       wf.BRAINSConstellationDetector.lzout.outputResampledVolume
    resample.inputs.inputVolume = wf.lzin.t1
    resample.inputs.interpolationMode = config["RESAMPLE"]["interpolationMode"]
    resample.inputs.pixelType =         config["RESAMPLE"]["pixelType"]        
    resample.inputs.referenceVolume =   wf.BRAINSConstellationDetector.lzout.outputResampledVolume 
    resample.inputs.warpTransform =     wf.BRAINSConstellationDetector.lzout.outputTransform 
    resample.inputs.outputVolume =      wf.resampledOutputVolume.lzout.out 
    wf.add(resample)
    
    # Set the outputs of the entire workflow
    wf.set_output(
        [
            ("outputLandmarksInInputSpace",       wf.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume",             wf.BRAINSConstellationDetector.lzout.outputResampledVolume),
            ("outputTransform",                   wf.BRAINSConstellationDetector.lzout.outputTransform),
            ("outputLandmarksInACPCAlignedSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
            ("writeBranded2DImage",               wf.BRAINSConstellationDetector.lzout.writeBranded2DImage),
            ("outputVolume",                      wf.BRAINSResample.lzout.outputVolume),
        ]
    )

    sink_node = pydra.Workflow(name="sink_node", input_spec=["outputLandmarksInInputSpace", "outputResampledVolume", "outputTransform", "outputLandmarksInACPCAlignedSpace", "writeBranded2DImage", "outputVolume"])

    sink_node.inputs.outputLandmarksInInputSpace      =wf.lzout.outputLandmarksInInputSpace  
    sink_node.inputs.outputResampledVolume            =wf.lzout.outputLandmarksInInputSpace
    sink_node.inputs.outputTransform                  =wf.lzout.outputTransform
    sink_node.inputs.outputLandmarksInACPCAlignedSpace=wf.lzout.outputLandmarksInACPCAlignedSpace
    sink_node.inputs.writeBranded2DImage              =wf.lzout.writeBranded2DImage
    sink_node.inputs.outputVolume                     =wf.lzout.outputVolume


    # Copy the files from the cache to the output directory so the resulting files can be accessed
    sink_node.add(copy_from_cache(name="outputLandmarksInInputSpace",       cache_path=sink_node.lzin.outputLandmarksInInputSpace,       output_dir=output_dir))
    sink_node.add(copy_from_cache(name="outputResampledVolume",             cache_path=sink_node.lzin.outputResampledVolume,             output_dir=output_dir))
    sink_node.add(copy_from_cache(name="outputTransform",                   cache_path=sink_node.lzin.outputTransform,                   output_dir=output_dir))
    sink_node.add(copy_from_cache(name="outputLandmarksInACPCAlignedSpace", cache_path=sink_node.lzin.outputLandmarksInACPCAlignedSpace, output_dir=output_dir))
    sink_node.add(copy_from_cache(name="writeBranded2DImage",               cache_path=sink_node.lzin.writeBranded2DImage,               output_dir=output_dir))
    sink_node.add(copy_from_cache(name="outputVolume",                      cache_path=sink_node.lzin.outputVolume,                                   output_dir=output_dir))
 
    sink_node.set_output(
        [
            ("outputLandmarksInInputSpace",       sink_node.outputLandmarksInInputSpace.lzout.out),
            ("outputResampledVolume",             sink_node.outputResampledVolume.lzout.out),
            ("outputTransform",                   sink_node.outputTransform.lzout.out),
            ("outputLandmarksInACPCAlignedSpace", sink_node.outputLandmarksInACPCAlignedSpace.lzout.out),
            ("writeBranded2DImage",               sink_node.writeBranded2DImage.lzout.out),
            ("outputVolume",                      sink_node.outputVolume.lzout.out)
        ]
    )   

    outer.add(source_node)
    outer.add(wf)
    outer.add(sink_node)
    outer.set_output(
        [
            ("outputLandmarksInInputSpace",       outer.sink_node.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume",             outer.sink_node.lzout.outputResampledVolume),
            ("outputTransform",                   outer.sink_node.lzout.outputTransform),
            ("outputLandmarksInACPCAlignedSpace", outer.sink_node.lzout.outputLandmarksInACPCAlignedSpace),
            ("writeBranded2DImage",               outer.sink_node.lzout.writeBranded2DImage),
            ("outputVolume",                      outer.sink_node.lzout.outputVolume)
        ]
    )        
    
    t0 = time.time() 
    # Run the pipeline
    with pydra.Submitter(plugin="cf") as sub:
        sub(outer)
    result = outer.result()
    print(result)
    print(f"total time: {time.time() - t0}")
