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
        if type(filename) is list:
            new_filename = []
            for f in filename:
                if extension == "":
                    extension = "".join(Path(f).suffixes)
                new_filename.append(f"{Path(Path(directory) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}")
        else:
            # If an extension is not specified and the filename has an extension, use the filename's extension
            if extension == "":
                extension = "".join(Path(filename).suffixes)
            new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
        # Path(new_filename).touch()
        # print(f"touching {new_filename}")
        print(f"filename: {filename}")
        return new_filename


@pydra.mark.task
def get_self(x):
    print(x)
    return x


# @pydra.mark.task
# def get_outputResampledVolume(source_n):
#     print(source_n)
#     return source_n.bcd_workflow.lzout.all_


@pydra.mark.task
def get_input_field(input_dict: dict, field):
    print(f"Getting: {field}")
    print(f"Found: {input_dict[field]}")
    return input_dict[field]

def get_inputs_workflow(my_source_node):

    get_inputs_workflow = pydra.Workflow(name="inputs_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    get_inputs_workflow.add(get_input_field(name="get_inputVolume", input_dict=get_inputs_workflow.lzin.input_data, field="t1"))
    get_inputs_workflow.add(get_input_field(name="get_inputLandmarksEMSP", input_dict=get_inputs_workflow.lzin.input_data, field="inputLandmarksEMSP"))

    get_inputs_workflow.set_output([
        ("inputVolume", get_inputs_workflow.get_inputVolume.lzout.out),
        ("inputLandmarksEMSP", get_inputs_workflow.get_inputLandmarksEMSP.lzout.out)
    ])
    return get_inputs_workflow


def make_bcd_workflow1(inputVolume, inputLandmarksEMSP) -> pydra.Workflow:
    # from .sem_tasks.segmentation.specialized import BRAINSConstellationDetector
    from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

    workflow_name = "bcd_workflow1"
    configkey='BRAINSConstellationDetector1'
    print(f"Making task {workflow_name}")


    # bcd_workflow = pydra.Workflow(name=workflow_name, input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
    #
    # bcd_workflow.add(get_input_field(name="get_t1", input_dict=bcd_workflow.lzin.input_data, field="t1"))
    # bcd_workflow.add(get_input_field(name="get_inputLandmarksEMSP", input_dict=bcd_workflow.lzin.input_data, field="inputLandmarksEMSP"))

    bcd_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume", "inputLandmarksEMSP"], inputVolume=inputVolume, inputLandmarksEMSP=inputLandmarksEMSP)

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration[configkey]['executable']).get_task()
    bcd_task.inputs.inputVolume =                       bcd_workflow.lzin.inputVolume
    bcd_task.inputs.LLSModel =                          experiment_configuration[configkey].get('LLSModel')
    bcd_task.inputs.acLowerBound =                      experiment_configuration[configkey].get('acLowerBound')
    bcd_task.inputs.atlasLandmarkWeights =              experiment_configuration[configkey].get('atlasLandmarkWeights')
    bcd_task.inputs.atlasLandmarks =                    experiment_configuration[configkey].get('atlasLandmarks')
    bcd_task.inputs.houghEyeDetectorMode =              experiment_configuration[configkey].get('houghEyeDetectorMode')
    bcd_task.inputs.inputLandmarksEMSP =                bcd_workflow.lzin.inputLandmarksEMSP
    bcd_task.inputs.inputTemplateModel =                experiment_configuration[configkey].get('inputTemplateModel')
    bcd_task.inputs.interpolationMode =                 experiment_configuration[configkey].get('interpolationMode')
    bcd_task.inputs.outputLandmarksInInputSpace =       experiment_configuration[configkey].get('outputLandmarksInInputSpace')      #bcd_workflow.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume =             experiment_configuration[configkey].get('outputResampledVolume')            #bcd_workflow.outputResampledVolume.lzout.out
    bcd_task.inputs.outputTransform =                   experiment_configuration[configkey].get('outputTransform')                  #bcd_workflow.outputTransform.lzout.out
    bcd_task.inputs.outputLandmarksInACPCAlignedSpace = experiment_configuration[configkey].get('outputLandmarksInACPCAlignedSpace')#bcd_workflow.outputLandmarksInACPCAlignedSpace.lzout.out
    bcd_task.inputs.writeBranded2DImage =               experiment_configuration[configkey].get('writeBranded2DImage')              #bcd_workflow.writeBranded2DImage.lzout.out
    bcd_workflow.add(bcd_task)

    # Set the outputs of the processing node and the source node so they are output to the sink node
    bcd_workflow.set_output([
        ("outputLandmarksInInputSpace",         bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
        ("outputResampledVolume",               bcd_workflow.BRAINSConstellationDetector.lzout.outputResampledVolume),
        ("outputTransform",                     bcd_workflow.BRAINSConstellationDetector.lzout.outputTransform),
        ("outputLandmarksInACPCAlignedSpace",   bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
        ("writeBranded2DImage",                 bcd_workflow.BRAINSConstellationDetector.lzout.writeBranded2DImage)
    ])
    return bcd_workflow

def make_roi_workflow1(inputVolume) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSROIAuto
    workflow_name = "roi_workflow1"
    configkey='BRAINSROIAuto1'
    print(f"Making task {workflow_name}")


    roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

    roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()
    roi_task.inputs.inputVolume =           roi_workflow.lzin.inputVolume
    roi_task.inputs.ROIAutoDilateSize =     experiment_configuration[configkey].get('ROIAutoDilateSize')
    roi_task.inputs.cropOutput =            experiment_configuration[configkey].get('cropOutput')
    roi_task.inputs.outputVolume =          experiment_configuration[configkey].get('outputVolume') #roi_workflow.outputVolume.lzout.out
    # roi_task.inputs.outputROIMaskVolume = roi_workflow.outputROIMaskVolume.lzout.out

    roi_workflow.add(roi_task)
    roi_workflow.set_output([
        ("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume),
        # ("outputROIMaskVolume", roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume),
    ])

    return roi_workflow

def make_landmarkInitializer_workflow1(inputMovingLandmarkFilename) -> pydra.Workflow:
    from sem_tasks.utilities.brains import BRAINSLandmarkInitializer
    workflow_name = "landmarkInitializer_workflow1"
    configkey='BRAINSLandmarkInitializer1'
    print(f"Making task {workflow_name}")


    landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputMovingLandmarkFilename"], inputMovingLandmarkFilename=inputMovingLandmarkFilename)

    landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()
    landmark_initializer_task.inputs.inputFixedLandmarkFilename =   experiment_configuration[configkey].get('inputFixedLandmarkFilename')
    landmark_initializer_task.inputs.inputMovingLandmarkFilename =  landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
    landmark_initializer_task.inputs.inputWeightFilename =          experiment_configuration[configkey].get('inputWeightFilename')
    landmark_initializer_task.inputs.outputTransformFilename =      experiment_configuration[configkey].get('outputTransformFilename') #landmark_initializer_workflow.outputTransformFilename.lzout.out

    landmark_initializer_workflow.add(landmark_initializer_task)
    landmark_initializer_workflow.set_output([
        ("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename)
    ])
    return landmark_initializer_workflow

def make_landmarkInitializer_workflow2(inputFixedLandmarkFilename) -> pydra.Workflow:
    from sem_tasks.utilities.brains import BRAINSLandmarkInitializer
    workflow_name = "landmarkInitializer_workflow2"
    configkey='BRAINSLandmarkInitializer2'
    print(f"Making task {workflow_name}")


    landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputFixedLandmarkFilename"], inputFixedLandmarkFilename=inputFixedLandmarkFilename)

    landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()
    landmark_initializer_task.inputs.inputFixedLandmarkFilename =   landmark_initializer_workflow.lzin.inputFixedLandmarkFilename
    landmark_initializer_task.inputs.inputMovingLandmarkFilename =  experiment_configuration[configkey].get('inputMovingLandmarkFilename')
    landmark_initializer_task.inputs.inputWeightFilename =          experiment_configuration[configkey].get('inputWeightFilename')
    landmark_initializer_task.inputs.outputTransformFilename =      experiment_configuration[configkey].get('outputTransformFilename')

    landmark_initializer_workflow.add(landmark_initializer_task)
    landmark_initializer_workflow.set_output([
        ("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename)
    ])

    return landmark_initializer_workflow

def make_resample_workflow1(inputVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow1"
    configkey='BRAINSResample1'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume", "warpTransform"], inputVolume=inputVolume, warpTransform=warpTransform)
    # resample_workflow.add(get_input_field(name="get_t1", input_dict=resample_workflow.lzin.input_data, field="t1"))

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          resample_workflow.lzin.inputVolume
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_roi_workflow2(inputVolume) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSROIAuto
    workflow_name = "roi_workflow2"
    configkey='BRAINSROIAuto2'
    print(f"Making task {workflow_name}")

    roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

    roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()
    roi_task.inputs.inputVolume =           roi_workflow.lzin.inputVolume
    roi_task.inputs.ROIAutoDilateSize =     experiment_configuration[configkey].get('ROIAutoDilateSize')
    roi_task.inputs.outputROIMaskVolume =   experiment_configuration[configkey].get('outputROIMaskVolume')

    roi_workflow.add(roi_task)
    roi_workflow.set_output([
        ("outputROIMaskVolume", roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume),
    ])

    return roi_workflow

def make_antsRegistration_workflow1(fixed_image, fixed_image_masks, initial_moving_transform) -> pydra.Workflow:
    from pydra.tasks.nipype1.utils import Nipype1Task
    from nipype.interfaces.ants import Registration

    workflow_name = "antsRegistration_workflow1"
    configkey='ANTSRegistration1'
    print(f"Making task {workflow_name}")

    # Create the workflow
    antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform)

    antsRegistration_task = Nipype1Task(Registration())

    # Set subject-specific files
    antsRegistration_task.inputs.fixed_image =                          antsRegistration_workflow.lzin.fixed_image #'/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz'
    antsRegistration_task.inputs.fixed_image_masks =                    antsRegistration_workflow.lzin.fixed_image_masks #['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz']*3
    antsRegistration_task.inputs.initial_moving_transform =             antsRegistration_workflow.lzin.initial_moving_transform #'/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/landmarkInitializer_atlas_to_subject_transform.h5'

    antsRegistration_task.inputs.moving_image =                         experiment_configuration[configkey].get('moving_image')
    antsRegistration_task.inputs.moving_image_masks =                   experiment_configuration[configkey].get('moving_image_masks')
    antsRegistration_task.inputs.transforms =                           experiment_configuration[configkey].get('transforms')
    antsRegistration_task.inputs.transform_parameters =                 experiment_configuration[configkey].get('transform_parameters')
    antsRegistration_task.inputs.number_of_iterations =                 experiment_configuration[configkey].get('number_of_iterations')
    antsRegistration_task.inputs.dimension =                            experiment_configuration[configkey].get('dimensionality')
    antsRegistration_task.inputs.write_composite_transform =            experiment_configuration[configkey].get('write_composite_transform')
    antsRegistration_task.inputs.collapse_output_transforms =           experiment_configuration[configkey].get('collapse_output_transforms')
    antsRegistration_task.inputs.verbose =                              experiment_configuration[configkey].get('verbose')
    antsRegistration_task.inputs.initialize_transforms_per_stage =      experiment_configuration[configkey].get('initialize_transforms_per_stage')
    antsRegistration_task.inputs.float =                                experiment_configuration[configkey].get('float')
    antsRegistration_task.inputs.metric =                               experiment_configuration[configkey].get('metric')
    antsRegistration_task.inputs.metric_weight =                        experiment_configuration[configkey].get('metric_weight')
    antsRegistration_task.inputs.radius_or_number_of_bins =             experiment_configuration[configkey].get('radius_or_number_of_bins')
    antsRegistration_task.inputs.sampling_strategy =                    experiment_configuration[configkey].get('sampling_strategy')
    antsRegistration_task.inputs.sampling_percentage =                  experiment_configuration[configkey].get('sampling_percentage')
    antsRegistration_task.inputs.convergence_threshold =                experiment_configuration[configkey].get('convergence_threshold')
    antsRegistration_task.inputs.convergence_window_size =              experiment_configuration[configkey].get('convergence_window_size')
    antsRegistration_task.inputs.smoothing_sigmas =                     experiment_configuration[configkey].get('smoothing_sigmas')
    antsRegistration_task.inputs.sigma_units =                          experiment_configuration[configkey].get('sigma_units')
    antsRegistration_task.inputs.shrink_factors =                       experiment_configuration[configkey].get('shrink_factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once =      experiment_configuration[configkey].get('use_estimate_learning_rate_once')
    antsRegistration_task.inputs.use_histogram_matching =               experiment_configuration[configkey].get('use_histogram_matching')
    antsRegistration_task.inputs.winsorize_lower_quantile =             experiment_configuration[configkey].get('winsorize_lower_quantile')
    antsRegistration_task.inputs.winsorize_upper_quantile =             experiment_configuration[configkey].get('winsorize_upper_quantile')

    # Set the variables that set output file names
    antsRegistration_task.inputs.output_transform_prefix =              experiment_configuration[configkey].get('output_transform_prefix')
    antsRegistration_task.inputs.output_warped_image =                  experiment_configuration[configkey].get('output_warped_image')
    antsRegistration_task.inputs.output_inverse_warped_image =          experiment_configuration[configkey].get('output_inverse_warped_image')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([
        ("composite_transform", antsRegistration_task.lzout.composite_transform),
        ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
        ("warped_image", antsRegistration_task.lzout.warped_image),
        ("inverse_warped_image", antsRegistration_task.lzout.inverse_warped_image),
    ])

    return antsRegistration_workflow

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



def make_antsRegistration_workflow2(my_source_node: pydra.Workflow) -> pydra.Workflow:
    from pydra.tasks.nipype1.utils import Nipype1Task
    from nipype.interfaces.ants import Registration

    # Create the workflow
    antsRegistration_workflow = pydra.Workflow(name="antsRegistration_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)

    # Get inputs specific to the subject
    antsRegistration_workflow.add(get_input_field(name="get_fixed_image", input_dict=antsRegistration_workflow.lzin.input_data, field="abcInputVolume"))
    antsRegistration_workflow.add(get_input_field(name="get_fixed_image_masks", input_dict=antsRegistration_workflow.lzin.input_data, field="fixed_image_masks"))
    antsRegistration_workflow.add(get_input_field(name="get_initial_moving_transform", input_dict=antsRegistration_workflow.lzin.input_data, field="initial_moving_transform2"))

    antsRegistration_task = Nipype1Task(Registration())

    # Set subject-specific files
    antsRegistration_task.inputs.fixed_image =                          antsRegistration_workflow.get_fixed_image.lzout.out #'/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz'
    antsRegistration_task.inputs.fixed_image_masks =                    antsRegistration_workflow.get_fixed_image_masks.lzout.out #['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz']*3
    antsRegistration_task.inputs.initial_moving_transform =             antsRegistration_workflow.get_initial_moving_transform.lzout.out #'/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/landmarkInitializer_atlas_to_subject_transform.h5'

    antsRegistration_task.inputs.moving_image = experiment_configuration['ANTSRegistration2'].get('moving_image')
    antsRegistration_task.inputs.moving_image_masks =               experiment_configuration['ANTSRegistration2'].get('moving_image_masks')
    antsRegistration_task.inputs.save_state =                       experiment_configuration['ANTSRegistration2'].get('save_state')
    antsRegistration_task.inputs.transforms =                       experiment_configuration['ANTSRegistration2'].get('transforms')
    antsRegistration_task.inputs.transform_parameters =             experiment_configuration['ANTSRegistration2'].get('transform_parameters')
    antsRegistration_task.inputs.number_of_iterations =             experiment_configuration['ANTSRegistration2'].get('number_of_iterations')
    antsRegistration_task.inputs.dimension =                        experiment_configuration['ANTSRegistration2'].get('dimensionality')
    antsRegistration_task.inputs.write_composite_transform =        experiment_configuration['ANTSRegistration2'].get('write_composite_transform')
    antsRegistration_task.inputs.collapse_output_transforms =       experiment_configuration['ANTSRegistration2'].get('collapse_output_transforms')
    antsRegistration_task.inputs.verbose =                          experiment_configuration['ANTSRegistration2'].get('verbose')
    antsRegistration_task.inputs.initialize_transforms_per_stage =  experiment_configuration['ANTSRegistration2'].get('initialize_transforms_per_stage')
    antsRegistration_task.inputs.float =                            experiment_configuration['ANTSRegistration2'].get('float')
    antsRegistration_task.inputs.metric =                           experiment_configuration['ANTSRegistration2'].get('metric')
    antsRegistration_task.inputs.metric_weight =                    experiment_configuration['ANTSRegistration2'].get('metric_weight')
    antsRegistration_task.inputs.radius_or_number_of_bins =         experiment_configuration['ANTSRegistration2'].get('radius_or_number_of_bins')
    antsRegistration_task.inputs.sampling_strategy =                experiment_configuration['ANTSRegistration2'].get('sampling_strategy')
    antsRegistration_task.inputs.sampling_percentage =              experiment_configuration['ANTSRegistration2'].get('sampling_percentage')
    antsRegistration_task.inputs.convergence_threshold =            experiment_configuration['ANTSRegistration2'].get('convergence_threshold')
    antsRegistration_task.inputs.convergence_window_size =          experiment_configuration['ANTSRegistration2'].get('convergence_window_size')
    antsRegistration_task.inputs.smoothing_sigmas =                 experiment_configuration['ANTSRegistration2'].get('smoothing_sigmas')
    antsRegistration_task.inputs.sigma_units =                      experiment_configuration['ANTSRegistration2'].get('sigma_units')
    antsRegistration_task.inputs.shrink_factors =                   experiment_configuration['ANTSRegistration2'].get('shrink_factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once =  experiment_configuration['ANTSRegistration2'].get('use_estimate_learning_rate_once')
    antsRegistration_task.inputs.use_histogram_matching =           experiment_configuration['ANTSRegistration2'].get('use_histogram_matching')
    antsRegistration_task.inputs.winsorize_lower_quantile =         experiment_configuration['ANTSRegistration2'].get('winsorize_lower_quantile')
    antsRegistration_task.inputs.winsorize_upper_quantile =         experiment_configuration['ANTSRegistration2'].get('winsorize_upper_quantile')

    # Set the variables that set output file names
    antsRegistration_task.inputs.output_transform_prefix =          experiment_configuration['ANTSRegistration2'].get('output_transform_prefix')
    antsRegistration_task.inputs.output_warped_image =              experiment_configuration['ANTSRegistration2'].get('output_warped_image')
    antsRegistration_task.inputs.output_inverse_warped_image =      experiment_configuration['ANTSRegistration2'].get('output_inverse_warped_image')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([
        ("composite_transform", antsRegistration_task.lzout.composite_transform),
        ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
        ("warped_image", antsRegistration_task.lzout.warped_image),
        ("inverse_warped_image", antsRegistration_task.lzout.inverse_warped_image),
    ])

    return antsRegistration_workflow

@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    return list(processed_dict.values())

# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir, input_data):
    input_filename = Path(input_data.get('t1')).with_suffix('').with_suffix('').name
    file_output_dir = Path(output_dir) / Path(input_filename)
    file_output_dir.mkdir(parents=True, exist_ok=True)
    if cache_path is None:
        print(f"cache_path: {cache_path}")
        return "" # Don't return a cache_path if it is None
    else:
        if type(cache_path) is list:
            output_list = []
            for path in cache_path:
                out_path = Path(file_output_dir) / Path(path).name
                print(f"Copying from {path} to {out_path}")
                copyfile(path, out_path)
                output_list.append(out_path)
            return output_list
        else:
            out_path = Path(file_output_dir) / Path(cache_path).name
            print(f"Copying from {cache_path} to {out_path}")
            copyfile(cache_path, out_path)
            return cache_path

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
source_node = pydra.Workflow(name="source_node", input_spec=["input_data"], cache_dir=experiment_configuration["cache_dir"])
source_node.inputs.input_data = experiment_configuration["input_data"]
source_node.split("input_data")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

# Get the processing workflow defined in a separate function
# bcd_workflow1 =
source_node.add(get_inputs_workflow(my_source_node=source_node))

source_node.add(make_bcd_workflow1(inputVolume=source_node.inputs_workflow.lzout.inputVolume, inputLandmarksEMSP=source_node.inputs_workflow.lzout.inputLandmarksEMSP))
source_node.add(make_roi_workflow1(inputVolume=source_node.bcd_workflow1.lzout.outputResampledVolume))
source_node.add(make_landmarkInitializer_workflow1(inputMovingLandmarkFilename=source_node.bcd_workflow1.lzout.outputLandmarksInInputSpace))
source_node.add(make_landmarkInitializer_workflow2(inputFixedLandmarkFilename=source_node.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace))
source_node.add(make_resample_workflow1(inputVolume=source_node.inputs_workflow.lzout.inputVolume, warpTransform=source_node.landmarkInitializer_workflow1.lzout.outputTransformFilename))
source_node.add(make_roi_workflow2(inputVolume=source_node.roi_workflow1.lzout.outputVolume))
source_node.add(make_antsRegistration_workflow1(fixed_image=source_node.roi_workflow1.lzout.outputVolume, fixed_image_masks=source_node.roi_workflow2.lzout.outputROIMaskVolume, initial_moving_transform=source_node.landmarkInitializer_workflow2.lzout.outputTransformFilename))

# preliminary_workflow4 = make_resample_workflow(source_node)
# preliminary_workflow4 = make_LandmarkInitializer_workflow(source_node)
# preliminary_workflow4 = make_ABC_workflow(source_node)
# preliminary_workflow4 = make_CreateLabelMapFromProbabilityMaps_workflow(source_node)
# preliminary_workflow4 = make_antsRegistration_workflow(source_node)
# preliminary_workflow4 = make_antsRegistration_workflow2(source_node)
final_processing_workflow = source_node.antsRegistration_workflow1


# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files', 'input_data'], processed_files=final_processing_workflow.lzout.all_, input_data=source_node.lzin.input_data)
sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
sink_node.add(copy_from_cache(name="copy_from_cache", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out, input_data=sink_node.lzin.input_data).split("cache_path"))
sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])


source_node.add(sink_node)

# Set the output of the source node to the same as the output of the sink_node
source_node.set_output([("output_files", source_node.sink_node.lzout.output_files),])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)