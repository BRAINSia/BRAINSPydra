import pydra
from pathlib import Path
from shutil import copyfile
import json
import argparse
# from pydra.utils import fun_write_file_list2dict

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Move echo numbers in fmap BIDS data to JSON sidecars')
    parser.add_argument('config_experimental', type=str, help='Path to the json file for configuring task parameters')
    parser.add_argument('config_environment', type=str, help='Path to the json file for setting environment config parameters')
    parser.add_argument('input_data_dictionary', type=str, help='Path to the json file for input data')
    args = parser.parse_args()

    with open(args.config_experimental) as f:
        experiment_configuration = json.load(f)
    with open(args.config_environment) as f:
        environment_configuration = json.load(f)
    with open(args.input_data_dictionary) as f:
        input_data_dictionary = json.load(f)


    @pydra.mark.task
    def make_filename(filename="", before_str="", append_str="", extension="", directory="", parent_dir=""):
        if filename is None:
            return None
        else:
            # if the input filename is a list, set the filename for each element in the list
            if type(filename) is list:
                new_filename = []
                for f in filename:
                    # If an extension is not specified and the filename has an extension, use the filename's extension(s)
                    if extension == "":
                        extension = "".join(Path(f).suffixes)
                    new_filename.append(f"{Path(Path(directory) / Path(parent_dir) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}")
            else:
                # If an extension is not specified and the filename has an extension, use the filename's extension(s)
                if extension == "":
                    extension = "".join(Path(filename).suffixes)
                new_filename = f"{Path(Path(directory) / Path(parent_dir) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
            return new_filename

    def get_inputs_workflow(my_source_node):
        @pydra.mark.task
        def get_input_field(input_dict: dict, field):
            return input_dict[field]

        get_inputs_workflow = pydra.Workflow(name="inputs_workflow", input_spec=["input_data"], input_data=my_source_node.lzin.input_data)
        # Get the list of t1 files from input_data_dictionary
        get_inputs_workflow.add(get_input_field(name="get_inputVolume", input_dict=get_inputs_workflow.lzin.input_data, field="t1"))
        # Get the list of landmark files from input_data_dictionary
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

        # Define the workflow and its lazy inputs
        bcd_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume", "inputLandmarksEMSP"], inputVolume=inputVolume, inputLandmarksEMSP=inputLandmarksEMSP)

        # Create the pydra-sem generated task
        bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        bcd_task.inputs.inputVolume =                       bcd_workflow.lzin.inputVolume
        bcd_task.inputs.inputLandmarksEMSP =                bcd_workflow.lzin.inputLandmarksEMSP
        bcd_task.inputs.inputTemplateModel =                experiment_configuration[configkey].get('inputTemplateModel')
        bcd_task.inputs.interpolationMode =                 experiment_configuration[configkey].get('interpolationMode')
        bcd_task.inputs.LLSModel =                          experiment_configuration[configkey].get('LLSModel')
        bcd_task.inputs.acLowerBound =                      experiment_configuration[configkey].get('acLowerBound')
        bcd_task.inputs.atlasLandmarkWeights =              experiment_configuration[configkey].get('atlasLandmarkWeights')
        bcd_task.inputs.atlasLandmarks =                    experiment_configuration[configkey].get('atlasLandmarks')
        bcd_task.inputs.houghEyeDetectorMode =              experiment_configuration[configkey].get('houghEyeDetectorMode')
        bcd_task.inputs.outputLandmarksInInputSpace =       experiment_configuration[configkey].get('outputLandmarksInInputSpace')
        bcd_task.inputs.outputResampledVolume =             experiment_configuration[configkey].get('outputResampledVolume')
        bcd_task.inputs.outputTransform =                   experiment_configuration[configkey].get('outputTransform')
        bcd_task.inputs.outputLandmarksInACPCAlignedSpace = experiment_configuration[configkey].get('outputLandmarksInACPCAlignedSpace')
        bcd_task.inputs.writeBranded2DImage =               experiment_configuration[configkey].get('writeBranded2DImage')
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

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
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


        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputMovingLandmarkFilename"], inputMovingLandmarkFilename=inputMovingLandmarkFilename)

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
        landmark_initializer_task.inputs.inputMovingLandmarkFilename =  landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
        landmark_initializer_task.inputs.inputFixedLandmarkFilename =   experiment_configuration[configkey].get('inputFixedLandmarkFilename')
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


        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputFixedLandmarkFilename"], inputFixedLandmarkFilename=inputFixedLandmarkFilename)

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
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

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume", "warpTransform"], inputVolume=inputVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.inputVolume =          resample_workflow.lzin.inputVolume
        resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_roi_workflow2(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto
        workflow_name = "roi_workflow2"
        configkey='BRAINSROIAuto2'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
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

        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform)

        if environment_configuration['set_threads']:
            # Set the number of threads to be used by ITK
            antsRegistration_task = Registration()
            antsRegistration_task.set_default_num_threads(experiment_configuration["num_threads"])
            antsRegistration_task.inputs.num_threads = experiment_configuration["num_threads"]
            antsRegistration_task = Nipype1Task(antsRegistration_task)
        else:
            # Use the default number of threads (1)
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


        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform)

        if environment_configuration['set_threads']:
            # Set the number of threads to be used by ITK
            antsRegistration_task = Registration()
            antsRegistration_task.set_default_num_threads(experiment_configuration["num_threads"])
            antsRegistration_task.inputs.num_threads = experiment_configuration["num_threads"]
            antsRegistration_task = Nipype1Task(antsRegistration_task)
        else:
            # Use the default number of threads (1)
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


    def make_abc_workflow1(inputVolumes, inputT1, restoreState) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSABC

        @pydra.mark.task
        def get_t1_average(outputs):
            return outputs[0]

        @pydra.mark.task
        def get_posteriors(outputs):
            return outputs[1:]

        workflow_name = "abc_workflow1"
        configkey='BRAINSABC1'
        print(f"Making task {workflow_name}")


        # Define the workflow and its lazy inputs
        abc_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolumes", "inputT1", "restoreState"], inputVolumes=inputVolumes, inputT1=inputT1, restoreState=restoreState)
        abc_workflow.add(make_filename(name="outputVolumes", filename=abc_workflow.lzin.inputT1, append_str="_corrected", extension=".nii.gz"))

        # Create the pydra-sem generated task
        abc_task = BRAINSABC(name="BRAINSABC", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        abc_task.inputs.inputVolumes =                  abc_workflow.lzin.inputVolumes #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" # # # #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/Cropped_BCD_ACPC_Aligned.nii.gz" #  #abc_workflow.lzin.inputVolumes
        abc_task.inputs.restoreState =                  abc_workflow.lzin.restoreState #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" # #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #"/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #"/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/SavedInternalSyNState.h5" #
        abc_task.inputs.outputVolumes =                 abc_workflow.outputVolumes.lzout.out #"sub-052823_ses-43817_run-002_T1w_corrected.nii.gz" # #"sub-052823_ses-43817_run-002_T1w_corrected.nii.gz" #

        abc_task.inputs.atlasDefinition =               experiment_configuration[configkey].get('atlasDefinition')
        abc_task.inputs.atlasToSubjectTransform =       experiment_configuration[configkey].get('atlasToSubjectTransform')
        abc_task.inputs.atlasToSubjectTransformType =   experiment_configuration[configkey].get('atlasToSubjectTransformType')
        abc_task.inputs.debuglevel =                    experiment_configuration[configkey].get('debuglevel')
        abc_task.inputs.filterIteration =               experiment_configuration[configkey].get('filterIteration')
        abc_task.inputs.filterMethod =                  experiment_configuration[configkey].get('filterMethod')
        abc_task.inputs.inputVolumeTypes =              experiment_configuration[configkey].get('inputVolumeTypes')
        abc_task.inputs.interpolationMode =             experiment_configuration[configkey].get('interpolationMode')
        abc_task.inputs.maxBiasDegree =                 experiment_configuration[configkey].get('maxBiasDegree')
        abc_task.inputs.maxIterations =                 experiment_configuration[configkey].get('maxIterations')
        abc_task.inputs.posteriorTemplate =             experiment_configuration[configkey].get('POSTERIOR_%s.nii.gz')
        abc_task.inputs.purePlugsThreshold =            experiment_configuration[configkey].get('purePlugsThreshold')
        abc_task.inputs.saveState =                     experiment_configuration[configkey].get('saveState')
        abc_task.inputs.useKNN =                        experiment_configuration[configkey].get('useKNN')
        abc_task.inputs.outputFormat =                  experiment_configuration[configkey].get('outputFormat')
        abc_task.inputs.outputDir =                     experiment_configuration[configkey].get('outputDir')
        abc_task.inputs.outputDirtyLabels =             experiment_configuration[configkey].get('outputDirtyLabels')
        abc_task.inputs.outputLabels =                  experiment_configuration[configkey].get('outputLabels')
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
        ])

        return abc_workflow

    def make_resample_workflow2(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow2"
        configkey='BRAINSResample2'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow3(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow3"
        configkey='BRAINSResample3'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow4(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow4"
        configkey='BRAINSResample4'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume =      resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform =        resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow5(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow5"
        configkey='BRAINSResample5'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow6(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow6"
        configkey='BRAINSResample6'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow7(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow7"
        configkey='BRAINSResample7'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_resample_workflow8(referenceVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample
        workflow_name = "resample_workflow8"
        configkey='BRAINSResample8'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(name=workflow_name, input_spec=["referenceVolume", "warpTransform"], referenceVolume=referenceVolume, warpTransform=warpTransform)

        # Create the pydra-sem generated task
        resample_task = BRAINSResample("BRAINSResample", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume =          experiment_configuration[configkey].get("inputVolume")
        resample_task.inputs.interpolationMode =    experiment_configuration[configkey].get("interpolationMode")
        resample_task.inputs.outputVolume =         experiment_configuration[configkey].get("outputVolume")
        resample_task.inputs.pixelType =            experiment_configuration[configkey].get("pixelType")

        resample_workflow.add(resample_task)
        resample_workflow.set_output([("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)])

        return resample_workflow

    def make_createLabelMapFromProbabilityMaps_workflow1(inputProbabilityVolume, nonAirRegionMask) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSCreateLabelMapFromProbabilityMaps
        workflow_name = "createLabelMapFromProbabilityMaps_workflow1"
        configkey='BRAINSCreateLabelMapFromProbabilityMaps1'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        label_map_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputProbabilityVolume", "nonAirRegionMask"], inputProbabilityVolume=inputProbabilityVolume, nonAirRegionMask=nonAirRegionMask)

        # Create the pydra-sem generated task
        label_map_task = BRAINSCreateLabelMapFromProbabilityMaps(name="BRAINSCreateLabelMapFromProbabilityMaps", executable=experiment_configuration[configkey]['executable']).get_task()

        # Set task inputs
        label_map_task.inputs.inputProbabilityVolume =      label_map_workflow.lzin.inputProbabilityVolume
        label_map_task.inputs.nonAirRegionMask =            label_map_workflow.lzin.nonAirRegionMask
        label_map_task.inputs.cleanLabelVolume =            experiment_configuration[configkey].get('cleanLabelVolume')
        label_map_task.inputs.dirtyLabelVolume =            experiment_configuration[configkey].get('dirtyLabelVolume')
        label_map_task.inputs.foregroundPriors =            experiment_configuration[configkey].get('foregroundPriors')
        label_map_task.inputs.priorLabelCodes =             experiment_configuration[configkey].get('priorLabelCodes')
        label_map_task.inputs.inclusionThreshold =          experiment_configuration[configkey].get('inclusionThreshold')

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

        @pydra.mark.task
        def get_parent_directory(filepath):
            return Path(filepath).parent.name

        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputFixedLandmarkFilename", "inputMovingLandmarkFilename"], inputFixedLandmarkFilename=inputFixedLandmarkFilename, inputMovingLandmarkFilename=inputMovingLandmarkFilename)

        landmark_initializer_workflow.add(get_parent_directory(name="get_parent_directory", filepath=landmark_initializer_workflow.lzin.inputMovingLandmarkFilename))
        landmark_initializer_workflow.add(make_filename(name="outputTransformFilename", before_str="landmarkInitializer_", filename=landmark_initializer_workflow.get_parent_directory.lzout.out, append_str="_to_subject_transform", extension=".h5"))

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(name="BRAINSLandmarkInitializer", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
        landmark_initializer_task.inputs.inputFixedLandmarkFilename =   landmark_initializer_workflow.lzin.inputFixedLandmarkFilename
        landmark_initializer_task.inputs.inputMovingLandmarkFilename =   landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
        landmark_initializer_task.inputs.outputTransformFilename =      landmark_initializer_workflow.outputTransformFilename.lzout.out #experiment_configuration[configkey].get('outputTransformFilename')
        landmark_initializer_task.inputs.inputWeightFilename =          experiment_configuration[configkey].get('inputWeightFilename')

        landmark_initializer_workflow.add(landmark_initializer_task)
        landmark_initializer_workflow.set_output([
            ("outputTransformFilename", landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename),
            ("atlas_id", landmark_initializer_workflow.get_parent_directory.lzout.out)
        ])

        return landmark_initializer_workflow


    def make_roi_workflow3(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto
        workflow_name = "roi_workflow2"
        configkey='BRAINSROIAuto2'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
        roi_task.inputs.inputVolume =           roi_workflow.lzin.inputVolume
        roi_task.inputs.ROIAutoDilateSize =     experiment_configuration[configkey].get('ROIAutoDilateSize')
        roi_task.inputs.outputROIMaskVolume =   experiment_configuration[configkey].get('outputROIMaskVolume')

        roi_workflow.add(roi_task)
        roi_workflow.set_output([
            ("outputROIMaskVolume", roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume),
        ])

        return roi_workflow

    def make_antsRegistration_workflow3(fixed_image, fixed_image_masks, initial_moving_transform) -> pydra.Workflow:

        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import Registration

        @pydra.mark.task
        def get_atlas_id_from_landmark_initializer_transform(landmark_initializer_transform):
            atlas_id = Path(landmark_initializer_transform).name.split("_")[1]
            return atlas_id

        workflow_name = "antsRegistration_workflow3"
        configkey='ANTSRegistration3'
        print(f"Making task {workflow_name}")


        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(name=workflow_name, input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"], fixed_image=fixed_image, fixed_image_masks=fixed_image_masks, initial_moving_transform=initial_moving_transform)

        antsRegistration_workflow.add(get_atlas_id_from_landmark_initializer_transform(name="atlas_id", landmark_initializer_transform=antsRegistration_workflow.lzin.initial_moving_transform))

        antsRegistration_workflow.add(make_filename(name="make_moving_image", directory=experiment_configuration[configkey].get('moving_image_dir'), parent_dir=antsRegistration_workflow.atlas_id.lzout.out, filename=experiment_configuration[configkey].get('moving_image_filename')))
        antsRegistration_workflow.add(make_filename(name="make_moving_image_masks", directory=experiment_configuration[configkey].get('moving_image_dir'), parent_dir=antsRegistration_workflow.atlas_id.lzout.out, filename=experiment_configuration[configkey].get('moving_image_masks_filename')))
        antsRegistration_workflow.add(make_filename(name="make_output_transform_prefix", before_str=antsRegistration_workflow.atlas_id.lzout.out, filename=experiment_configuration[configkey].get('output_transform_prefix_suffix')))
        antsRegistration_workflow.add(make_filename(name="make_output_warped_image", before_str=antsRegistration_workflow.atlas_id.lzout.out, filename=experiment_configuration[configkey].get('output_warped_image_suffix')))

        if environment_configuration['set_threads']:
            # Set the number of threads to be used by ITK
            antsRegistration_task = Registration()
            antsRegistration_task.set_default_num_threads(1)
            antsRegistration_task.inputs.num_threads = 1
            antsRegistration_task = Nipype1Task(antsRegistration_task)
        else:
            # Use the default number of threads (1)
            antsRegistration_task = Nipype1Task(Registration())

        # Set task inputs
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

        antsRegistration_workflow.add(antsRegistration_task)
        antsRegistration_workflow.set_output([
            ("save_state", antsRegistration_task.lzout.save_state),
            ("composite_transform", antsRegistration_task.lzout.composite_transform),
            ("inverse_composite_transform", antsRegistration_task.lzout.inverse_composite_transform),
            ("warped_image", antsRegistration_task.lzout.warped_image),
        ])

        return antsRegistration_workflow

    def make_roi_workflow3(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto
        workflow_name = "roi_workflow3"
        configkey='BRAINSROIAuto3'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(name=workflow_name, input_spec=["inputVolume"], inputVolume=inputVolume)

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto("BRAINSROIAuto", executable=experiment_configuration[configkey].get('executable')).get_task()

        # Set task inputs
        roi_task.inputs.inputVolume =           roi_workflow.lzin.inputVolume
        roi_task.inputs.ROIAutoDilateSize =     experiment_configuration[configkey].get('ROIAutoDilateSize')
        roi_task.inputs.outputROIMaskVolume =   experiment_configuration[configkey].get('outputROIMaskVolume')

        roi_workflow.add(roi_task)
        roi_workflow.set_output([
            ("outputROIMaskVolume", roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume),
        ])

        return roi_workflow

    def make_antsApplyTransforms_workflow(index, output_image_end, reference_image, transform):
        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import ApplyTransforms

        @pydra.mark.task
        def get_atlas_id_from_transform(transform):
            # From 68653_ToSubjectPreJointFusion_SyNComposite.h5 get 68653
            atlas_id = Path(transform).name.split("_")[0]
            return atlas_id

        workflow_name = f"antsApplyTransforms_workflow{index}"
        configkey=f'ANTSApplyTransforms{index}'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsApplyTransforms_workflow = pydra.Workflow(name=workflow_name, input_spec=["reference_image", "transform"], reference_image=reference_image, transform=transform)

        antsApplyTransforms_workflow.add(get_atlas_id_from_transform(name="atlas_id", transform=antsApplyTransforms_workflow.lzin.transform))

        antsApplyTransforms_workflow.add(make_filename(name="input_image", directory=experiment_configuration[configkey].get('input_image_dir'), parent_dir=antsApplyTransforms_workflow.atlas_id.lzout.out, filename=experiment_configuration[configkey].get('input_image_filename')))
        antsApplyTransforms_workflow.add(make_filename(name="output_image", before_str=antsApplyTransforms_workflow.atlas_id.lzout.out, filename=output_image_end))

        if environment_configuration['set_threads']:
            # Set the number of threads to be used by ITK
            antsApplyTransforms_task = ApplyTransforms()
            antsApplyTransforms_task.set_default_num_threads(experiment_configuration["num_threads"])
            antsApplyTransforms_task.inputs.num_threads = experiment_configuration["num_threads"]
            antsApplyTransforms_task = Nipype1Task(antsApplyTransforms_task)
        else:
            # Use the default number of threads (1)
            antsApplyTransforms_task = Nipype1Task(ApplyTransforms())

        # Set task inputs
        antsApplyTransforms_task.inputs.input_image = antsApplyTransforms_workflow.input_image.lzout.out
        antsApplyTransforms_task.inputs.output_image = antsApplyTransforms_workflow.output_image.lzout.out
        antsApplyTransforms_task.inputs.reference_image = antsApplyTransforms_workflow.lzin.reference_image
        antsApplyTransforms_task.inputs.transforms = antsApplyTransforms_workflow.lzin.transform
        antsApplyTransforms_task.inputs.dimension = experiment_configuration[configkey].get('dimension')
        antsApplyTransforms_task.inputs.float = experiment_configuration[configkey].get('float')
        antsApplyTransforms_task.inputs.interpolation = experiment_configuration[configkey].get('interpolation')

        antsApplyTransforms_workflow.add(antsApplyTransforms_task)
        antsApplyTransforms_workflow.set_output([
            ("output_image", antsApplyTransforms_task.lzout.output_image),
        ])

        return antsApplyTransforms_workflow

    def make_antsJointFusion_workflow1(atlas_image, atlas_segmentation_image, target_image, mask_image):

        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import JointFusion

        @pydra.mark.task
        def to_list(value):
            return [value]

        workflow_name = f"antsJointFusion_workflow1"
        configkey=f'ANTSJointFusion1'
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsJointFusion_workflow = pydra.Workflow(name=workflow_name, input_spec=["atlas_image", "atlas_segmentation_image", "target_image", "mask_image"], atlas_image=atlas_image, atlas_segmentation_image=atlas_segmentation_image, target_image=target_image, mask_image=mask_image)
        antsJointFusion_workflow.add(to_list(name="to_list", value=antsJointFusion_workflow.lzin.target_image))

        if environment_configuration['set_threads']:
            # Set the number of threads to be used by ITK
            antsJointFusion_task = JointFusion()
            antsJointFusion_task.set_default_num_threads(1)
            antsJointFusion_task.inputs.num_threads = 1
            antsJointFusion_task = Nipype1Task(antsJointFusion_task)
        else:
            # Use the default number of threads (1)
            antsJointFusion_task = Nipype1Task(JointFusion())

        antsJointFusion_task.inputs.atlas_image =               antsJointFusion_workflow.lzin.atlas_image
        antsJointFusion_task.inputs.atlas_segmentation_image =  antsJointFusion_workflow.lzin.atlas_segmentation_image
        antsJointFusion_task.inputs.mask_image =                antsJointFusion_workflow.lzin.mask_image
        antsJointFusion_task.inputs.target_image =              antsJointFusion_workflow.to_list.lzout.out
        antsJointFusion_task.inputs.alpha =                     experiment_configuration[configkey].get('alpha')
        antsJointFusion_task.inputs.beta =                      experiment_configuration[configkey].get('beta')
        antsJointFusion_task.inputs.dimension =                 experiment_configuration[configkey].get('dimension')
        antsJointFusion_task.inputs.out_label_fusion =          experiment_configuration[configkey].get('out_label_fusion')
        antsJointFusion_task.inputs.search_radius =             experiment_configuration[configkey].get('search_radius')
        antsJointFusion_task.inputs.verbose =                   experiment_configuration[configkey].get('verbose')

        antsJointFusion_workflow.add(antsJointFusion_task)
        antsJointFusion_workflow.set_output([
            ("out_label_fusion", antsJointFusion_task.lzout.out_label_fusion)
        ])

        return antsJointFusion_workflow

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
        print(f"\n\n\n{cache_path}\n\n\n")
        input_filename = Path(input_data.get('t1')).with_suffix('').with_suffix('').name
        file_output_dir = Path(output_dir) / Path(input_filename)
        file_output_dir.mkdir(parents=True, exist_ok=True)
        if cache_path is None:
            return "" # Don't return a cache_path if it is None
        else:
            # If the files to be copied locally are nested in a dictionary, put the values of the dictionary in a list
            if type(cache_path) is dict:
                print("\n\nHere\n\n")
                print(f"cache_path.values(): {cache_path.values()}")

                print(type(list(cache_path.values())[0]))
                print(list(cache_path.values())[0])
                if type(list(cache_path.values())[0]) is list:
                    cache_path_list = []
                    print("Here4")
                    print(f"list(cache_path.values()): {list(cache_path.values())}")
                    for task_list in list(cache_path.values()):
                        print("Here3")
                        for task_dict in task_list:
                            print("Here5")
                            print(task_dict)
                            print(task_dict.values())
                            for file in list(task_dict.values()):
                                cache_path_list.append(file)
                elif type(list(cache_path.values())[0]) is dict:
                    cache_path_list = []
                    for task_ele in list(cache_path.values()):
                        print("Here6")
                        # print(task_dict)
                        if type(task_ele) is list:
                            for task_dict in task_ele:
                                print("Here5")
                                print(task_dict)
                                print(task_dict.values())
                                for file in list(task_dict.values()):
                                    cache_path_list.append(file)
                        else:
                            # print(task_dict.values())
                            for file in list(task_ele.values()):
                                cache_path_list.append(file)
                else:
                    print()
                    cache_path_elements = list(cache_path.values())
                    print(cache_path_elements)
                    cache_path_list = []
                    for cache_path_element in cache_path_elements:
                            cache_path_list.append(cache_path_element)
                cache_path = cache_path_list
                print(f"cache_path is now: {cache_path}")
            # If the files to be copied are in a list, copy each element of the list
            if type(cache_path) is list:
                output_list = []
                for path in cache_path:
                    # If the files to be copied are in a dictionary, copy each value of the dictionary
                    if type(path) is dict:
                        for nested_path in list(path.values()):
                            out_path = copy(nested_path, file_output_dir)
                            output_list.append(out_path)
                    elif type(path) is list:
                        for nested_path in path:
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

    # Make the processing workflow to take the input data, process it, and pass the processed data to the sink_node
    processing_node = pydra.Workflow(name="processing_node", input_spec=["input_data"], input_data=source_node.lzin.input_data)


    # Fill the processing node with BRAINS and ANTs applications
    prejointFusion_node = pydra.Workflow(name="prejointFusion_node", input_spec=["input_data"], input_data=processing_node.lzin.input_data)
    prejointFusion_node.add(get_inputs_workflow(my_source_node=prejointFusion_node))
    prejointFusion_node.add(make_bcd_workflow1(inputVolume=prejointFusion_node.inputs_workflow.lzout.inputVolume, inputLandmarksEMSP=prejointFusion_node.inputs_workflow.lzout.inputLandmarksEMSP))
    prejointFusion_node.add(make_roi_workflow1(inputVolume=prejointFusion_node.bcd_workflow1.lzout.outputResampledVolume))
    prejointFusion_node.add(make_landmarkInitializer_workflow1(inputMovingLandmarkFilename=prejointFusion_node.bcd_workflow1.lzout.outputLandmarksInInputSpace))
    prejointFusion_node.add(make_landmarkInitializer_workflow2(inputFixedLandmarkFilename=prejointFusion_node.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace))
    prejointFusion_node.add(make_resample_workflow1(inputVolume=prejointFusion_node.inputs_workflow.lzout.inputVolume, warpTransform=prejointFusion_node.landmarkInitializer_workflow1.lzout.outputTransformFilename))
    prejointFusion_node.add(make_roi_workflow2(inputVolume=prejointFusion_node.roi_workflow1.lzout.outputVolume))
    prejointFusion_node.add(make_antsRegistration_workflow1(fixed_image=prejointFusion_node.roi_workflow1.lzout.outputVolume, fixed_image_masks=prejointFusion_node.roi_workflow2.lzout.outputROIMaskVolume, initial_moving_transform=prejointFusion_node.landmarkInitializer_workflow2.lzout.outputTransformFilename))
    prejointFusion_node.add(make_antsRegistration_workflow2(fixed_image=prejointFusion_node.roi_workflow1.lzout.outputVolume, fixed_image_masks=prejointFusion_node.roi_workflow2.lzout.outputROIMaskVolume, initial_moving_transform=prejointFusion_node.antsRegistration_workflow1.lzout.composite_transform))
    prejointFusion_node.add(make_abc_workflow1(inputVolumes=prejointFusion_node.roi_workflow1.lzout.outputVolume, inputT1=prejointFusion_node.inputs_workflow.lzout.inputVolume, restoreState=prejointFusion_node.antsRegistration_workflow2.lzout.save_state))
    prejointFusion_node.add(make_resample_workflow2(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow3(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow4(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow5(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow6(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow7(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_resample_workflow8(referenceVolume=prejointFusion_node.abc_workflow1.lzout.t1_average, warpTransform=prejointFusion_node.abc_workflow1.lzout.atlasToSubjectTransform))
    prejointFusion_node.add(make_createLabelMapFromProbabilityMaps_workflow1(inputProbabilityVolume=prejointFusion_node.abc_workflow1.lzout.posteriors, nonAirRegionMask=prejointFusion_node.roi_workflow2.lzout.outputROIMaskVolume))
    prejointFusion_node.add(make_landmarkInitializer_workflow3(inputMovingLandmarkFilename=experiment_configuration["BRAINSLandmarkInitializer3"].get('inputMovingLandmarkFilename'), inputFixedLandmarkFilename=prejointFusion_node.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace).split("inputMovingLandmarkFilename"))
    prejointFusion_node.add(make_roi_workflow3(inputVolume=prejointFusion_node.abc_workflow1.lzout.t1_average))
    # prejointFusion_node.add(make_antsRegistration_workflow3(fixed_image=prejointFusion_node.abc_workflow1.lzout.t1_average, fixed_image_masks=prejointFusion_node.roi_workflow3.lzout.outputROIMaskVolume, initial_moving_transform=prejointFusion_node.landmarkInitializer_workflow3.lzout.outputTransformFilename))
    # prejointFusion_node.add(make_antsApplyTransforms_workflow(index=1, output_image_end=experiment_configuration["ANTSApplyTransforms1"].get('output_image_end'), reference_image=prejointFusion_node.abc_workflow1.lzout.t1_average, transform=prejointFusion_node.antsRegistration_workflow3.lzout.inverse_composite_transform))
    # prejointFusion_node.add(make_antsApplyTransforms_workflow(index=2, output_image_end=experiment_configuration["ANTSApplyTransforms2"].get('output_image_end'), reference_image=prejointFusion_node.abc_workflow1.lzout.t1_average, transform=prejointFusion_node.antsRegistration_workflow3.lzout.inverse_composite_transform))
    # Combine the results of the processing to this point into lists as input to JointFusion
    prejointFusion_node.set_output([
        ("bcd_workflow1"                              , prejointFusion_node.bcd_workflow1.lzout.all_                         ),
        ("roi_workflow1"                              , prejointFusion_node.roi_workflow1.lzout.all_                         ),
        ("landmarkInitializer_workflow1"              , prejointFusion_node.landmarkInitializer_workflow1.lzout.all_         ),
        ("landmarkInitializer_workflow2"              , prejointFusion_node.landmarkInitializer_workflow2.lzout.all_         ),
        ("resample_workflow1"                         , prejointFusion_node.resample_workflow1.lzout.all_                    ),
        ("roi_workflow2"                              , prejointFusion_node.roi_workflow2.lzout.all_                         ),
        ("antsRegistration_workflow1"                 , prejointFusion_node.antsRegistration_workflow1.lzout.all_            ),
        ("antsRegistration_workflow2"                 , prejointFusion_node.antsRegistration_workflow2.lzout.all_            ),
        ("abc_workflow1"                              , prejointFusion_node.abc_workflow1.lzout.all_                         ),
        ("resample_workflow2"                         , prejointFusion_node.resample_workflow2.lzout.all_                    ),
        ("resample_workflow3"                         , prejointFusion_node.resample_workflow3.lzout.all_                    ),
        ("resample_workflow4"                         , prejointFusion_node.resample_workflow4.lzout.all_                    ),
        ("resample_workflow5"                         , prejointFusion_node.resample_workflow5.lzout.all_                    ),
        ('resample_workflow6'                         , prejointFusion_node.resample_workflow6.lzout.all_                    ),
        ("resample_workflow7"                         , prejointFusion_node.resample_workflow7.lzout.all_                    ),
        ("resample_workflow8"                         , prejointFusion_node.resample_workflow8.lzout.all_                    ),
        ("createLabelMapFromProbabilityMaps_workflow1", prejointFusion_node.createLabelMapFromProbabilityMaps_workflow1.lzout.all_),
        ("landmarkInitializer_workflow3"              , prejointFusion_node.landmarkInitializer_workflow3.lzout.all_         ),
        ("roi_workflow3"                              , prejointFusion_node.roi_workflow3.lzout.all_                         ),
        # ("antsRegistration_workflow3"                 , prejointFusion_node.antsRegistration_workflow3.lzout.all_            ),
        # ("antsApplyTransforms_workflow1"              , prejointFusion_node.antsApplyTransforms_workflow1.lzout.all_         ),
        # ('antsApplyTransforms_workflow2'              , prejointFusion_node.antsApplyTransforms_workflow2.lzout.all_         ),
        # ("atlas_image", prejointFusion_node.antsRegistration_workflow3.lzout.warped_image),
        # ("atlas_segmentation_image", prejointFusion_node.antsApplyTransforms_workflow2.lzout.output_image),
        # ("target_image", prejointFusion_node.abc_workflow1.lzout.t1_average),
        # ("mask_image", prejointFusion_node.roi_workflow2.lzout.outputROIMaskVolume),
    ])

    # jointFusion_node = pydra.Workflow(name="jointFusion_node", input_spec=["atlas_image", "atlas_segmentation_image", "target_image", "mask_image"], atlas_image = prejointFusion_node.lzout.atlas_image, atlas_segmentation_image =  prejointFusion_node.lzout.atlas_segmentation_image, target_image = prejointFusion_node.lzout.target_image, mask_image = prejointFusion_node.lzout.mask_image)
    # jointFusion_node.add(make_antsJointFusion_workflow1(atlas_image=jointFusion_node.lzin.atlas_image, atlas_segmentation_image=jointFusion_node.lzin.atlas_segmentation_image, target_image=jointFusion_node.lzin.target_image, mask_image=jointFusion_node.lzin.mask_image))
    # jointFusion_node.set_output([("jointFusion_out", jointFusion_node.antsJointFusion_workflow1.lzout.out_label_fusion)])

    processing_node.add(prejointFusion_node)
    # processing_node.add(jointFusion_node)
    processing_node.set_output([("prejointFusion_out", processing_node.prejointFusion_node.lzout.all_),
                                # ("prejointFusion_out2", processing_node.prejointFusion_node.lzout.all_),
                                # ("jointFusion_out", processing_node.jointFusion_node.lzout.all_)
                                ])

    # The sink converts the cached files to output_dir, a location on the local machine
    # sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files', 'input_data'], processed_files=processing_node.lzout.all_, input_data=source_node.lzin.input_data, output_dir=experiment_configuration["output_dir"])
    # sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
    # # sink_node.add(fun_)
    # # sink_node.add(copy_from_cache(name="copy_from_cache19", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_processed_outputs.lzout.out, input_data=sink_node.lzin.input_data).split("cache_path"))
    # # sink_node.add(get_processed_outputs(name="get_post_processed_outputs", processed_dict=sink_node.lzin.post_processed_files))
    # sink_node.add(copy_from_cache(name="copy_from_cache2", output_dir=experiment_configuration['output_dir'], cache_path=sink_node.get_post_processed_outputs.lzout.out, input_data=sink_node.lzin.input_data).split("cache_path"))
    # sink_node.set_output([
    #     ("processing_node_out", sink_node.lzin.processed_files)
    #     # ("pipline_output", sink_node.copy_from_cache19.lzout.out),
    #     # ("output_files2", sink_node.copy_from_cache2.lzout.out)
    # ])





    source_node.add(processing_node)
    source_node.add(prejointFusion_node)
    # source_node.add(sink_node2)
    # source_node.add(jointFusion_node)

    # source_node.add(sink_node)

    # Set the output of the source node to the same as the output of the sink_node
    # source_node.set_output([("output_files", source_node.sink_node.lzout.pipline_output),])
    # source_node.set_output([("output_files", source_node.sink_node.lzout.files_out)])
    source_node.set_output([("out", source_node.processing_node.lzout.all_)])

    # source_node.output_dir = experiment_configuration['output_dir']
    # Run the entire workflow
    with pydra.Submitter(plugin="cf") as sub:
        sub(source_node)
        # sub(sink_node2)



    # Create graphs representing the connections within the pipeline (first in a .dot file then converted to a pdf and png
    def make_graphs(node: pydra.Workflow):
        graph_dir = Path(experiment_configuration['graph_dir'])
        graph_dir.mkdir(parents=True, exist_ok=True)
        node.create_dotfile(type="simple", export=["pdf", "png"], name=graph_dir / Path(f"{node.name}_simple"))
        node.create_dotfile(type="nested", export=["pdf", "png"], name=graph_dir / Path(f"{node.name}_nested"))
        node.create_dotfile(type="detailed", export=["pdf", "png"], name=graph_dir / Path(f"{node.name}_detailed"))
        print(f"Created the {node.name} graph visual")

    make_graphs(prejointFusion_node)
    # make_graphs(jointFusion_node)
    make_graphs(processing_node)

    result = source_node.result()
    print(result)

    print(f"processing node output_dir: {processing_node.output_dir}")
    print(f"output_dir: {source_node.output_dir}")


    @pydra.mark.task
    def copy(source_output_dir):
        print(f"output_dir in sink: {source_output_dir}")
        p = Path(source_output_dir)
        for cache_filepath in p.glob("**/[!_]*"):

            # if Path(cache_path).is_file():
            #     out_path = Path(output_dir) / Path(cache_path).name
            #     print(f"Copying from {cache_path} to {out_path}")
            #     copyfile(cache_path, out_path)


            output_directory = Path(experiment_configuration["output_dir"])
            output_directory.mkdir(parents=True, exist_ok=True)
            output_filepath = Path(output_directory) / Path(cache_filepath).name
            print(f"Copying {cache_filepath} to {output_filepath}")
            print(type(cache_filepath))
            print(type(output_filepath))
            output_filepath.link_to(cache_filepath)
            # copyfile(cache_filepath, output_filepath)
            # if environment_configuration['hard_links']:
            #     output_filepath.link_to(cache_filepath)
            #     print(f"Hard linked {cache_filepath} to {output_filepath}")
            # else:
            #     copyfile(cache_filepath, output_filepath)
            #     print(f"Copied {cache_filepath} to {output_filepath}")


    # def copy(cache_path, output_dir):
    #     if Path(cache_path).is_file():
    #         out_path = Path(output_dir) / Path(cache_path).name
    #         print(f"Copying from {cache_path} to {out_path}")
    #         copyfile(cache_path, out_path)
    #     else:
    #         print(f"{cache_path} is not a file")
    #         out_path = cache_path
    #
    #     return out_path


    sink_node2 = pydra.Workflow(name="sink_node", input_spec=["output_directory"], output_directory=source_node.output_dir)
    sink_node2.add(copy(name="copy4", source_output_dir=sink_node2.lzin.output_directory).split("source_output_dir"))
    sink_node2.set_output([("files_out", sink_node2.copy4.lzout.out)])

    with pydra.Submitter(plugin="cf") as sub:
        sub(sink_node2)