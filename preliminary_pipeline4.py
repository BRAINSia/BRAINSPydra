import pydra
from pathlib import Path
from shutil import copyfile
import json
import argparse

parser = argparse.ArgumentParser(description='Move echo numbers in fmap BIDS data to JSON sidecars')
parser.add_argument('config_experimental', type=str, help='The path to the top level of the BIDS directory')
args = parser.parse_args()

with open(args.config_experimental) as f:
    experiment_configuration = json.load(f)

@pydra.mark.task
def make_output_filename(filename="", before_str="", append_str="", extension="", directory="", unused=""):
    if filename is None:
        return None
    else:
        # If an extension is not specified and the filename has an extension, use the filename's extension
        if extension == "":
            extension = "".join(Path(filename).suffixes)
        new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
        print(new_filename)
        return new_filename


@pydra.mark.task
def get_self(x):
    print(x)
    return x


@pydra.mark.task
def get_input_field(input_dict: dict, field):
    return input_dict[field]

def make_bcd_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    # from .sem_tasks.segmentation.specialized import BRAINSConstellationDetector
    from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

    bcd_workflow = pydra.Workflow(name="preliminary_workflow4", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)

    bcd_workflow.add(get_input_field(name="get_t1", input_dict=bcd_workflow.lzin.input_data, field="t1"))

    # Set the filenames for the output of the BRAINSConstellationDetector task
    # bcd_workflow.add(make_output_filename(name="outputLandmarksInInputSpace", filename=experiment_configuration['BRAINSConstellationDetector']['outputLandmarksInInputSpace']))
    bcd_workflow.add(make_output_filename(name="outputResampledVolume", filename=experiment_configuration['BRAINSConstellationDetector']['outputResampledVolume']))
    # bcd_workflow.add(make_output_filename(name="outputTransform", filename=experiment_configuration['BRAINSConstellationDetector']['outputTransform']))
    bcd_workflow.add(make_output_filename(name="outputLandmarksInACPCAlignedSpace", filename=experiment_configuration['BRAINSConstellationDetector']['outputLandmarksInACPCAlignedSpace']))
    # bcd_workflow.add(make_output_filename(name="writeBranded2DImage", filename=experiment_configuration['BRAINSConstellationDetector']['writeBranded2DImage']))

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration['BRAINSConstellationDetector']['executable']).get_task()
    bcd_task.inputs.inputVolume = bcd_workflow.get_t1.lzout.out
    bcd_task.inputs.LLSModel = experiment_configuration['BRAINSConstellationDetector'].get('LLSModel')
    # bcd_task.inputs.acLowerBound = experiment_configuration['BRAINSConstellationDetector'].get('acLowerBound')
    # bcd_task.inputs.atlasLandmarkWeights = experiment_configuration['BRAINSConstellationDetector'].get('atlasLandmarkWeights')
    # bcd_task.inputs.atlasLandmarks = experiment_configuration['BRAINSConstellationDetector'].get('atlasLandmarks')
    # bcd_task.inputs.houghEyeDetectorMode = experiment_configuration['BRAINSConstellationDetector'].get('houghEyeDetectorMode')
    # bcd_task.inputs.inputLandmarksEMSP = experiment_configuration['BRAINSConstellationDetector'].get('inputLandmarksEMSP')
    # bcd_task.inputs.inputTemplateModel = experiment_configuration['BRAINSConstellationDetector'].get('inputTemplateModel')
    # bcd_task.inputs.interpolationMode = experiment_configuration['BRAINSConstellationDetector'].get('interpolationMode')
    # bcd_task.inputs.outputLandmarksInInputSpace = bcd_workflow.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume = bcd_workflow.outputResampledVolume.lzout.out
    # bcd_task.inputs.outputTransform = bcd_workflow.outputTransform.lzout.out
    # bcd_task.inputs.outputLandmarksInACPCAlignedSpace = bcd_workflow.outputLandmarksInACPCAlignedSpace.lzout.out
    # bcd_task.inputs.writeBranded2DImage = bcd_workflow.writeBranded2DImage.lzout.out
    bcd_workflow.add(bcd_task)

    # Set the outputs of the processing node and the source node so they are output to the sink node
    bcd_workflow.set_output([
        # ("outputLandmarksInInputSpace", bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
        ("outputResampledVolume", bcd_workflow.BRAINSConstellationDetector.lzout.outputResampledVolume),
        # ("outputTransform", bcd_workflow.BRAINSConstellationDetector.lzout.outputTransform),
        # ("outputLandmarksInACPCAlignedSpace", bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
        # ("writeBranded2DImage", bcd_workflow.BRAINSConstellationDetector.lzout.writeBranded2DImage)
    ])
    return bcd_workflow

