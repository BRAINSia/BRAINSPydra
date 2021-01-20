import pydra
import nest_asyncio
from pathlib import Path
from shutil import copyfile
import json
from segmentation.specialized import BRAINSConstellationDetector
from registration import BRAINSResample



@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    return list(processed_dict.values())

@pydra.mark.task
def get_t1(x):
    return x

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename

def make_bcd_workflow(source_node: pydra.Workflow) -> pydra.Workflow:
    with open('config_experimental.json') as f:
        config_experimental_dict = json.load(f)
    preliminary_workflow4 = pydra.Workflow(name="preliminary_workflow4", input_spec=["t1"], t1=source_node.get_t1.lzout.out)
    # preliminary_workflow4.inputs.t1 = source_node.lzin.t1_list
    # Set the filenames for the output of the BRAINSConstellationDetector task
    preliminary_workflow4.add(append_filename(name="outputLandmarksInInputSpace", filename=preliminary_workflow4.lzin.t1, append_str="_BCD_Original", extension=".fcsv"))
    preliminary_workflow4.add(append_filename(name="outputResampledVolume", filename=preliminary_workflow4.lzin.t1, append_str="_BCD_ACPC", extension=".nii.gz"))
    preliminary_workflow4.add(append_filename(name="outputTransform", filename=preliminary_workflow4.lzin.t1, append_str="_BCD_Original2ACPC_transform", extension=".h5"))
    preliminary_workflow4.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=preliminary_workflow4.lzin.t1, append_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
    preliminary_workflow4.add(append_filename(name="writeBranded2DImage", filename=preliminary_workflow4.lzin.t1, append_str="_BCD_Branded2DQCimage", extension=".png"))

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector4", executable=config_experimental_dict['BRAINSConstellationDetector']['executable']).get_task()
    bcd_task.inputs.inputVolume = preliminary_workflow4.lzin.t1
    bcd_task.inputs.inputTemplateModel = config_experimental_dict['BRAINSConstellationDetector']['inputTemplateModel']
    bcd_task.inputs.LLSModel = config_experimental_dict['BRAINSConstellationDetector']['LLSModel']
    bcd_task.inputs.atlasLandmarkWeights = config_experimental_dict['BRAINSConstellationDetector']['atlasLandmarkWeights']
    bcd_task.inputs.atlasLandmarks = config_experimental_dict['BRAINSConstellationDetector']['atlasLandmarks']
    bcd_task.inputs.houghEyeDetectorMode = config_experimental_dict['BRAINSConstellationDetector']['houghEyeDetectorMode']
    bcd_task.inputs.acLowerBound = config_experimental_dict['BRAINSConstellationDetector']['acLowerBound']
    bcd_task.inputs.interpolationMode = config_experimental_dict['BRAINSConstellationDetector']['interpolationMode']
    bcd_task.inputs.outputLandmarksInInputSpace = preliminary_workflow4.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume = preliminary_workflow4.outputResampledVolume.lzout.out
    bcd_task.inputs.outputTransform = preliminary_workflow4.outputTransform.lzout.out
    bcd_task.inputs.outputLandmarksInACPCAlignedSpace = preliminary_workflow4.outputLandmarksInACPCAlignedSpace.lzout.out
    bcd_task.inputs.writeBranded2DImage = preliminary_workflow4.writeBranded2DImage.lzout.out
    preliminary_workflow4.add(bcd_task)

    # Set the outputs of the processing node and the source node so they are output to the sink node
    preliminary_workflow4.set_output([("outputLandmarksInInputSpace",
                                       preliminary_workflow4.BRAINSConstellationDetector4.lzout.outputLandmarksInInputSpace),
                                      ("outputResampledVolume",
                                       preliminary_workflow4.BRAINSConstellationDetector4.lzout.outputResampledVolume),
                                      ("outputTransform",
                                       preliminary_workflow4.BRAINSConstellationDetector4.lzout.outputTransform),
                                      ("outputLandmarksInACPCAlignedSpace",
                                       preliminary_workflow4.BRAINSConstellationDetector4.lzout.outputLandmarksInACPCAlignedSpace),
                                      ("writeBranded2DImage",
                                       preliminary_workflow4.BRAINSConstellationDetector4.lzout.writeBranded2DImage)])
    return preliminary_workflow4



