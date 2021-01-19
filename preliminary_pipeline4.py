
import pydra
import nest_asyncio
from pathlib import Path
from shutil import copyfile
from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path

nest_asyncio.apply()

# Get the list of two files of the pattern subject*.txt images in this directory
input = ["/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/subject1.txt","/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/subject2.txt"]

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow3)
source_node = pydra.Workflow(name="source_node", input_spec=["input"])
preliminary_workflow4 = pydra.Workflow(name="preliminary_workflow4", input_spec=["input"], input=source_node.lzin.input)
source_node.add(preliminary_workflow4)
source_node.split("input") # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)
source_node.inputs.input = input

preliminary_workflow4.add(append_filename(name="outputLandmarksInInputSpace", filename=preliminary_workflow4.lzin.input, appended_str="_BCD_Original", extension=".fcsv"))
preliminary_workflow4.add(append_filename(name="outputResampledVolume", filename=preliminary_workflow4.lzin.input, appended_str="_BCD_ACPC", extension=".nii.gz"))
preliminary_workflow4.add(append_filename(name="outputTransform", filename=preliminary_workflow4.lzin.input, appended_str="_BCD_Original2ACPC_transform", extension=".h5"))
preliminary_workflow4.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=preliminary_workflow4.lzin.input, appended_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
preliminary_workflow4.add(append_filename(name="writeBranded2DImage", filename=preliminary_workflow4.lzin.input, appended_str="_BCD_Branded2DQCimage", extension=".png"))

BCD_task = BRAINSConstellationDetector(name="BCD", executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSConstellationDetector3.sh").get_task()
BCD_task.inputs.inputVolume = preliminary_workflow4.lzin.input
BCD_task.inputs.inputTemplateModel = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/T1_50Lmks.mdl"
BCD_task.inputs.LLSModel = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/LLSModel_50Lmks.h5"
BCD_task.inputs.atlasLandmarkWeights = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_weights_50Lmks.wts"
BCD_task.inputs.atlasLandmarks = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_landmarks_50Lmks.fcsv"
BCD_task.inputs.houghEyeDetectorMode = 1
BCD_task.inputs.acLowerBound = 80.000000
BCD_task.inputs.interpolationMode = "Linear"
BCD_task.inputs.outputLandmarksInInputSpace = preliminary_workflow4.outputLandmarksInInputSpace.lzout.out
BCD_task.inputs.outputResampledVolume = preliminary_workflow4.outputResampledVolume.lzout.out
BCD_task.inputs.outputTransform = preliminary_workflow4.outputTransform.lzout.out
BCD_task.inputs.outputLandmarksInACPCAlignedSpace = preliminary_workflow4.outputLandmarksInACPCAlignedSpace.lzout.out
BCD_task.inputs.writeBranded2DImage = preliminary_workflow4.writeBranded2DImage.lzout.out
preliminary_workflow4.add(BCD_task)

preliminary_workflow4.add(append_filename(name="outputVolume", filename=preliminary_workflow4.BCD.lzout.outputResampledVolume, appended_str="_resampled", extension=".txt"))

RESAMPLE_task = BRAINSResample(name="RESAMPLE", executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSResample3.sh").get_task()
RESAMPLE_task.inputs.inputVolume = preliminary_workflow4.BCD.lzout.outputResampledVolume
RESAMPLE_task.inputs.interpolationMode = "Linear"
RESAMPLE_task.inputs.pixelType = "binary"
RESAMPLE_task.inputs.referenceVolume = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/resample_refs/t1_average_BRAINSABC.nii.gz"
RESAMPLE_task.inputs.warpTransform = preliminary_workflow4.BCD.lzout.outputTransform
RESAMPLE_task.inputs.outputVolume = preliminary_workflow4.outputVolume.lzout.out
preliminary_workflow4.add(RESAMPLE_task)



# Set the outputs of the processing node and the source node so they are output to the sink node
preliminary_workflow4.set_output([("outputLandmarksInInputSpace",             preliminary_workflow4.BCD.lzout.outputLandmarksInInputSpace),
                                  ("outputResampledVolume",             preliminary_workflow4.BCD.lzout.outputResampledVolume),
                                  ("outputTransform",                   preliminary_workflow4.BCD.lzout.outputTransform),
                                  ("outputLandmarksInACPCAlignedSpace", preliminary_workflow4.BCD.lzout.outputLandmarksInACPCAlignedSpace),
                                  ("writeBranded2DImage",               preliminary_workflow4.BCD.lzout.writeBranded2DImage),
                                  ("outputVolume",                      preliminary_workflow4.RESAMPLE.lzout.outputVolume)])
source_node.set_output([("outputLandmarksInInputSpace",       source_node.preliminary_workflow4.lzout.outputLandmarksInInputSpace),
                        ("outputResampledVolume",             source_node.preliminary_workflow4.lzout.outputResampledVolume),
                        ("outputTransform",                   source_node.preliminary_workflow4.lzout.outputTransform),
                        ("outputLandmarksInACPCAlignedSpace", source_node.preliminary_workflow4.lzout.outputLandmarksInACPCAlignedSpace),
                        ("writeBranded2DImage",               source_node.preliminary_workflow4.lzout.writeBranded2DImage),
                        ("outputVolume",                      source_node.preliminary_workflow4.lzout.outputVolume)])

# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"], cache_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/cache_dir")
sink_node.add(source_node)
sink_node.add(copy_from_cache(name="outputLandmarksInInputSpace",       output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputLandmarksInInputSpace))
sink_node.add(copy_from_cache(name="outputResampledVolume",             output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputResampledVolume))
sink_node.add(copy_from_cache(name="outputTransform",                   output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputTransform))
sink_node.add(copy_from_cache(name="outputLandmarksInACPCAlignedSpace", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputLandmarksInACPCAlignedSpace))
sink_node.add(copy_from_cache(name="writeBranded2DImage",               output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.writeBranded2DImage))
sink_node.add(copy_from_cache(name="outputVolume",                      output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputVolume))
sink_node.set_output([("output", sink_node.outputVolume.lzout.out)])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)
