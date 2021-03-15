import pydra
from pathlib import Path
from shutil import copyfile
import json
import argparse
import attr
from nipype.interfaces.base import (
    File,
)


parser = argparse.ArgumentParser(description='Move echo numbers in fmap BIDS data to JSON sidecars')
parser.add_argument('config_experimental', type=str, help='Path to the json file for configuring task parameters')
parser.add_argument('input_data_dictionary', type=str, help='Path to the json file for input data')
args = parser.parse_args()

with open(args.config_experimental) as f:
    experiment_configuration = json.load(f)
with open(args.input_data_dictionary) as f:
    input_data_dictionary = json.load(f)



@pydra.mark.task
def get_self(x):
    print(f"type of self: {type(x)}")
    print(f"self: {x}")
    print(f"x[0]: {x[0]}")
    list = []
    for index, ele in enumerate(x):
        list.append(str(ele))
    print(f"list: {list}")
    return list

@pydra.mark.task
def get_atlas_id(atlas_id):
    return atlas_id

@pydra.mark.task
def get_atlas_id_from_transform(transform):
    atlas_id = transform
    print(atlas_id)
    return atlas_id


@pydra.mark.task
def make_output_filename(filename="", before_str="", append_str="", extension="", directory="", parent_dir="", unused=""):
    print("Making output filename")
    if filename is None:
        print("filename is none")
        return None
    else:
        # If we want to set the parent id for a subject, the following if statement converts as follows:
        # "/localscratch/Users/cjohnson30/wf_ref/20160523_HDAdultAtlas/91300/t1_average_BRAINSABC_GaussianDenoised.nii.gz" -> "91300"
        if type(filename) is list:
            new_filename = []
            for f in filename:
                if extension == "":
                    extension = "".join(Path(f).suffixes)
                new_filename.append(f"{Path(Path(directory) / Path(parent_dir) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}")
        else:
            # If an extension is not specified and the filename has an extension, use the filename's extension
            if extension == "":
                extension = "".join(Path(filename).suffixes)
            new_filename = f"{Path(Path(directory) / Path(parent_dir) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
        print(f"filename: {filename}")
        print(f"parent_dir: {parent_dir}")
        print(f"new_filename: {new_filename}")
        return new_filename

@pydra.mark.task
def get_parent_directory(filepath):
    return Path(filepath).parent.name