@pydra.mark.task
def get_subject(sub):
    return sub


# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path


nest_asyncio.apply()


# Get the list of two files of the pattern subject*.txt images in this directory
t1_list = []
p = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files")
for t1 in p.glob("subject*.txt"):
    t1_list.append(t1)

with open('config_experimental.json') as f:
    config_experimental_dict = json.load(f)

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.add(get_t1(name="get_t1", x=source_node.lzin.t1_list))
source_node.inputs.t1_list = t1_list
source_node.split("t1_list")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

preliminary_workflow4 = make_bcd_workflow(source_node)



# The sink converts the cached files to output_dir, a location on the local machine
# sink_node = pydra.Workflow(name="sink_node", input_spec=["outputLandmarksInInputSpace", "outputResampledVolume", "outputTransform", "outputLandmarksInACPCAlignedSpace", "writeBranded2DImage"],
#                            outputLandmarksInInputSpace=preliminary_workflow4.lzout.outputLandmarksInInputSpace,
#                            outputResampledVolume=preliminary_workflow4.lzout.outputResampledVolume,
#                            outputTransform=preliminary_workflow4.lzout.outputTransform,
#                            outputLandmarksInACPCAlignedSpace=preliminary_workflow4.lzout.outputLandmarksInACPCAlignedSpace,
#                            writeBranded2DImage=preliminary_workflow4.lzout.writeBranded2DImage)
sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files'], processed_files=preliminary_workflow4.lzout.all_)
sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
sink_node.add(copy_from_cache(name="copy_from_cache", output_dir=config_experimental_dict['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out).split("cache_path"))
sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])

# sink_node.add(copy_from_cache(name="outputLandmarksInInputSpace", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.lzin.outputLandmarksInInputSpace))
# sink_node.add(copy_from_cache(name="outputResampledVolume", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.lzin.outputResampledVolume))
# sink_node.add(copy_from_cache(name="outputTransform", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.lzin.outputTransform))
# sink_node.add(copy_from_cache(name="outputLandmarksInACPCAlignedSpace", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.lzin.outputLandmarksInACPCAlignedSpace))
# sink_node.add(copy_from_cache(name="writeBranded2DImage", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.lzin.writeBranded2DImage))
# sink_node.set_output([("outputLandmarksInInputSpace", sink_node.outputLandmarksInInputSpace.lzout.out),
#      ("outputResampledVolume", sink_node.outputResampledVolume.lzout.out),
#      ("outputTransform", sink_node.outputTransform.lzout.out),
#      ("outputLandmarksInACPCAlignedSpace", sink_node.outputLandmarksInACPCAlignedSpace.lzout.out),
#      ("writeBranded2DImage", sink_node.writeBranded2DImage.lzout.out)])


source_node.add(preliminary_workflow4)
source_node.add(sink_node)
# sink_node.add(source_node)

source_node.set_output([("output_files", source_node.sink_node.lzout.output_files),])
     # ("outputResampledVolume", source_node.preliminary_workflow4.lzout.outputResampledVolume),
     # ("outputTransform", source_node.preliminary_workflow4.lzout.outputTransform),
     # ("outputLandmarksInACPCAlignedSpace", source_node.preliminary_workflow4.lzout.outputLandmarksInACPCAlignedSpace),
     # ("writeBranded2DImage", source_node.preliminary_workflow4.lzout.writeBranded2DImage)])
# source_node.set_output([("all_workflow_output", source_node.preliminary_workflow4.lzout.all_)])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)
# # Run the entire workflow
# with pydra.Submitter(plugin="cf") as sub:
#     sub(sink_node)
# result = sink_node.result()
# print(result)