def make_resample_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample

    resample_workflow = pydra.Workflow(name="resample_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    # Get the t1 image for the subject in the input data
    resample_workflow.add(get_input_field(name="get_t1", input_dict=resample_workflow.lzin.input_data, field="t1"))
    # Set the filename of the output of Resample
    resample_workflow.add(make_output_filename(name="resampledOutputVolume", filename=experiment_configuration["BRAINSResample"]["outputVolume"]))

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration['BRAINSResample']['executable']).get_task()
    resample_task.inputs.inputVolume = resample_workflow.get_t1.lzout.out
    resample_task.inputs.interpolationMode = experiment_configuration["BRAINSResample"].get("interpolationMode")
    resample_task.inputs.pixelType = experiment_configuration["BRAINSResample"].get("pixelType")
    resample_task.inputs.referenceVolume = experiment_configuration["BRAINSResample"].get("referenceVolume")
    resample_task.inputs.warpTransform = experiment_configuration["BRAINSResample"].get("warpTransform")
    resample_task.inputs.outputVolume = resample_workflow.resampledOutputVolume.lzout.out

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_ROIAuto_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSROIAuto

    roi_workflow = pydra.Workflow(name="roi_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    roi_workflow.add(get_input_field(name="get_t1", input_dict=roi_workflow.lzin.input_data, field="t1"))
    roi_workflow.add(make_output_filename(name="outputVolume", filename=experiment_configuration['BRAINSROIAuto'].get('outputVolume')))
    roi_workflow.add(make_output_filename(name="outputROIMaskVolume", filename=experiment_configuration['BRAINSROIAuto'].get('outputROIMaskVolume')))

    roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration['BRAINSROIAuto'].get('executable')).get_task()
    roi_task.inputs.inputVolume = roi_workflow.get_t1.lzout.out
    roi_task.inputs.ROIAutoDilateSize = experiment_configuration['BRAINSROIAuto'].get('ROIAutoDilateSize')
    roi_task.inputs.cropOutput = experiment_configuration['BRAINSROIAuto'].get('cropOutput')
    roi_task.inputs.outputVolume = roi_workflow.outputVolume.lzout.out
    roi_task.inputs.outputROIMaskVolume = roi_workflow.outputROIMaskVolume.lzout.out

    roi_workflow.add(roi_task)
    roi_workflow.set_output([("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume),])

    return roi_workflow

def make_LandmarkInitializer_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.utilities.brains import BRAINSLandmarkInitializer

    landmark_initializer_workflow = pydra.Workflow(name="landmark_initializer_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    landmark_initializer_workflow.add(get_input_field(name="get_movingLandmark", input_dict=landmark_initializer_workflow.lzin.input_data, field="inputMovingLandmarkFilename"))
    landmark_initializer_workflow.add(make_output_filename(name="outputTransformFilename", filename=experiment_configuration['BRAINSLandmarkInitializer'].get('outputTransformFilename')))

    landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration['BRAINSLandmarkInitializer'].get('executable')).get_task()
    landmark_initializer_task.inputs.inputFixedLandmarkFilename = experiment_configuration['BRAINSLandmarkInitializer'].get('inputFixedLandmarkFilename')
    landmark_initializer_task.inputs.inputMovingLandmarkFilename = landmark_initializer_workflow.get_movingLandmark.lzout.out
    landmark_initializer_task.inputs.inputWeightFilename = experiment_configuration['BRAINSLandmarkInitializer'].get('inputWeightFilename')
    landmark_initializer_task.inputs.outputTransformFilename = landmark_initializer_workflow.outputTransformFilename.lzout.out

    landmark_initializer_workflow.add(landmark_initializer_task)
    landmark_initializer_workflow.set_output(([("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename)]))

    return landmark_initializer_workflow

def make_ABC_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSABC

    abc_workflow = pydra.Workflow(name="abc_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    abc_workflow.add(get_input_field(name="get_inputVolumes", input_dict=abc_workflow.lzin.input_data, field="t1"))
    # abc_workflow.add(make_output_filename(name="outputDirtyLabels", filename=experiment_configuration['BRAINSABC'].get('outputDirtyLabels')))
    abc_workflow.add(make_output_filename(name="outputVolumes", filename=abc_workflow.get_inputVolumes.lzout.out, append_str="_corrected", extension=".txt"))


    abc_task = BRAINSABC(name="BRAINSABC", executable=experiment_configuration['BRAINSABC']['executable']).get_task()
    abc_task.inputs.atlasDefinition = experiment_configuration['BRAINSABC'].get('atlasDefinition')
    abc_task.inputs.atlasToSubjectTransform = experiment_configuration['BRAINSABC'].get('atlasToSubjectTransform')
    abc_task.inputs.atlasToSubjectTransformType = experiment_configuration['BRAINSABC'].get('atlasToSubjectTransformType')
    abc_task.inputs.debuglevel = experiment_configuration['BRAINSABC'].get('debuglevel')
    abc_task.inputs.filterIteration = experiment_configuration['BRAINSABC'].get('filterIteration')
    abc_task.inputs.filterMethod = experiment_configuration['BRAINSABC'].get('filterMethod')
    abc_task.inputs.inputVolumeTypes = experiment_configuration['BRAINSABC'].get('inputVolumeTypes')
    abc_task.inputs.inputVolumes = abc_workflow.get_inputVolumes.lzout.out
    abc_task.inputs.interpolationMode = experiment_configuration['BRAINSABC'].get('interpolationMode')
    abc_task.inputs.maxBiasDegree = experiment_configuration['BRAINSABC'].get('maxBiasDegree')
    abc_task.inputs.maxIterations = experiment_configuration['BRAINSABC'].get('maxIterations')
    abc_task.inputs.outputFormat = experiment_configuration['BRAINSABC'].get('outputFormat')
    abc_task.inputs.outputDir = experiment_configuration['BRAINSABC'].get('outputDir')
    abc_task.inputs.outputDirtyLabels = experiment_configuration['BRAINSABC'].get('outputDirtyLabels')
    abc_task.inputs.outputLabels = experiment_configuration['BRAINSABC'].get('outputLabels')
    abc_task.inputs.outputVolumes = abc_workflow.outputVolumes.lzout.out

    # print(abc_task.cmdline)
    abc_workflow.add(abc_task)
    abc_workflow.set_output([("outputVolumes", abc_workflow.BRAINSABC.lzout.outputVolumes)])

    return abc_workflow

def make_CreateLabelMapFromProbabilityMaps_workflow(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSCreateLabelMapFromProbabilityMaps

    label_map_workflow = pydra.Workflow(name="label_map_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)

    label_map_task = BRAINSCreateLabelMapFromProbabilityMaps(name="BRAINSCreateLabelMapFromProbabilityMaps", executable=experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps']['executable']).get_task()
    label_map_task.inputs.cleanLabelVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('cleanLabelVolume')
    label_map_task.inputs.dirtyLabelVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('dirtyLabelVolume')
    label_map_task.inputs.foregroundPriors = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('foregroundPriors')
    label_map_task.inputs.inputProbabilityVolume = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('inputProbabilityVolume')
    label_map_task.inputs.priorLabelCodes = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('priorLabelCodes')
    label_map_task.inputs.inclusionThreshold = experiment_configuration['BRAINSCreateLabelMapFromProbabilityMaps'].get('inclusionThreshold')

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
    antsRegistration_task.inputs.verbose = experiment_configuration['ANTSRegistration'].get('verbose')
    antsRegistration_task.inputs.collapse_output_transforms = experiment_configuration['ANTSRegistration'].get('collapse-output-transforms')
    antsRegistration_task.inputs.dimensionality = experiment_configuration['ANTSRegistration'].get('dimensionality')
    antsRegistration_task.inputs.float = experiment_configuration['ANTSRegistration'].get('float')
    antsRegistration_task.inputs.initial_moving_transform = experiment_configuration['ANTSRegistration'].get('initial-moving-transform')
    antsRegistration_task.inputs.initialize_transforms_per_stage = experiment_configuration['ANTSRegistration'].get('initialize-transforms-per-stage')
    antsRegistration_task.inputs.interpolation = experiment_configuration['ANTSRegistration'].get('interpolation')
    antsRegistration_task.inputs.output = experiment_configuration['ANTSRegistration'].get('output') #antsRegistration_workflow.outputVolumes.lzout.out # # # # [ "AtlasToSubjectPreBABC_Rigid", "atlas2subjectRigid.nii.gz", "subject2atlasRigid.nii.gz"] ,
    antsRegistration_task.inputs.transform = experiment_configuration['ANTSRegistration'].get('transform')
    antsRegistration_task.inputs.metric = experiment_configuration['ANTSRegistration'].get('metric')
    antsRegistration_task.inputs.convergence = experiment_configuration['ANTSRegistration'].get('convergence')
    antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration['ANTSRegistration'].get('smoothing-sigmas')
    antsRegistration_task.inputs.shrink_factors = experiment_configuration['ANTSRegistration'].get('shrink-factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once = experiment_configuration['ANTSRegistration'].get('use-estimate-learning-rate-once')
    antsRegistration_task.inputs.use_histogram_matching = experiment_configuration['ANTSRegistration'].get('use-histogram-matching')
    antsRegistration_task.inputs.masks = experiment_configuration['ANTSRegistration'].get('masks')
    antsRegistration_task.inputs.winsorize_image_intensities = experiment_configuration['ANTSRegistration'].get('winsorize-image-intensities')
    antsRegistration_task.inputs.write_composite_transform = experiment_configuration['ANTSRegistration'].get('write-composite-transform')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([("output", antsRegistration_workflow.ANTSRegistration.lzout.output)])

    return antsRegistration_workflow

@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
        return list(processed_dict.values())

# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    if cache_path is None:
        return "" # Don't return a cache_path if it is None
    else:
        if type(cache_path) is list:
            output_list = []
            for path in cache_path:
                copyfile(path, Path(output_dir) / Path(path).name)
                out_path = Path(output_dir) / Path(path).name
                copyfile(path, out_path)
                output_list.append(out_path)
            return output_list
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
preliminary_workflow4 = make_bcd_workflow(source_node)
# preliminary_workflow4 = make_resample_workflow(source_node)
# preliminary_workflow4 = make_ROIAuto_workflow(source_node)
# preliminary_workflow4 = make_LandmarkInitializer_workflow(source_node)
# preliminary_workflow4 = make_ABC_workflow(source_node)
# preliminary_workflow4 = make_CreateLabelMapFromProbabilityMaps_workflow(source_node)
# preliminary_workflow4 = make_antsRegistration_workflow(source_node)

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
# source_node.set_output([("output_files", source_node.abc_workflow.lzout.all_),])


# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)