@pydra.mark.task
def get_input_field(input_dict: dict, field):
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
    from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

    workflow_name = "bcd_workflow1"
    configkey='BRAINSConstellationDetector1'
    print(f"Making task {workflow_name}")

    bcd_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume", "inputLandmarksEMSP"], inputVolume=inputVolume, inputLandmarksEMSP=inputLandmarksEMSP)

    # bcd_workflow.add(make_output_filename(name="outputLandmarksInInputSpace", filename=experiment_configuration[configkey].get('outputLandmarksInInputSpace')))
    # bcd_workflow.add(make_output_filename(name="outputResampledVolume", filename=experiment_configuration[configkey].get('outputResampledVolume')))
    # bcd_workflow.add(make_output_filename(name="outputTransform", filename=experiment_configuration[configkey].get('outputTransform')))
    # bcd_workflow.add(make_output_filename(name="outputLandmarksInACPCAlignedSpace", filename=experiment_configuration[configkey].get('outputLandmarksInACPCAlignedSpace')))
    # bcd_workflow.add(make_output_filename(name="writeBranded2DImage", filename=experiment_configuration[configkey].get('writeBranded2DImage')))


    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration[configkey]['executable']).get_task()
    bcd_task.inputs.inputVolume =                       bcd_workflow.lzin.inputVolume    #"/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-273625_ses-47445_run-002_T1w.nii.gz" #"/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-052823_ses-43817_run-002_T1w.nii.gz" #bcd_workflow.lzin.inputVolume
    bcd_task.inputs.LLSModel =                          experiment_configuration[configkey].get('LLSModel')
    bcd_task.inputs.acLowerBound =                      experiment_configuration[configkey].get('acLowerBound')
    bcd_task.inputs.atlasLandmarkWeights =              experiment_configuration[configkey].get('atlasLandmarkWeights')
    bcd_task.inputs.atlasLandmarks =                    experiment_configuration[configkey].get('atlasLandmarks')
    bcd_task.inputs.houghEyeDetectorMode =              experiment_configuration[configkey].get('houghEyeDetectorMode')
    bcd_task.inputs.inputLandmarksEMSP =                bcd_workflow.lzin.inputLandmarksEMSP #"/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-273625_ses-47445_run-002_T1w.fcsv" #"/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-052823_ses-43817_run-002_T1w.fcsv" #bcd_workflow.lzin.inputLandmarksEMSP
    bcd_task.inputs.inputTemplateModel =                experiment_configuration[configkey].get('inputTemplateModel')
    bcd_task.inputs.interpolationMode =                 experiment_configuration[configkey].get('interpolationMode')

    bcd_task.inputs.outputLandmarksInInputSpace =       experiment_configuration[configkey].get('outputLandmarksInInputSpace')      #bcd_workflow.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume =             experiment_configuration[configkey].get('outputResampledVolume')            #bcd_workflow.outputResampledVolume.lzout.out
    bcd_task.inputs.outputTransform =                   experiment_configuration[configkey].get('outputTransform')                  #bcd_workflow.outputTransform.lzout.out
    bcd_task.inputs.outputLandmarksInACPCAlignedSpace = experiment_configuration[configkey].get('outputLandmarksInACPCAlignedSpace')#bcd_workflow.outputLandmarksInACPCAlignedSpace.lzout.out
    bcd_task.inputs.writeBranded2DImage =               experiment_configuration[configkey].get('writeBranded2DImage')              #bcd_workflow.writeBranded2DImage.lzout.out
    bcd_workflow.add(bcd_task)

    # print(bcd_task.cmdline)

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

    roi_workflow.add(roi_task)
    roi_workflow.set_output([
        ("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume),
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
    antsRegistration_task.inputs.fixed_image =                     antsRegistration_workflow.lzin.fixed_image
    antsRegistration_task.inputs.fixed_image_masks =               antsRegistration_workflow.lzin.fixed_image_masks
    antsRegistration_task.inputs.initial_moving_transform =        antsRegistration_workflow.lzin.initial_moving_transform

    antsRegistration_task.inputs.moving_image =                    experiment_configuration[configkey].get('moving_image')
    antsRegistration_task.inputs.moving_image_masks =              experiment_configuration[configkey].get('moving_image_masks')
    antsRegistration_task.inputs.transforms =                      experiment_configuration[configkey].get('transforms')
    antsRegistration_task.inputs.transform_parameters =            experiment_configuration[configkey].get('transform_parameters')
    antsRegistration_task.inputs.number_of_iterations =            experiment_configuration[configkey].get('number_of_iterations')
    antsRegistration_task.inputs.dimension =                       experiment_configuration[configkey].get('dimensionality')
    antsRegistration_task.inputs.write_composite_transform =       experiment_configuration[configkey].get('write_composite_transform')
    antsRegistration_task.inputs.collapse_output_transforms =      experiment_configuration[configkey].get('collapse_output_transforms')
    antsRegistration_task.inputs.verbose =                         experiment_configuration[configkey].get('verbose')
    antsRegistration_task.inputs.initialize_transforms_per_stage = experiment_configuration[configkey].get('initialize_transforms_per_stage')
    antsRegistration_task.inputs.float =                           experiment_configuration[configkey].get('float')
    antsRegistration_task.inputs.metric =                          experiment_configuration[configkey].get('metric')
    antsRegistration_task.inputs.metric_weight =                   experiment_configuration[configkey].get('metric_weight')
    antsRegistration_task.inputs.radius_or_number_of_bins =        experiment_configuration[configkey].get('radius_or_number_of_bins')
    antsRegistration_task.inputs.sampling_strategy =               experiment_configuration[configkey].get('sampling_strategy')
    antsRegistration_task.inputs.sampling_percentage =             experiment_configuration[configkey].get('sampling_percentage')
    antsRegistration_task.inputs.convergence_threshold =           experiment_configuration[configkey].get('convergence_threshold')
    antsRegistration_task.inputs.convergence_window_size =         experiment_configuration[configkey].get('convergence_window_size')
    antsRegistration_task.inputs.smoothing_sigmas =                experiment_configuration[configkey].get('smoothing_sigmas')
    antsRegistration_task.inputs.sigma_units =                     experiment_configuration[configkey].get('sigma_units')
    antsRegistration_task.inputs.shrink_factors =                  experiment_configuration[configkey].get('shrink_factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once = experiment_configuration[configkey].get('use_estimate_learning_rate_once')
    antsRegistration_task.inputs.use_histogram_matching =          experiment_configuration[configkey].get('use_histogram_matching')
    antsRegistration_task.inputs.winsorize_lower_quantile =        experiment_configuration[configkey].get('winsorize_lower_quantile')
    antsRegistration_task.inputs.winsorize_upper_quantile =        experiment_configuration[configkey].get('winsorize_upper_quantile')

    # Set the variables that set output file names
    antsRegistration_task.inputs.output_transform_prefix =         experiment_configuration[configkey].get('output_transform_prefix')
    antsRegistration_task.inputs.output_warped_image =             experiment_configuration[configkey].get('output_warped_image')
    antsRegistration_task.inputs.output_inverse_warped_image =     experiment_configuration[configkey].get('output_inverse_warped_image')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([
        ("composite_transform", antsRegistration_task.lzout.composite_transform),
        ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
        ("warped_image", antsRegistration_task.lzout.warped_image),
        ("inverse_warped_image", antsRegistration_task.lzout.inverse_warped_image),
    ])

    return antsRegistration_workflow

def make_antsRegistration_workflow2(fixed_image, fixed_image_masks, initial_moving_transform) -> pydra.Workflow:
    from pydra.tasks.nipype1.utils import Nipype1Task
    from nipype.interfaces.ants import Registration

    workflow_name = "antsRegistration_workflow2"
    configkey='ANTSRegistration2'
    print(f"Making task {workflow_name}")

    # Create the workflow
    antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform)

    antsRegistration_task = Nipype1Task(Registration())

    # Set subject-specific files
    antsRegistration_task.inputs.fixed_image =                      antsRegistration_workflow.lzin.fixed_image
    antsRegistration_task.inputs.fixed_image_masks =                antsRegistration_workflow.lzin.fixed_image_masks
    antsRegistration_task.inputs.initial_moving_transform =         antsRegistration_workflow.lzin.initial_moving_transform

    antsRegistration_task.inputs.moving_image =                     experiment_configuration[configkey].get('moving_image')
    antsRegistration_task.inputs.moving_image_masks =               experiment_configuration[configkey].get('moving_image_masks')
    antsRegistration_task.inputs.save_state =                       experiment_configuration[configkey].get('save_state')
    antsRegistration_task.inputs.transforms =                       experiment_configuration[configkey].get('transforms')
    antsRegistration_task.inputs.transform_parameters =             experiment_configuration[configkey].get('transform_parameters')
    antsRegistration_task.inputs.number_of_iterations =             experiment_configuration[configkey].get('number_of_iterations')
    antsRegistration_task.inputs.dimension =                        experiment_configuration[configkey].get('dimensionality')
    antsRegistration_task.inputs.write_composite_transform =        experiment_configuration[configkey].get('write_composite_transform')
    antsRegistration_task.inputs.collapse_output_transforms =       experiment_configuration[configkey].get('collapse_output_transforms')
    antsRegistration_task.inputs.verbose =                          experiment_configuration[configkey].get('verbose')
    antsRegistration_task.inputs.initialize_transforms_per_stage =  experiment_configuration[configkey].get('initialize_transforms_per_stage')
    antsRegistration_task.inputs.float =                            experiment_configuration[configkey].get('float')
    antsRegistration_task.inputs.metric =                           experiment_configuration[configkey].get('metric')
    antsRegistration_task.inputs.metric_weight =                    experiment_configuration[configkey].get('metric_weight')
    antsRegistration_task.inputs.radius_or_number_of_bins =         experiment_configuration[configkey].get('radius_or_number_of_bins')
    antsRegistration_task.inputs.sampling_strategy =                experiment_configuration[configkey].get('sampling_strategy')
    antsRegistration_task.inputs.sampling_percentage =              experiment_configuration[configkey].get('sampling_percentage')
    antsRegistration_task.inputs.convergence_threshold =            experiment_configuration[configkey].get('convergence_threshold')
    antsRegistration_task.inputs.convergence_window_size =          experiment_configuration[configkey].get('convergence_window_size')
    antsRegistration_task.inputs.smoothing_sigmas =                 experiment_configuration[configkey].get('smoothing_sigmas')
    antsRegistration_task.inputs.sigma_units =                      experiment_configuration[configkey].get('sigma_units')
    antsRegistration_task.inputs.shrink_factors =                   experiment_configuration[configkey].get('shrink_factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once =  experiment_configuration[configkey].get('use_estimate_learning_rate_once')
    antsRegistration_task.inputs.use_histogram_matching =           experiment_configuration[configkey].get('use_histogram_matching')
    antsRegistration_task.inputs.winsorize_lower_quantile =         experiment_configuration[configkey].get('winsorize_lower_quantile')
    antsRegistration_task.inputs.winsorize_upper_quantile =         experiment_configuration[configkey].get('winsorize_upper_quantile')

    # Set the variables that set output file names
    antsRegistration_task.inputs.output_transform_prefix =          experiment_configuration[configkey].get('output_transform_prefix')
    antsRegistration_task.inputs.output_warped_image =              experiment_configuration[configkey].get('output_warped_image')
    antsRegistration_task.inputs.output_inverse_warped_image =      experiment_configuration[configkey].get('output_inverse_warped_image')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([
        ("save_state", antsRegistration_task.lzout.save_state),
        ("composite_transform", antsRegistration_task.lzout.composite_transform),
        ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
        ("warped_image", antsRegistration_task.lzout.warped_image),
        ("inverse_warped_image", antsRegistration_task.lzout.inverse_warped_image),
    ])

    return antsRegistration_workflow

@pydra.mark.task
def get_t1_average(outputs):
    return outputs[0]

@pydra.mark.task
def get_posteriors(outputs):
    # print(type(outputs[1:]))
    # print(outputs[1:])
    return outputs[1:]



def make_abc_workflow1(inputVolumes, inputT1, restoreState) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSABC

    workflow_name = "abc_workflow1"
    configkey='BRAINSABC1'
    print(f"Making task {workflow_name}")

    # Create the workflow
    abc_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolumes", "inputT1", "restoreState"], inputVolumes=inputVolumes, inputT1=inputT1, restoreState=restoreState)
    abc_workflow.add(make_output_filename(name="outputVolumes", filename=abc_workflow.lzin.inputT1, append_str="_corrected", extension=".nii.gz"))

    # abc_workflow.add(get_self(name="get_self", x=abc_workflow.outputVolumes.lzout.out))
    # abc_workflow.add(get_self(name="get_self2", x=abc_workflow.lzin.inputVolumes))

    abc_task = BRAINSABC(name="BRAINSABC", executable=experiment_configuration[configkey]['executable']).get_task()

    abc_task.inputs.atlasDefinition =               experiment_configuration[configkey].get('atlasDefinition')
    abc_task.inputs.atlasToSubjectTransform =       experiment_configuration[configkey].get('atlasToSubjectTransform')
    abc_task.inputs.atlasToSubjectTransformType =   experiment_configuration[configkey].get('atlasToSubjectTransformType')
    abc_task.inputs.debuglevel =                    experiment_configuration[configkey].get('debuglevel')
    abc_task.inputs.filterIteration =               experiment_configuration[configkey].get('filterIteration')
    abc_task.inputs.filterMethod =                  experiment_configuration[configkey].get('filterMethod')
    abc_task.inputs.inputVolumeTypes =              experiment_configuration[configkey].get('inputVolumeTypes')
    abc_task.inputs.inputVolumes =                  abc_workflow.lzin.inputVolumes #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" # # # #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" #  #abc_workflow.lzin.inputVolumes
    abc_task.inputs.interpolationMode =             experiment_configuration[configkey].get('interpolationMode')
    abc_task.inputs.maxBiasDegree =                 experiment_configuration[configkey].get('maxBiasDegree')
    abc_task.inputs.maxIterations =                 experiment_configuration[configkey].get('maxIterations')
    abc_task.inputs.posteriorTemplate =             experiment_configuration[configkey].get('POSTERIOR_%s.nii.gz')
    abc_task.inputs.purePlugsThreshold =            experiment_configuration[configkey].get('purePlugsThreshold')
    abc_task.inputs.restoreState =                  abc_workflow.lzin.restoreState #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" # #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #
    abc_task.inputs.saveState =                     experiment_configuration[configkey].get('saveState')
    abc_task.inputs.useKNN =                        experiment_configuration[configkey].get('useKNN')
    abc_task.inputs.outputFormat =                  experiment_configuration[configkey].get('outputFormat')
    abc_task.inputs.outputDir =                     experiment_configuration[configkey].get('outputDir')
    abc_task.inputs.outputDirtyLabels =             experiment_configuration[configkey].get('outputDirtyLabels')
    abc_task.inputs.outputLabels =                  experiment_configuration[configkey].get('outputLabels')
    abc_task.inputs.outputVolumes =                 abc_workflow.outputVolumes.lzout.out #"sub-052823_ses-43817_run-002_T1w_corrected.nii.gz" # #"sub-052823_ses-43817_run-002_T1w_corrected.nii.gz" #
    abc_task.inputs.implicitOutputs =               [experiment_configuration[configkey].get('t1_average')] + experiment_configuration[configkey].get('posteriors')



    abc_workflow.add(abc_task)
    abc_workflow.add(get_t1_average(name="get_t1_average", outputs=abc_task.lzout.implicitOutputs))
    abc_workflow.add(get_posteriors(name="get_posteriors", outputs=abc_task.lzout.implicitOutputs))
    abc_workflow.set_output([
        ("outputVolumes", abc_workflow.BRAINSABC.lzout.outputVolumes),
        ("outputDirtyLabels", abc_workflow.BRAINSABC.lzout.outputDirtyLabels),
        ("outputLabels", abc_workflow.BRAINSABC.lzout.outputLabels),
        ("atlasToSubjectTransform", abc_workflow.BRAINSABC.lzout.atlasToSubjectTransform),
        ("t1_average", abc_workflow.get_t1_average.lzout.out),
        ("posteriors", abc_workflow.get_posteriors.lzout.out),
        # ("posteriors", abc_workflow.BRAINSABC.lzout.implicitOutputs),

    ])

    return abc_workflow

def make_resample_workflow2(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow2"
    configkey='BRAINSResample2'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow3(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow3"
    configkey='BRAINSResample3'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow4(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow4"
    configkey='BRAINSResample4'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow5(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow5"
    configkey='BRAINSResample5'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow6(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow6"
    configkey='BRAINSResample6'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow7(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow7"
    configkey='BRAINSResample7'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_resample_workflow8(referenceVolume, warpTransform) -> pydra.Workflow:
    from sem_tasks.registration import BRAINSResample
    workflow_name = "resample_workflow8"
    configkey='BRAINSResample8'
    print(f"Making task {workflow_name}")

    resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

    # Set the inputs of Resample
    resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()
    resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
    resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
    resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
    resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")
    resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
    resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform

    resample_workflow.add(resample_task)
    resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

    return resample_workflow

def make_createLabelMapFromProbabilityMaps_workflow1(inputProbabilityVolume, nonAirRegionMask) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSCreateLabelMapFromProbabilityMaps
    workflow_name = "createLabelMapFromProbabilityMaps_workflow1"
    configkey='BRAINSCreateLabelMapFromProbabilityMaps1'
    print(f"Making task {workflow_name}")

    label_map_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputProbabilityVolume", "nonAirRegionMask"], inputProbabilityVolume=inputProbabilityVolume, nonAirRegionMask=nonAirRegionMask)

    label_map_task = BRAINSCreateLabelMapFromProbabilityMaps(name="BRAINSCreateLabelMapFromProbabilityMaps", executable=experiment_configuration[configkey]['executable']).get_task()
    label_map_task.inputs.cleanLabelVolume =            experiment_configuration[configkey].get('cleanLabelVolume')
    label_map_task.inputs.dirtyLabelVolume =            experiment_configuration[configkey].get('dirtyLabelVolume')
    label_map_task.inputs.foregroundPriors =            experiment_configuration[configkey].get('foregroundPriors')
    label_map_task.inputs.inputProbabilityVolume =      label_map_workflow.lzin.inputProbabilityVolume #experiment_configuration[configkey].get('inputProbabilityVolume') #label_map_workflow.get_self.lzout.out # #label_map_workflow.get_self.lzout.out #label_map_workflow.lzin.inputProbabilityVolume #  # #label_map_workflow.lzin.inputProbabilityVolume # #inputProbabilityVolumes #label_map_workflow.lzin.inputProbabilityVolume # # #
    label_map_task.inputs.priorLabelCodes =             experiment_configuration[configkey].get('priorLabelCodes')
    label_map_task.inputs.inclusionThreshold =          experiment_configuration[configkey].get('inclusionThreshold')
    label_map_task.inputs.nonAirRegionMask =            label_map_workflow.lzin.nonAirRegionMask

    label_map_workflow.add(label_map_task)
    label_map_workflow.set_output([
        ("cleanLabelVolume", label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.cleanLabelVolume),
        ("dirtyLabelVolume", label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.dirtyLabelVolume),
    ])
    return label_map_workflow

def make_landmarkInitializer_workflow3(inputFixedLandmarkFilename, inputMovingLandmarkFilename) -> pydra.Workflow:
    from sem_tasks.utilities.brains import BRAINSLandmarkInitializer
    workflow_name = f"landmarkInitializer_workflow3"
    configkey = f'BRAINSLandmarkInitializer3'
    print(f"Making task {workflow_name}")


    landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputFixedLandmarkFilename", "inputMovingLandmarkFilename"], inputFixedLandmarkFilename=inputFixedLandmarkFilename, inputMovingLandmarkFilename=inputMovingLandmarkFilename)
    landmark_initializer_workflow.add(get_parent_directory(name="get_parent_directory", filepath=landmark_initializer_workflow.lzin.inputMovingLandmarkFilename))
    landmark_initializer_workflow.add(make_output_filename(name="outputTransformFilename", before_str="landmarkInitializer_", filename=landmark_initializer_workflow.get_parent_directory.lzout.out, append_str="_to_subject_transform", extension=".h5"))

    landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()
    landmark_initializer_task.inputs.inputFixedLandmarkFilename =   landmark_initializer_workflow.lzin.inputFixedLandmarkFilename
    landmark_initializer_task.inputs.inputMovingLandmarkFilename =   landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
    landmark_initializer_task.inputs.inputWeightFilename =          experiment_configuration[configkey].get('inputWeightFilename')
    landmark_initializer_task.inputs.outputTransformFilename =      landmark_initializer_workflow.outputTransformFilename.lzout.out #experiment_configuration[configkey].get('outputTransformFilename')

    landmark_initializer_workflow.add(landmark_initializer_task)
    landmark_initializer_workflow.set_output([
        ("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename),
        # ("outputTransformFilename2", landmark_initializer_workflow.outputTransformFilename.lzout.out)
        ("atlas_id", landmark_initializer_workflow.get_parent_directory.lzout.out)
    ])

    return landmark_initializer_workflow


def make_roi_workflow3(inputVolume) -> pydra.Workflow:
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

def make_antsRegistration_workflow3(fixed_image, fixed_image_masks, initial_moving_transform, atlas_id) -> pydra.Workflow:
    from pydra.tasks.nipype1.utils import Nipype1Task
    from nipype.interfaces.ants import Registration

    workflow_name = "antsRegistration_workflow3"
    configkey='ANTSRegistration3'
    print(f"Making task {workflow_name}")

    # Create the workflow
    antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform", "atlas_id"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform, atlas_id=atlas_id)
    antsRegistration_workflow.add(make_output_filename(name="make_moving_image", directory=experiment_configuration[configkey].get('moving_image_dir'), parent_dir=antsRegistration_workflow.lzin.atlas_id, filename=experiment_configuration[configkey].get('moving_image_filename')))
    antsRegistration_workflow.add(make_output_filename(name="make_moving_image_masks", directory=experiment_configuration[configkey].get('moving_image_dir'), parent_dir=antsRegistration_workflow.lzin.atlas_id, filename=experiment_configuration[configkey].get('moving_image_masks_filename')))
    antsRegistration_workflow.add(make_output_filename(name="make_output_transform_prefix", before_str=antsRegistration_workflow.lzin.atlas_id, filename=experiment_configuration[configkey].get('output_transform_prefix_suffix')))
    antsRegistration_workflow.add(make_output_filename(name="make_output_warped_image", before_str=antsRegistration_workflow.lzin.atlas_id, filename=experiment_configuration[configkey].get('output_warped_image_suffix')))
    antsRegistration_workflow.add(get_atlas_id(name="get_atlas_id", atlas_id=antsRegistration_workflow.lzin.atlas_id))

    antsRegistration_task = Nipype1Task(Registration())

    antsRegistration_task.inputs.fixed_image =                      antsRegistration_workflow.lzin.fixed_image
    antsRegistration_task.inputs.fixed_image_masks =                antsRegistration_workflow.lzin.fixed_image_masks
    antsRegistration_task.inputs.initial_moving_transform =         antsRegistration_workflow.lzin.initial_moving_transform
    antsRegistration_task.inputs.moving_image =                     antsRegistration_workflow.make_moving_image.lzout.out
    antsRegistration_task.inputs.moving_image_masks =               antsRegistration_workflow.make_moving_image_masks.lzout.out

    antsRegistration_task.inputs.save_state =                       experiment_configuration[configkey].get('save_state')
    antsRegistration_task.inputs.transforms =                       experiment_configuration[configkey].get('transforms')
    antsRegistration_task.inputs.transform_parameters =             experiment_configuration[configkey].get('transform_parameters')
    antsRegistration_task.inputs.number_of_iterations =             experiment_configuration[configkey].get('number_of_iterations')
    antsRegistration_task.inputs.dimension =                        experiment_configuration[configkey].get('dimensionality')
    antsRegistration_task.inputs.write_composite_transform =        experiment_configuration[configkey].get('write_composite_transform')
    antsRegistration_task.inputs.collapse_output_transforms =       experiment_configuration[configkey].get('collapse_output_transforms')
    antsRegistration_task.inputs.verbose =                          experiment_configuration[configkey].get('verbose')
    antsRegistration_task.inputs.initialize_transforms_per_stage =  experiment_configuration[configkey].get('initialize_transforms_per_stage')
    antsRegistration_task.inputs.float =                            experiment_configuration[configkey].get('float')
    antsRegistration_task.inputs.metric =                           experiment_configuration[configkey].get('metric')
    antsRegistration_task.inputs.metric_weight =                    experiment_configuration[configkey].get('metric_weight')
    antsRegistration_task.inputs.radius_or_number_of_bins =         experiment_configuration[configkey].get('radius_or_number_of_bins')
    antsRegistration_task.inputs.sampling_strategy =                experiment_configuration[configkey].get('sampling_strategy')
    antsRegistration_task.inputs.sampling_percentage =              experiment_configuration[configkey].get('sampling_percentage')
    antsRegistration_task.inputs.convergence_threshold =            experiment_configuration[configkey].get('convergence_threshold')
    antsRegistration_task.inputs.convergence_window_size =          experiment_configuration[configkey].get('convergence_window_size')
    antsRegistration_task.inputs.smoothing_sigmas =                 experiment_configuration[configkey].get('smoothing_sigmas')
    antsRegistration_task.inputs.sigma_units =                      experiment_configuration[configkey].get('sigma_units')
    antsRegistration_task.inputs.shrink_factors =                   experiment_configuration[configkey].get('shrink_factors')
    antsRegistration_task.inputs.use_estimate_learning_rate_once =  experiment_configuration[configkey].get('use_estimate_learning_rate_once')
    antsRegistration_task.inputs.use_histogram_matching =           experiment_configuration[configkey].get('use_histogram_matching')
    antsRegistration_task.inputs.winsorize_lower_quantile =         experiment_configuration[configkey].get('winsorize_lower_quantile')
    antsRegistration_task.inputs.winsorize_upper_quantile =         experiment_configuration[configkey].get('winsorize_upper_quantile')

    # Set the variables that set output file names
    antsRegistration_task.inputs.output_transform_prefix =          antsRegistration_workflow.make_output_transform_prefix.lzout.out
    antsRegistration_task.inputs.output_warped_image =              antsRegistration_workflow.make_output_warped_image.lzout.out #experiment_configuration[configkey].get('output_warped_image')
    # antsRegistration_task.inputs.output_inverse_warped_image =      False #    experiment_configuration[configkey].get('output_inverse_warped_image')

    antsRegistration_workflow.add(antsRegistration_task)
    antsRegistration_workflow.set_output([
        ("save_state", antsRegistration_task.lzout.save_state),
        ("composite_transform", antsRegistration_task.lzout.composite_transform),
        ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
        ("warped_image", antsRegistration_task.lzout.warped_image),
        ("atlas_id", antsRegistration_workflow.get_atlas_id.lzout.out)
    ])

    return antsRegistration_workflow

def make_roi_workflow3(inputVolume) -> pydra.Workflow:
    from sem_tasks.segmentation.specialized import BRAINSROIAuto
    workflow_name = "roi_workflow3"
    configkey='BRAINSROIAuto3'
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

def make_antsApplyTransforms_workflow1(reference_image, transform):
    from pydra.tasks.nipype1.utils import Nipype1Task
    from nipype.interfaces.ants import ApplyTransforms

    workflow_name = "antsApplyTransforms_workflow1"
    configkey='ANTSApplyTransforms1'
    print(f"Making task {workflow_name}")

    # Create the workflow
    antsApplyTransforms_workflow = pydra.Workflow(name=workflow_name, input_spec=["reference_image", "transform"], reference_image=reference_image, transform=transform)
    # antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["atlas_id"], atlas_id=atlas_id)

    antsApplyTransforms_workflow.add(make_output_filename(name="input_image", directory=experiment_configuration[configkey].get('input_image_dir'), parent_dir="91300", filename=experiment_configuration[configkey].get('input_image_filename')))
    antsApplyTransforms_workflow.add(make_output_filename(name="output_image", before_str="before", filename=experiment_configuration[configkey].get('output_image_end')))
    antsApplyTransforms_workflow.add(get_atlas_id_from_transform(name="atlas_id", transform=antsApplyTransforms_workflow.transform.lzout.out))
    antsApplyTransforms_workflow.add(get_self(name="get_self1", x=antsApplyTransforms_workflow.input_image.lzout.out))
    antsApplyTransforms_workflow.add(get_self(name="get_self2", x=antsApplyTransforms_workflow.output_image.lzout.out))
    antsApplyTransforms_workflow.add(get_self(name="get_self3", x=antsApplyTransforms_workflow.lzin.reference_image))
    antsApplyTransforms_workflow.add(get_self(name="get_self4", x=antsApplyTransforms_workflow.lzin.transform))

    antsApplyTransforms_task = Nipype1Task(ApplyTransforms())

    antsApplyTransforms_task.inputs.dimension = 3
    antsApplyTransforms_task.inputs.float = False
    antsApplyTransforms_task.inputs.input_image = antsApplyTransforms_workflow.input_image.lzout.out #"/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/91300/wholeBrain_label.nii.gz"
    antsApplyTransforms_task.inputs.interpolation = "MultiLabel"
    antsApplyTransforms_task.inputs.output_image = antsApplyTransforms_workflow.output_image.lzout.out #"91300fswm_2_subj_lbl.nii.gz"
    antsApplyTransforms_task.inputs.reference_image = antsApplyTransforms_workflow.lzin.reference_image #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz"
    antsApplyTransforms_task.inputs.transforms = antsApplyTransforms_workflow.lzin.transform #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5"

    antsApplyTransforms_workflow.add(antsApplyTransforms_task)
    antsApplyTransforms_workflow.set_output([
        ("output_image", antsApplyTransforms_task.lzout.output_image),
    ])

    return antsApplyTransforms_workflow

@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    return list(processed_dict.values())

def copy(cache_path, output_dir):
    if Path(cache_path).is_file():
        out_path = Path(output_dir) / Path(cache_path).name
        print(f"Copying from {cache_path} to {out_path}")
        copyfile(cache_path, out_path)
    else:
        print(f"{cache_path} is not a file")
        out_path = cache_path

    return out_path

# If on same mount point use hard link instead of copy (not windows - look into this)
@pydra.mark.task
def copy_from_cache(cache_path, output_dir, input_data):
    print(cache_path)
    input_filename = Path(input_data.get('t1')).with_suffix('').with_suffix('').name
    file_output_dir = Path(output_dir) / Path(input_filename)
    file_output_dir.mkdir(parents=True, exist_ok=True)
    if cache_path is None:
        return "" # Don't return a cache_path if it is None
    else:
        # If the files to be copied locally are nested in a dictionary, put the values of the dictionary in a list
        if type(cache_path) is dict:
            cache_path_elements = list(cache_path.values())
            cache_path = []
            for cache_path_element in cache_path_elements:
                    cache_path.append(cache_path_element)
        # If the files to be copied are in a list, copy each element of the list
        if type(cache_path) is list:
            output_list = []
            for path in cache_path:
                # If the files to be copied are in a dictionary, copy each value of the dictionary
                if type(path) is dict:
                    for nested_path in list(path.values()):
                        out_path = copy(nested_path, file_output_dir)
                        output_list.append(out_path)
                else:
                    out_path = copy(path, file_output_dir)
                    output_list.append(out_path)
            return output_list
        else:
            cache_path = copy(cache_path, file_output_dir)
    return cache_path

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
source_node = pydra.Workflow(name="source_node", input_spec=["input_data"], cache_dir=experiment_configuration["cache_dir"])
source_node.inputs.input_data = input_data_dictionary["input_data"]
source_node.split("input_data")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

# Get the processing workflow defined in a separate function
processing_node = pydra.Workflow(name="processing_node", input_spec=["input_data"], input_data=source_node.lzin.input_data)
processing_node.add(get_inputs_workflow(my_source_node=processing_node))


processing_node.add(make_bcd_workflow1(inputVolume=processing_node.inputs_workflow.lzout.inputVolume, inputLandmarksEMSP=processing_node.inputs_workflow.lzout.inputLandmarksEMSP))
processing_node.add(make_roi_workflow1(inputVolume=processing_node.bcd_workflow1.lzout.outputResampledVolume))
processing_node.add(make_landmarkInitializer_workflow1(inputMovingLandmarkFilename=processing_node.bcd_workflow1.lzout.outputLandmarksInInputSpace))
processing_node.add(make_landmarkInitializer_workflow2(inputFixedLandmarkFilename=processing_node.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace))
processing_node.add(make_resample_workflow1(inputVolume=processing_node.inputs_workflow.lzout.inputVolume, warpTransform=processing_node.landmarkInitializer_workflow1.lzout.outputTransformFilename))
processing_node.add(make_roi_workflow2(inputVolume=processing_node.roi_workflow1.lzout.outputVolume))
processing_node.add(make_antsRegistration_workflow1(fixed_image=processing_node.roi_workflow1.lzout.outputVolume, fixed_image_masks=processing_node.roi_workflow2.lzout.outputROIMaskVolume, initial_moving_transform=processing_node.landmarkInitializer_workflow2.lzout.outputTransformFilename))
processing_node.add(make_antsRegistration_workflow2(fixed_image=processing_node.roi_workflow1.lzout.outputVolume, fixed_image_masks=processing_node.roi_workflow2.lzout.outputROIMaskVolume, initial_moving_transform=processing_node.antsRegistration_workflow1.lzout.composite_transform))
processing_node.add(make_abc_workflow1(inputVolumes=processing_node.roi_workflow1.lzout.outputVolume, inputT1=processing_node.inputs_workflow.lzout.inputVolume, restoreState=processing_node.antsRegistration_workflow2.lzout.save_state))
processing_node.add(make_resample_workflow2(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow3(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow4(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow5(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow6(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow7(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_resample_workflow8(referenceVolume=processing_node.abc_workflow1.lzout.t1_average, warpTransform=processing_node.abc_workflow1.lzout.atlasToSubjectTransform))
processing_node.add(make_createLabelMapFromProbabilityMaps_workflow1(inputProbabilityVolume=processing_node.abc_workflow1.lzout.posteriors, nonAirRegionMask=processing_node.roi_workflow2.lzout.outputROIMaskVolume))
processing_node.add(make_landmarkInitializer_workflow3(inputMovingLandmarkFilename=experiment_configuration["BRAINSLandmarkInitializer3"].get('inputMovingLandmarkFilename'), inputFixedLandmarkFilename=processing_node.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace).split("inputMovingLandmarkFilename"))
processing_node.add(make_roi_workflow3(inputVolume=processing_node.abc_workflow1.lzout.t1_average))
processing_node.add(make_antsRegistration_workflow3(fixed_image=processing_node.abc_workflow1.lzout.t1_average, fixed_image_masks=processing_node.roi_workflow3.lzout.outputROIMaskVolume, initial_moving_transform=processing_node.landmarkInitializer_workflow3.lzout.outputTransformFilename, atlas_id=processing_node.landmarkInitializer_workflow3.lzout.atlas_id))
processing_node.add(make_antsApplyTransforms_workflow1(reference_image=processing_node.abc_workflow1.lzout.t1_average, transform=processing_node.antsRegistration_workflow3.lzout.inverse_composite_transform)) # reference_image=processing_node.abc_workflow1.t1_average, transform=processing_node.antsRegistration_workflow3.inversCompositeTransform))

processing_node.set_output([
    ("out", processing_node.antsApplyTransforms_workflow1.lzout.output_image),
])


# The sink converts the cached files to output_dir, a location on the local machine
# sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files', 'input_data'], processed_files=processing_node.lzout.all_, input_data=source_node.lzin.input_data)
# sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
# sink_node.add(copy_from_cache(name="copy_from_cache", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out, input_data=sink_node.lzin.input_data).split("cache_path"))
# sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])

source_node.add(processing_node)

# source_node.add(sink_node)

# Set the output of the source node to the same as the output of the sink_node
# source_node.set_output([("output_files", source_node.sink_node.lzout.output_files),])
source_node.set_output([("output_files", source_node.processing_node.lzout.out)])
# source_node.set_output([("output_files", source_node.processing_node.lzout.all_)])



# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)

# Create graphs representing the connections within the pipeline (first in a .dot file then converted to a pdf and png
graph_dir = Path(experiment_configuration['graph_dir'])
processing_node.create_dotfile(type="simple", export=["pdf", "png"], name=graph_dir / Path("processing_simple"))
processing_node.create_dotfile(type="nested", export=["pdf", "png"], name=graph_dir / Path("processing_nested"))
processing_node.create_dotfile(type="detailed", export=["pdf", "png"], name=graph_dir / Path("processing_detailed"))
print("Created the processing pipeline graph visual")

result = source_node.result()
print(result)