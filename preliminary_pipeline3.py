import pydra
import nest_asyncio
import attr
from pathlib import Path
from shutil import copyfile
from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector


nest_asyncio.apply()

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

# Get the list of two files of the pattern subject*.txt images in this directory
t1_list = []
p = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files")
for t1 in p.glob("subject*.txt"):
    t1_list.append(t1)

# Put the files into the pydra cache and split them into iterable objects
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
preliminary_workflow3 = pydra.Workflow(name="preliminary_workflow3", input_spec=["t1"], t1=source_node.lzin.t1_list)
source_node.add(preliminary_workflow3)
source_node.split("t1_list")
source_node.inputs.t1_list = t1_list

preliminary_workflow3.add(append_filename(name="outputLandmarksInInputSpace", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_Original", extension=".fcsv"))
preliminary_workflow3.add(append_filename(name="outputResampledVolume", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_ACPC", extension=".nii.gz"))
preliminary_workflow3.add(append_filename(name="outputTransform", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_Original2ACPC_transform", extension=".h5"))
preliminary_workflow3.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
preliminary_workflow3.add(append_filename(name="writeBranded2DImage", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_Branded2DQCimage", extension=".png"))


bcd_task = BRAINSConstellationDetector("BRAINSConstellationDetector3").get_task()
bcd_task.inputs.inputVolume =             "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/subject1.txt"#preliminary_workflow3.lzin.t1
bcd_task.inputs.inputTemplateModel =      "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/T1_50Lmks.mdl"
bcd_task.inputs.LLSModel =                "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/LLSModel_50Lmks.h5"
bcd_task.inputs.atlasLandmarkWeights =    "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_weights_50Lmks.wts"
bcd_task.inputs.atlasLandmarks =          "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_landmarks_50Lmks.fcsv"
bcd_task.inputs.houghEyeDetectorMode =    1
bcd_task.inputs.acLowerBound =            80.000000
bcd_task.inputs.interpolationMode =       "Linear"
bcd_task.inputs.outputLandmarksInInputSpace =       preliminary_workflow3.outputLandmarksInInputSpace.lzout.out
bcd_task.inputs.outputResampledVolume =             preliminary_workflow3.outputResampledVolume.lzout.out
bcd_task.inputs.outputTransform =                   preliminary_workflow3.outputTransform.lzout.out
bcd_task.inputs.outputLandmarksInACPCAlignedSpace = preliminary_workflow3.outputLandmarksInACPCAlignedSpace.lzout.out
bcd_task.inputs.writeBranded2DImage =               preliminary_workflow3.writeBranded2DImage.lzout.out
preliminary_workflow3.add(bcd_task)

resampledOutputVolumeTask = append_filename(name="resampledOutputVolume", filename=preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume, append_str="_resampled", extension=".txt", directory="")
preliminary_workflow3.add(resampledOutputVolumeTask)

resample_task = BRAINSResample("BRAINSResample3").get_task()
resample_task.inputs.inputVolume =       preliminary_workflow3.lzin.t1 #preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume
resample_task.inputs.interpolationMode = "Linear"
resample_task.inputs.pixelType =         "binary"
resample_task.inputs.referenceVolume =   "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz"
resample_task.inputs.warpTransform =     "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5" # outputTransform
resample_task.inputs.outputVolume =      preliminary_workflow3.resampledOutputVolume.lzout.out
preliminary_workflow3.add(resample_task)

preliminary_workflow3.set_output([("outputLandmarksInInputSpace",       preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputLandmarksInInputSpace),
                                  ("outputResampledVolume",             preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume),
                                  ("outputTransform",                   preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputTransform),
                                  ("outputLandmarksInACPCAlignedSpace", preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputLandmarksInACPCAlignedSpace),
                                  ("writeBranded2DImage",               preliminary_workflow3.BRAINSConstellationDetector3.lzout.writeBranded2DImage),
                                  ("outputVolume",                      preliminary_workflow3.BRAINSResample3.lzout.outputVolume)])
source_node.set_output([("outputLandmarksInInputSpace",       source_node.preliminary_workflow3.lzout.outputLandmarksInInputSpace),
                        ("outputResampledVolume",             source_node.preliminary_workflow3.lzout.outputResampledVolume),
                        ("outputTransform",                   source_node.preliminary_workflow3.lzout.outputTransform),
                        ("outputLandmarksInACPCAlignedSpace", source_node.preliminary_workflow3.lzout.outputLandmarksInACPCAlignedSpace),
                        ("writeBranded2DImage",               source_node.preliminary_workflow3.lzout.writeBranded2DImage),
                        ("outputVolume",                      source_node.preliminary_workflow3.lzout.outputVolume)])



# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"])
sink_node.add(source_node)
sink_node.add(copy_from_cache(name="outputLandmarksInInputSpace",       output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputLandmarksInInputSpace))
sink_node.add(copy_from_cache(name="outputResampledVolume",             output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputResampledVolume))
sink_node.add(copy_from_cache(name="outputTransform",                   output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputTransform))
sink_node.add(copy_from_cache(name="outputLandmarksInACPCAlignedSpace", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputLandmarksInACPCAlignedSpace))
sink_node.add(copy_from_cache(name="writeBranded2DImage",               output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.writeBranded2DImage))
sink_node.add(copy_from_cache(name="outputVolume",                      output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.outputVolume))
sink_node.set_output([("output", sink_node.outputVolume.lzout.out)])


# # Run the entire workflow
# with pydra.Submitter(plugin="cf") as sub:
#     sub(source_node)
# result=source_node.result()
# print(result)

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)