import pydra
from pathlib import Path
from shutil import copyfile
import json

with open('config_experimental.json') as f:
    experiment_configuration = json.load(f)

@pydra.mark.task
def append_filename(filename="", before_str="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename

def make_bcd_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    # from .sem_tasks.segmentation.specialized import BRAINSConstellationDetector
    from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

    bcd_workflow = pydra.Workflow(name="preliminary_workflow4", input_spec=["t1"], t1=my_source_node.lzin.t1_list)
    # Set the filenames for the output of the BRAINSConstellationDetector task
    bcd_workflow.add(append_filename(name="outputLandmarksInInputSpace", filename=bcd_workflow.lzin.t1, append_str="_BCD_Original", extension=".fcsv"))
    bcd_workflow.add(append_filename(name="outputResampledVolume", filename=bcd_workflow.lzin.t1, append_str="_BCD_ACPC", extension=".nii.gz"))
    bcd_workflow.add(append_filename(name="outputTransform", filename=bcd_workflow.lzin.t1, append_str="_BCD_Original2ACPC_transform", extension=".h5"))
    bcd_workflow.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=bcd_workflow.lzin.t1, append_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
    bcd_workflow.add(append_filename(name="writeBranded2DImage", filename=bcd_workflow.lzin.t1, append_str="_BCD_Branded2DQCimage", extension=".png"))

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration['BRAINSConstellationDetector']['executable']).get_task()
    bcd_task.inputs.inputVolume = bcd_workflow.lzin.t1
    bcd_task.inputs.inputTemplateModel = experiment_configuration['BRAINSConstellationDetector']['inputTemplateModel']
    bcd_task.inputs.LLSModel = experiment_configuration['BRAINSConstellationDetector']['LLSModel']
    bcd_task.inputs.atlasLandmarkWeights = experiment_configuration['BRAINSConstellationDetector']['atlasLandmarkWeights']
    bcd_task.inputs.atlasLandmarks = experiment_configuration['BRAINSConstellationDetector']['atlasLandmarks']
    bcd_task.inputs.houghEyeDetectorMode = experiment_configuration['BRAINSConstellationDetector']['houghEyeDetectorMode']
    bcd_task.inputs.acLowerBound = experiment_configuration['BRAINSConstellationDetector']['acLowerBound']
    bcd_task.inputs.interpolationMode = experiment_configuration['BRAINSConstellationDetector']['interpolationMode']
    bcd_task.inputs.outputLandmarksInInputSpace = bcd_workflow.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume = bcd_workflow.outputResampledVolume.lzout.out
    bcd_task.inputs.outputTransform = bcd_workflow.outputTransform.lzout.out
    bcd_task.inputs.outputLandmarksInACPCAlignedSpace = bcd_workflow.outputLandmarksInACPCAlignedSpace.lzout.out
    bcd_task.inputs.writeBranded2DImage = bcd_workflow.writeBranded2DImage.lzout.out
    bcd_workflow.add(bcd_task)

    # Set the outputs of the processing node and the source node so they are output to the sink node
    bcd_workflow.set_output([("outputLandmarksInInputSpace",
                                       bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
                                      ("outputResampledVolume",
                                       bcd_workflow.BRAINSConstellationDetector.lzout.outputResampledVolume),
                                      ("outputTransform",
                                       bcd_workflow.BRAINSConstellationDetector.lzout.outputTransform),
                                      ("outputLandmarksInACPCAlignedSpace",
                                       bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
                                      ("writeBranded2DImage",
                                       bcd_workflow.BRAINSConstellationDetector.lzout.writeBranded2DImage)])
    return bcd_workflow

def make_resample_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample

    resample_workflow = pydra.Workflow(name="resample_workflow", input_spec=["t1"], t1=my_source_node.lzin.t1_list)

    # Set the filename of the output of Resample
    resample_workflow.add(append_filename(name="resampledOutputVolume", filename=resample_workflow.lzin.t1, append_str="_resampled", extension=".nii.gz"))

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration['BRAINSResample']['executable']).get_task()
    resample_task.inputs.inputVolume = resample_workflow.lzin.t1
    resample_task.inputs.interpolationMode = experiment_configuration["BRAINSResample"]["interpolationMode"]
    resample_task.inputs.pixelType = experiment_configuration["BRAINSResample"]["pixelType"]
    resample_task.inputs.referenceVolume = experiment_configuration["BRAINSResample"]["referenceVolume"]
    resample_task.inputs.warpTransform = experiment_configuration["BRAINSResample"]["warpTransform"]
    resample_task.inputs.outputVolume = resample_workflow.resampledOutputVolume.lzout.out
    resample_workflow.add(resample_task)

    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])
    return resample_workflow

def make_ROIAuto_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSROIAuto

    roi_workflow = pydra.Workflow(name="roi_workflow", input_spec=["t1"], t1=my_source_node.lzin.t1_list)

    roi_workflow.add(append_filename(name="roiOutputVolume", filename=roi_workflow.lzin.t1, before_str="Cropped_", append_str="_Aligned", extension=".nii.gz"))

    roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration['BRAINSROIAuto']['executable']).get_task()
    roi_task.inputs.inputVolume = roi_workflow.lzin.t1
    roi_task.inputs.ROIAutoDilateSize = experiment_configuration['BRAINSROIAuto']['ROIAutoDilateSize']
    roi_task.inputs.cropOutput = experiment_configuration['BRAINSROIAuto']['cropOutput']
    roi_task.inputs.outputVolume = roi_workflow.roiOutputVolume.lzout.out
    roi_workflow.add(roi_task)

    roi_workflow.set_output([("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume)])
    return roi_workflow

@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    return list(processed_dict.values())

# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.inputs.t1_list = experiment_configuration["t1_list"]
source_node.split("t1_list")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

# Get the processing workflow defined in a separate function
# preliminary_workflow4 = make_bcd_workflow(source_node)
# preliminary_workflow4 = make_resample_workflow(source_node)
preliminary_workflow4 = make_ROIAuto_workflow(source_node)

# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files'], processed_files=preliminary_workflow4.lzout.all_)
sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
sink_node.add(copy_from_cache(name="copy_from_cache", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out).split("cache_path"))
sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])

# Add the processing workflow and sink_node to the source_node to be included in running the pipeline
source_node.add(preliminary_workflow4)
source_node.add(sink_node)

# Set the output of the source node to the same as the output of the sink_node
source_node.set_output([("output_files", source_node.sink_node.lzout.output_files),])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)