import pydra
from pathlib import Path
from shutil import copyfile
import json

with open('config_experimental.json') as f:
    experiment_configuration = json.load(f)

@pydra.mark.task
def append_filename(filename="", before_str="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    print(f"new: {new_filename}")
    return new_filename

@pydra.mark.task
def get_self(x):
    return x

@pydra.mark.task
def get_input_field(input_dict: dict, field):
    print(input_dict)
    print(f'returning: {input_dict[field]}')
    return input_dict[field]

def make_bcd_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    # from .sem_tasks.segmentation.specialized import BRAINSConstellationDetector
    from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

    bcd_workflow = pydra.Workflow(name="preliminary_workflow4", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)

    bcd_workflow.add(get_input_field(name="get_t1", input_dict=bcd_workflow.lzin.input_data, field="t1"))


    # Set the filenames for the output of the BRAINSConstellationDetector task
    bcd_workflow.add(append_filename(name="outputLandmarksInInputSpace", filename=bcd_workflow.get_t1.lzout.out, append_str="_BCD_Original", extension=".fcsv"))
    bcd_workflow.add(append_filename(name="outputResampledVolume", filename=bcd_workflow.get_t1.lzout.out, append_str="_BCD_ACPC", extension=".nii.gz"))
    bcd_workflow.add(append_filename(name="outputTransform", filename=bcd_workflow.get_t1.lzout.out, append_str="_BCD_Original2ACPC_transform", extension=".h5"))
    bcd_workflow.add(append_filename(name="outputLandmarksInACPCAlignedSpace", filename=bcd_workflow.get_t1.lzout.out, append_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
    bcd_workflow.add(append_filename(name="writeBranded2DImage", filename=bcd_workflow.get_t1.lzout.out, append_str="_BCD_Branded2DQCimage", extension=".png"))

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration['BRAINSConstellationDetector']['executable']).get_task()
    bcd_task.inputs.inputVolume = bcd_workflow.get_t1.lzout.out
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

    resample_workflow = pydra.Workflow(name="resample_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    # Get the t1 image for the subject in the input data
    resample_workflow.add(get_input_field(name="get_t1", input_dict=resample_workflow.lzin.input_data, field="t1"))
    # Set the filename of the output of Resample
    resample_workflow.add(append_filename(name="resampledOutputVolume", filename=resample_workflow.get_t1.lzout.out, append_str="_resampled", extension=".nii.gz"))

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration['BRAINSResample']['executable']).get_task()
    resample_task.inputs.inputVolume = resample_workflow.get_t1.lzout.out
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

    roi_workflow = pydra.Workflow(name="roi_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    roi_workflow.add(get_input_field(name="get_t1", input_dict=roi_workflow.lzin.input_data, field="t1"))
    roi_workflow.add(append_filename(name="roiOutputVolume", filename=roi_workflow.get_t1.lzout.out, before_str="Cropped_", append_str="_Aligned", extension=".txt"))

    roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration['BRAINSROIAuto']['executable']).get_task()
    roi_task.inputs.inputVolume = roi_workflow.get_t1.lzout.out
    roi_task.inputs.ROIAutoDilateSize = experiment_configuration['BRAINSROIAuto']['ROIAutoDilateSize']
    roi_task.inputs.cropOutput = experiment_configuration['BRAINSROIAuto']['cropOutput']
    roi_task.inputs.outputVolume = roi_workflow.roiOutputVolume.lzout.out

    roi_workflow.add(roi_task)
    roi_workflow.set_output([("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume)])

    return roi_workflow

def make_LandmarkInitializer_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.utilities.brains import BRAINSLandmarkInitializer

    landmark_initializer_workflow = pydra.Workflow(name="landmark_initializer_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    landmark_initializer_workflow.add(get_input_field(name="get_movingLandmark", input_dict=landmark_initializer_workflow.lzin.input_data, field="inputMovingLandmarkFilename"))
    landmark_initializer_workflow.add(append_filename(name="outputTransformFilename", filename="landmarkInitializer_subject_to_atlas_transform", extension=".h5"))

    landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration['BRAINSLandmarkInitializer']['executable']).get_task()
    landmark_initializer_task.inputs.inputFixedLandmarkFilename = experiment_configuration['BRAINSLandmarkInitializer']['inputFixedLandmarkFilename']
    landmark_initializer_task.inputs.inputMovingLandmarkFilename = landmark_initializer_workflow.get_movingLandmark.lzout.out
    landmark_initializer_task.inputs.inputWeightFilename = experiment_configuration['BRAINSLandmarkInitializer']['inputWeightFilename']
    landmark_initializer_task.inputs.outputTransformFilename = landmark_initializer_workflow.outputTransformFilename.lzout.out

    landmark_initializer_workflow.add(landmark_initializer_task)
    landmark_initializer_workflow.set_output(([("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename)]))

    return landmark_initializer_workflow

def make_ABC_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSABC

    abc_workflow = pydra.Workflow(name="abc_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    abc_workflow.add(get_input_field(name="get_inputVolumes", input_dict=abc_workflow.lzin.input_data, field="t1"))
    abc_workflow.add(append_filename(name="outputVolumes", filename=abc_workflow.get_inputVolumes.lzout.out, append_str="_corrected", extension=".txt"))

    abc_task = BRAINSABC(name="BRAINSABC", executable=experiment_configuration['BRAINSABC']['executable']).get_task()
    abc_task.inputs.atlasDefinition = experiment_configuration['BRAINSABC']['atlasDefinition']
    abc_task.inputs.atlasToSubjectTransform = experiment_configuration['BRAINSABC']['atlasToSubjectTransform']
    abc_task.inputs.atlasToSubjectTransformType = experiment_configuration['BRAINSABC']['atlasToSubjectTransformType']
    abc_task.inputs.debuglevel = experiment_configuration['BRAINSABC']['debuglevel']
    abc_task.inputs.filterIteration = experiment_configuration['BRAINSABC']['filterIteration']
    abc_task.inputs.filterMethod = experiment_configuration['BRAINSABC']['filterMethod']
    abc_task.inputs.inputVolumeTypes = experiment_configuration['BRAINSABC']['inputVolumeTypes']
    abc_task.inputs.inputVolumes = abc_workflow.get_inputVolumes.lzout.out
    abc_task.inputs.interpolationMode = experiment_configuration['BRAINSABC']['interpolationMode']
    abc_task.inputs.maxBiasDegree = experiment_configuration['BRAINSABC']['maxBiasDegree']
    abc_task.inputs.maxIterations = experiment_configuration['BRAINSABC']['maxIterations']
    abc_task.inputs.outputDir = experiment_configuration['BRAINSABC']['outputDir']
    abc_task.inputs.outputDirtyLabels = experiment_configuration['BRAINSABC']['outputDirtyLabels']
    abc_task.inputs.outputFormat = experiment_configuration['BRAINSABC']['outputFormat']
    abc_task.inputs.outputLabels = experiment_configuration['BRAINSABC']['outputLabels']
    abc_task.inputs.outputVolumes = abc_workflow.outputVolumes.lzout.out

    abc_workflow.add(abc_task)
    abc_workflow.set_output([("outputVolumes", abc_workflow.BRAINSABC.lzout.outputVolumes)])

    return abc_workflow

def make_CreateLabelMapFromProbabilityMaps_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSCreateLabelMapFromProbabilityMaps

    label_map_workflow = pydra.Workflow(name="label_map_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)

    label_map_task = BRAINSCreateLabelMapFromProbabilityMaps(name="BRAINSCreateLabelMapFromProbabilityMaps", executable=experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['executable']).get_task()
    label_map_task.inputs.cleanLabelVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['cleanLabelVolume']
    label_map_task.inputs.dirtyLabelVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['dirtyLabelVolume']
    label_map_task.inputs.foregroundPriors = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['foregroundPriors']
    label_map_task.inputs.inputProbabilityVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['inputProbabilityVolume']
    label_map_task.inputs.nonAirRegionMask = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['nonAirRegionMask']
    label_map_task.inputs.priorLabelCodes = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['priorLabelCodes']

    label_map_workflow.add(label_map_task)
    label_map_workflow.set_output([("cleanLabelVolume", label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.cleanLabelVolume),
                                   ("dirtyLabelVolume", label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.dirtyLabelVolume)])
    return label_map_workflow

def make_antsRegistration_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.ants import ANTSRegistration

    antsRegistration_workflow = pydra.Workflow(name="antsRegistration_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    # antsRegistration_workflow.add(get_input_field(name="get_output", input_dict=experiment_configuration["ANTSRegistration"], field="output"))
    # antsRegistration_workflow.add(append_filename(name="outputVolumes", filename=antsRegistration_workflow.get_output.lzout.out))


    antsRegistration_task = ANTSRegistration(name="ANTSRegistration", executable=experiment_configuration['ANTSRegistration']['executable']).get_task()
    # antsRegistration_task.inputs.verbose = experiment_configuration['ANTSRegistration']['verbose']
    # antsRegistration_task.inputs.collapse_output_transforms = experiment_configuration['ANTSRegistration']['collapse-output-transforms']
    # antsRegistration_task.inputs.dimensionality = experiment_configuration['ANTSRegistration']['dimensionality']
    # antsRegistration_task.inputs.float = experiment_configuration['ANTSRegistration']['float']
    # antsRegistration_task.inputs.initial_moving_transform = experiment_configuration['ANTSRegistration']['initial-moving-transform']
    # antsRegistration_task.inputs.initialize_transforms_per_stage = experiment_configuration['ANTSRegistration']['initialize-transforms-per-stage']
    # antsRegistration_task.inputs.interpolation = experiment_configuration['ANTSRegistration']['interpolation']
    antsRegistration_task.inputs.output = ["test1","test2","test3"] #experiment_configuration['ANTSRegistration']['output'] #antsRegistration_workflow.outputVolumes.lzout.out # # # # [ "AtlasToSubjectPreBABC_Rigid", "atlas2subjectRigid.nii.gz", "subject2atlasRigid.nii.gz"] ,

    # antsRegistration_task.inputs.transform = experiment_configuration['ANTSRegistration']['transform']
    # antsRegistration_task.inputs.metric = experiment_configuration['ANTSRegistration']['metric']
    # antsRegistration_task.inputs.convergence = experiment_configuration['ANTSRegistration']['convergence']
    # antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration['ANTSRegistration']['smoothing-sigmas']
    # antsRegistration_task.inputs.shrink_factors = experiment_configuration['ANTSRegistration']['shrink-factors']
    # antsRegistration_task.inputs.use_estimate_learning_rate_once = experiment_configuration['ANTSRegistration']['use-estimate-learning-rate-once']
    # antsRegistration_task.inputs.use_histogram_matching = experiment_configuration['ANTSRegistration']['use-histogram-matching']
    # antsRegistration_task.inputs.winsorize_image_intensities = experiment_configuration['ANTSRegistration']['winsorize-image-intensities']
    # antsRegistration_task.inputs.write_composite_transform = experiment_configuration['ANTSRegistration']['write-composite-transform']

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([("output", antsRegistration_workflow.ANTSRegistration.lzout.output)])

    print(antsRegistration_task.cmdline)
    return antsRegistration_workflow

@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    # print(list(processed_dict.values()))
    # print(len(list(processed_dict.values())))
    return list(processed_dict.values())

# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    print(cache_path)
    if len(cache_path) > 1:
        for path in cache_path:
            copyfile(path, Path(output_dir) / Path(path).name)
            out_path = Path(output_dir) / Path(path).name
            copyfile(path, out_path)
        return path
    else:
        copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
        out_path = Path(output_dir) / Path(cache_path).name
        copyfile(cache_path, out_path)
        return cache_path

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
source_node = pydra.Workflow(name="source_node", input_spec=["input_data"])
source_node.inputs.input_data = experiment_configuration["input_data"]
source_node.split("input_data")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

# Get the processing workflow defined in a separate function
# preliminary_workflow4 = make_bcd_workflow(source_node)
# preliminary_workflow4 = make_resample_workflow(source_node)
# preliminary_workflow4 = make_ROIAuto_workflow(source_node)
# preliminary_workflow4 = make_LandmarkInitializer_workflow(source_node)
# preliminary_workflow4 = make_ABC_workflow(source_node)
# preliminary_workflow4 = make_CreateLabelMapFromProbabilityMaps_workflow(source_node)
preliminary_workflow4 = make_antsRegistration_workflow(source_node)

# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files'], processed_files=preliminary_workflow4.lzout.all_)
sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
# sink_node.set_output([("output_files", sink_node.get_processed_outputs.lzout.out)])
sink_node.add(copy_from_cache(name="copy_from_cache", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out).split("cache_path"))
sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])


# Add the processing workflow and sink_node to the source_node to be included in running the pipeline
source_node.add(preliminary_workflow4)

source_node.add(sink_node)

# Set the output of the source node to the same as the output of the sink_node
# source_node.set_output([("output_files", source_node.sink_node.lzout.output_files),])
source_node.set_output([("output_files", source_node.antsRegistration_workflow.lzout.output),])


# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)