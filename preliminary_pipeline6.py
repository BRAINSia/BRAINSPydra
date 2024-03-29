import pydra
from pathlib import Path
from shutil import copyfile
import json
import argparse
import pickle
from dask.distributed import Client, LocalCluster
import time
from pydra.engine.submitter import get_runnable_tasks
import attr
from pydra import ShellCommandTask


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Move echo numbers in fmap BIDS data to JSON sidecars"
    )
    parser.add_argument(
        "config_experimental",
        type=str,
        help="Path to the json file for configuring task parameters",
    )
    parser.add_argument(
        "config_environment",
        type=str,
        help="Path to the json file for setting environment config parameters",
    )
    parser.add_argument(
        "input_data_dictionary", type=str, help="Path to the json file for input data"
    )
    args = parser.parse_args()

    with open(args.config_experimental) as f:
        experiment_configuration = json.load(f)
    with open(args.config_environment) as f:
        environment_configuration = json.load(f)
    with open(args.input_data_dictionary) as f:
        input_data_dictionary = json.load(f)

    # Set ANTS_MAX_THREADS to the minimum of 4 and environment_configuration["max_threads"]
    ANTS_MAX_THREADS = 4
    if environment_configuration["max_threads"] < 4:
        ANTS_MAX_THREADS = environment_configuration["max_threads"]

    SGE_THREADS_INPUT_SPEC = (
        "sgeThreads",
        attr.ib(
            type=int,
            metadata={
                "help_string": "The number of threads the Sun Grid engine should use in running this task",
                "mandatory": False,
            },
        ),
    )

    @pydra.mark.task
    def make_filename(
        filename="",
        before_str="",
        append_str="",
        extension="",
        directory="",
        parent_dir="",
    ):
        if filename is None:
            return None
        else:
            print(filename)
            print(directory)
            # if the input filename is a list, set the filename for each element in the list
            if type(filename) is list:
                new_filename = []
                for f in filename:
                    # If an extension is not specified and the filename has an extension, use the filename's extension(s)
                    if extension == "":
                        extension = "".join(Path(f).suffixes)
                    new_filename.append(
                        f"{Path(Path(directory) / Path(parent_dir) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}"
                    )
            else:
                # If an extension is not specified and the filename has an extension, use the filename's extension(s)
                if extension == "":
                    extension = "".join(Path(filename).suffixes)
                new_filename = f"{Path(Path(directory) / Path(parent_dir) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
            return new_filename

    @pydra.mark.task
    def get_input_field(input_dict: dict, field):
        print(f"input_dict: {input_dict}")
        if field in input_dict:
            print(f"field: {input_dict[field]}")
            return input_dict[field]
        else:
            return None

    def get_inputs_workflow(my_source_node):
        @pydra.mark.task
        def get_input_field(input_dict: dict, field):
            print(f"input_dict: {input_dict}")
            if field in input_dict:
                print(f"field: {input_dict[field]}")
                return input_dict[field]
            else:
                return None

        get_inputs_workflow = pydra.Workflow(
            name="inputs_workflow",
            input_spec=["input_data"],
            input_data=my_source_node.lzin.input_data,
        )
        # Get the list of t1 files from input_data_dictionary
        get_inputs_workflow.add(
            get_input_field(
                name="get_inputVolumes",
                input_dict=get_inputs_workflow.lzin.input_data,
                field="inputVolumes",
            )
        )
        get_inputs_workflow.add(
            get_input_field(
                name="get_inputVolumeTypes",
                input_dict=get_inputs_workflow.lzin.input_data,
                field="inputVolumeTypes",
            )
        )
        # Get the list of landmark files from input_data_dictionary
        get_inputs_workflow.add(
            get_input_field(
                name="get_inputLandmarksEMSP",
                input_dict=get_inputs_workflow.lzin.input_data,
                field="inputLandmarksEMSP",
            )
        )

        get_inputs_workflow.set_output(
            [
                ("inputVolumes", get_inputs_workflow.get_inputVolumes.lzout.out),
                (
                    "inputVolumeTypes",
                    get_inputs_workflow.get_inputVolumeTypes.lzout.out,
                ),
                (
                    "inputLandmarksEMSP",
                    get_inputs_workflow.get_inputLandmarksEMSP.lzout.out,
                ),
            ]
        )
        return get_inputs_workflow

    def make_bcd_workflow1(inputVolume, inputLandmarksEMSP) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSConstellationDetector

        @pydra.mark.task
        def print_input(x):
            print(f"input: {x}")
            return x


        workflow_name = "bcd_workflow1"
        configkey = "BRAINSConstellationDetector1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        bcd_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputVolume", "inputLandmarksEMSP"],
            inputVolume=inputVolume,
            inputLandmarksEMSP=inputLandmarksEMSP,
        )

        # Create the pydra-sem generated task
        bcd_task = BRAINSConstellationDetector(
            name="BRAINSConstellationDetector",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        bcd_task.qsub_args = f"-l h_rt=00:30:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"
        bcd_task.inputs.numberOfThreads = experiment_configuration[configkey].get(
            "threads"
        )

        bcd_task.inputs.inputVolume = bcd_workflow.lzin.inputVolume
        bcd_task.inputs.inputLandmarksEMSP = bcd_workflow.lzin.inputLandmarksEMSP
        bcd_task.inputs.inputTemplateModel = experiment_configuration[configkey].get(
            "inputTemplateModel"
        )
        bcd_task.inputs.interpolationMode = experiment_configuration[configkey].get(
            "interpolationMode"
        )
        bcd_task.inputs.LLSModel = experiment_configuration[configkey].get("LLSModel")
        bcd_task.inputs.acLowerBound = experiment_configuration[configkey].get(
            "acLowerBound"
        )
        bcd_task.inputs.atlasLandmarkWeights = experiment_configuration[configkey].get(
            "atlasLandmarkWeights"
        )
        bcd_task.inputs.atlasLandmarks = experiment_configuration[configkey].get(
            "atlasLandmarks"
        )
        bcd_task.inputs.houghEyeDetectorMode = experiment_configuration[configkey].get(
            "houghEyeDetectorMode"
        )
        bcd_task.inputs.outputLandmarksInInputSpace = experiment_configuration[
            configkey
        ].get("outputLandmarksInInputSpace")
        bcd_task.inputs.outputResampledVolume = experiment_configuration[configkey].get(
            "outputResampledVolume"
        )
        bcd_task.inputs.outputTransform = experiment_configuration[configkey].get(
            "outputTransform"
        )
        bcd_task.inputs.outputLandmarksInACPCAlignedSpace = experiment_configuration[
            configkey
        ].get("outputLandmarksInACPCAlignedSpace")
        bcd_task.inputs.writeBranded2DImage = experiment_configuration[configkey].get(
            "writeBranded2DImage"
        )
        bcd_workflow.add(bcd_task)

        # Set the outputs of the processing node and the source node so they are output to the sink node
        bcd_workflow.set_output(
            [
                (
                    "outputLandmarksInInputSpace",
                    bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace,
                ),
                (
                    "outputResampledVolume",
                    bcd_workflow.BRAINSConstellationDetector.lzout.outputResampledVolume,
                ),
                (
                    "outputTransform",
                    bcd_workflow.BRAINSConstellationDetector.lzout.outputTransform,
                ),
                (
                    "outputLandmarksInACPCAlignedSpace",
                    bcd_workflow.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace,
                ),
                (
                    "writeBranded2DImage",
                    bcd_workflow.BRAINSConstellationDetector.lzout.writeBranded2DImage,
                ),
            ]
        )
        return bcd_workflow

    def make_roi_workflow1(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto

        workflow_name = "roi_workflow1"
        configkey = "BRAINSROIAuto1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputVolume"],
            inputVolume=inputVolume,
        )

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto(
            "BRAINSROIAuto",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()


        # Set task inputs
        roi_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"
        roi_task.inputs.inputVolume = roi_workflow.lzin.inputVolume
        roi_task.inputs.ROIAutoDilateSize = experiment_configuration[configkey].get(
            "ROIAutoDilateSize"
        )
        roi_task.inputs.cropOutput = experiment_configuration[configkey].get(
            "cropOutput"
        )
        roi_task.inputs.outputVolume = experiment_configuration[configkey].get(
            "outputVolume"
        )

        roi_workflow.add(roi_task)
        roi_workflow.set_output(
            [
                ("outputVolume", roi_workflow.BRAINSROIAuto.lzout.outputVolume),
            ]
        )

        return roi_workflow

    def make_landmarkInitializer_workflow1(
        inputMovingLandmarkFilename,
    ) -> pydra.Workflow:
        from sem_tasks.utilities.brains import BRAINSLandmarkInitializer

        workflow_name = "landmarkInitializer_workflow1"
        configkey = "BRAINSLandmarkInitializer1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputMovingLandmarkFilename"],
            inputMovingLandmarkFilename=inputMovingLandmarkFilename,
        )

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(
            name="BRAINSLandmarkInitializer",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()


        landmark_initializer_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        landmark_initializer_task.inputs.inputMovingLandmarkFilename = (
            landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
        )
        landmark_initializer_task.inputs.inputFixedLandmarkFilename = (
            experiment_configuration[configkey].get("inputFixedLandmarkFilename")
        )
        landmark_initializer_task.inputs.inputWeightFilename = experiment_configuration[
            configkey
        ].get("inputWeightFilename")
        landmark_initializer_task.inputs.outputTransformFilename = (
            experiment_configuration[configkey].get("outputTransformFilename")
        ) 

        landmark_initializer_workflow.add(landmark_initializer_task)
        landmark_initializer_workflow.set_output(
            [
                (
                    "outputTransformFilename",
                    landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename,
                )
            ]
        )
        return landmark_initializer_workflow

    def make_landmarkInitializer_workflow2(
        inputFixedLandmarkFilename,
    ) -> pydra.Workflow:
        from sem_tasks.utilities.brains import BRAINSLandmarkInitializer

        workflow_name = "landmarkInitializer_workflow2"
        configkey = "BRAINSLandmarkInitializer2"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputFixedLandmarkFilename"],
            inputFixedLandmarkFilename=inputFixedLandmarkFilename,
        )

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(
            name="BRAINSLandmarkInitializer",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()


        landmark_initializer_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        landmark_initializer_task.inputs.inputFixedLandmarkFilename = (
            landmark_initializer_workflow.lzin.inputFixedLandmarkFilename
        )
        landmark_initializer_task.inputs.inputMovingLandmarkFilename = (
            experiment_configuration[configkey].get("inputMovingLandmarkFilename")
        )
        landmark_initializer_task.inputs.inputWeightFilename = experiment_configuration[
            configkey
        ].get("inputWeightFilename")
        landmark_initializer_task.inputs.outputTransformFilename = (
            experiment_configuration[configkey].get("outputTransformFilename")
        )

        landmark_initializer_workflow.add(landmark_initializer_task)
        landmark_initializer_workflow.set_output(
            [
                (
                    "outputTransformFilename",
                    landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename,
                )
            ]
        )

        return landmark_initializer_workflow

    def make_resample_workflow1(inputVolume, warpTransform) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample

        workflow_name = "resample_workflow1"
        configkey = "BRAINSResample1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputVolume", "warpTransform"],
            inputVolume=inputVolume,
            warpTransform=warpTransform,
        )

        # Create the pydra-sem generated task
        resample_task = BRAINSResample(
            "BRAINSResample",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        resample_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        resample_task.inputs.inputVolume = resample_workflow.lzin.inputVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.interpolationMode = experiment_configuration[
            configkey
        ].get("interpolationMode")
        resample_task.inputs.outputVolume = experiment_configuration[configkey].get(
            "outputVolume"
        )

        resample_workflow.add(resample_task)
        resample_workflow.set_output(
            [("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)]
        )

        return resample_workflow

    def make_roi_workflow2(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto

        workflow_name = "roi_workflow2"
        configkey = "BRAINSROIAuto2"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputVolume"],
            inputVolume=inputVolume,
        )

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto(
            "BRAINSROIAuto",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()


        roi_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        roi_task.inputs.inputVolume = roi_workflow.lzin.inputVolume
        roi_task.inputs.ROIAutoDilateSize = experiment_configuration[configkey].get(
            "ROIAutoDilateSize"
        )
        roi_task.inputs.outputROIMaskVolume = experiment_configuration[configkey].get(
            "outputROIMaskVolume"
        )

        roi_workflow.add(roi_task)
        roi_workflow.set_output(
            [
                (
                    "outputROIMaskVolume",
                    roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume,
                ),
            ]
        )

        return roi_workflow

    def make_antsRegistration_workflow1(
        fixed_image, fixed_image_masks, initial_moving_transform
    ) -> pydra.Workflow:
        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import Registration

        workflow_name = "antsRegistration_workflow1"
        configkey = "ANTSRegistration1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"],
            fixed_image=fixed_image,
            fixed_image_masks=fixed_image_masks,
            initial_moving_transform=initial_moving_transform,
        )

        registration = Registration()
        registration._cmd = experiment_configuration[configkey].get("executable")

        registration.inputs.num_threads = -1
        antsRegistration_task = Nipype1Task(registration)
        antsRegistration_task.qsub_args = f"-l h_rt=01:00:00 -q all.q -l mem_free=15G -pe smp {experiment_configuration[configkey].get('threads')}"


        # Set subject-specific files
        antsRegistration_task.inputs.fixed_image = (
            antsRegistration_workflow.lzin.fixed_image
        )
        antsRegistration_task.inputs.fixed_image_masks = (
            antsRegistration_workflow.lzin.fixed_image_masks
        )
        antsRegistration_task.inputs.initial_moving_transform = (
            antsRegistration_workflow.lzin.initial_moving_transform
        )

        antsRegistration_task.inputs.moving_image = experiment_configuration[
            configkey
        ].get("moving_image")
        antsRegistration_task.inputs.moving_image_masks = experiment_configuration[
            configkey
        ].get("moving_image_masks")
        antsRegistration_task.inputs.transforms = experiment_configuration[
            configkey
        ].get("transforms")
        antsRegistration_task.inputs.transform_parameters = experiment_configuration[
            configkey
        ].get("transform_parameters")
        antsRegistration_task.inputs.number_of_iterations = experiment_configuration[
            configkey
        ].get("number_of_iterations")
        antsRegistration_task.inputs.dimension = experiment_configuration[
            configkey
        ].get("dimensionality")
        antsRegistration_task.inputs.write_composite_transform = (
            experiment_configuration[configkey].get("write_composite_transform")
        )
        antsRegistration_task.inputs.collapse_output_transforms = (
            experiment_configuration[configkey].get("collapse_output_transforms")
        )
        antsRegistration_task.inputs.verbose = experiment_configuration[configkey].get(
            "verbose"
        )
        antsRegistration_task.inputs.initialize_transforms_per_stage = (
            experiment_configuration[configkey].get("initialize_transforms_per_stage")
        )
        antsRegistration_task.inputs.float = experiment_configuration[configkey].get(
            "float"
        )
        antsRegistration_task.inputs.metric = experiment_configuration[configkey].get(
            "metric"
        )
        antsRegistration_task.inputs.metric_weight = experiment_configuration[
            configkey
        ].get("metric_weight")
        antsRegistration_task.inputs.radius_or_number_of_bins = (
            experiment_configuration[configkey].get("radius_or_number_of_bins")
        )
        antsRegistration_task.inputs.sampling_strategy = experiment_configuration[
            configkey
        ].get("sampling_strategy")
        antsRegistration_task.inputs.sampling_percentage = experiment_configuration[
            configkey
        ].get("sampling_percentage")
        antsRegistration_task.inputs.convergence_threshold = experiment_configuration[
            configkey
        ].get("convergence_threshold")
        antsRegistration_task.inputs.convergence_window_size = experiment_configuration[
            configkey
        ].get("convergence_window_size")
        antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration[
            configkey
        ].get("smoothing_sigmas")
        antsRegistration_task.inputs.sigma_units = experiment_configuration[
            configkey
        ].get("sigma_units")
        antsRegistration_task.inputs.shrink_factors = experiment_configuration[
            configkey
        ].get("shrink_factors")
        antsRegistration_task.inputs.use_estimate_learning_rate_once = (
            experiment_configuration[configkey].get("use_estimate_learning_rate_once")
        )
        antsRegistration_task.inputs.use_histogram_matching = experiment_configuration[
            configkey
        ].get("use_histogram_matching")
        antsRegistration_task.inputs.winsorize_lower_quantile = (
            experiment_configuration[configkey].get("winsorize_lower_quantile")
        )
        antsRegistration_task.inputs.winsorize_upper_quantile = (
            experiment_configuration[configkey].get("winsorize_upper_quantile")
        )

        # Set the variables that set output file names
        antsRegistration_task.inputs.output_transform_prefix = experiment_configuration[
            configkey
        ].get("output_transform_prefix")
        antsRegistration_task.inputs.output_warped_image = experiment_configuration[
            configkey
        ].get("output_warped_image")
        antsRegistration_task.inputs.output_inverse_warped_image = (
            experiment_configuration[configkey].get("output_inverse_warped_image")
        )

        antsRegistration_workflow.add(antsRegistration_task)
        antsRegistration_workflow.set_output(
            [
                (
                    "composite_transform",
                    antsRegistration_task.lzout.composite_transform,
                ),
                (
                    "inverse_composite_transform",
                    antsRegistration_task.lzout.inverse_composite_transform,
                ),
                ("warped_image", antsRegistration_task.lzout.warped_image),
                (
                    "inverse_warped_image",
                    antsRegistration_task.lzout.inverse_warped_image,
                ),
            ]
        )

        return antsRegistration_workflow

    def make_antsRegistration_workflow2(
        fixed_image, fixed_image_masks, initial_moving_transform
    ) -> pydra.Workflow:
        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import Registration

        workflow_name = "antsRegistration_workflow2"
        configkey = "ANTSRegistration2"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"],
            fixed_image=fixed_image,
            fixed_image_masks=fixed_image_masks,
            initial_moving_transform=initial_moving_transform,
        )

        registration = Registration()
        registration._cmd = experiment_configuration[configkey].get("executable")

        registration.inputs.num_threads = -1
        antsRegistration_task = Nipype1Task(registration)

        antsRegistration_task.qsub_args = f"-l h_rt=02:00:00 -q all.q -l mem_free=15G -pe smp {experiment_configuration[configkey].get('threads')}"
        # Set subject-specific files
        antsRegistration_task.inputs.fixed_image = (
            antsRegistration_workflow.lzin.fixed_image
        )
        antsRegistration_task.inputs.fixed_image_masks = (
            antsRegistration_workflow.lzin.fixed_image_masks
        )
        antsRegistration_task.inputs.initial_moving_transform = (
            antsRegistration_workflow.lzin.initial_moving_transform
        )

        antsRegistration_task.inputs.moving_image = experiment_configuration[
            configkey
        ].get("moving_image")
        antsRegistration_task.inputs.moving_image_masks = experiment_configuration[
            configkey
        ].get("moving_image_masks")
        antsRegistration_task.inputs.save_state = experiment_configuration[
            configkey
        ].get("save_state")
        antsRegistration_task.inputs.transforms = experiment_configuration[
            configkey
        ].get("transforms")
        antsRegistration_task.inputs.transform_parameters = experiment_configuration[
            configkey
        ].get("transform_parameters")
        antsRegistration_task.inputs.number_of_iterations = experiment_configuration[
            configkey
        ].get("number_of_iterations")
        antsRegistration_task.inputs.dimension = experiment_configuration[
            configkey
        ].get("dimensionality")
        antsRegistration_task.inputs.write_composite_transform = (
            experiment_configuration[configkey].get("write_composite_transform")
        )
        antsRegistration_task.inputs.collapse_output_transforms = (
            experiment_configuration[configkey].get("collapse_output_transforms")
        )
        antsRegistration_task.inputs.verbose = experiment_configuration[configkey].get(
            "verbose"
        )
        antsRegistration_task.inputs.initialize_transforms_per_stage = (
            experiment_configuration[configkey].get("initialize_transforms_per_stage")
        )
        antsRegistration_task.inputs.float = experiment_configuration[configkey].get(
            "float"
        )
        antsRegistration_task.inputs.metric = experiment_configuration[configkey].get(
            "metric"
        )
        antsRegistration_task.inputs.metric_weight = experiment_configuration[
            configkey
        ].get("metric_weight")
        antsRegistration_task.inputs.radius_or_number_of_bins = (
            experiment_configuration[configkey].get("radius_or_number_of_bins")
        )
        antsRegistration_task.inputs.sampling_strategy = experiment_configuration[
            configkey
        ].get("sampling_strategy")
        antsRegistration_task.inputs.sampling_percentage = experiment_configuration[
            configkey
        ].get("sampling_percentage")
        antsRegistration_task.inputs.convergence_threshold = experiment_configuration[
            configkey
        ].get("convergence_threshold")
        antsRegistration_task.inputs.convergence_window_size = experiment_configuration[
            configkey
        ].get("convergence_window_size")
        antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration[
            configkey
        ].get("smoothing_sigmas")
        antsRegistration_task.inputs.sigma_units = experiment_configuration[
            configkey
        ].get("sigma_units")
        antsRegistration_task.inputs.shrink_factors = experiment_configuration[
            configkey
        ].get("shrink_factors")
        antsRegistration_task.inputs.use_estimate_learning_rate_once = (
            experiment_configuration[configkey].get("use_estimate_learning_rate_once")
        )
        antsRegistration_task.inputs.use_histogram_matching = experiment_configuration[
            configkey
        ].get("use_histogram_matching")
        antsRegistration_task.inputs.winsorize_lower_quantile = (
            experiment_configuration[configkey].get("winsorize_lower_quantile")
        )
        antsRegistration_task.inputs.winsorize_upper_quantile = (
            experiment_configuration[configkey].get("winsorize_upper_quantile")
        )

        # Set the variables that set output file names
        antsRegistration_task.inputs.output_transform_prefix = experiment_configuration[
            configkey
        ].get("output_transform_prefix")
        antsRegistration_task.inputs.output_warped_image = experiment_configuration[
            configkey
        ].get("output_warped_image")
        antsRegistration_task.inputs.output_inverse_warped_image = (
            experiment_configuration[configkey].get("output_inverse_warped_image")
        )

        antsRegistration_workflow.add(antsRegistration_task)
        antsRegistration_workflow.set_output(
            [
                ("save_state", antsRegistration_task.lzout.save_state),
                (
                    "composite_transform",
                    antsRegistration_task.lzout.composite_transform,
                ),
                (
                    "inverse_composite_transform",
                    antsRegistration_task.lzout.inverse_composite_transform,
                ),
                ("warped_image", antsRegistration_task.lzout.warped_image),
                (
                    "inverse_warped_image",
                    antsRegistration_task.lzout.inverse_warped_image,
                ),
            ]
        )

        return antsRegistration_workflow

    def make_abc_workflow1(
        inputVolumeCropped, inputVolumes, inputVolumeTypes, restoreState
    ) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSABC

        averaged_filenames_by_type = {
            "T1": "t1_average_BRAINSABC.nii.gz",
            "T2": "t2_average_BRAINSABC.nii.gz",
            "PD": "pd_average_BRAINSABC.nii.gz",
            "FL": "fl_average_BRAINSABC.nii.gz",
        }

        @pydra.mark.task
        def get_averaged_volume(outputs, filetype):
            output_filenames = [x.name for x in outputs]
            if averaged_filenames_by_type[filetype] in output_filenames:
                return outputs[
                    output_filenames.index(averaged_filenames_by_type[filetype])
                ]
            else:
                return None

        @pydra.mark.task
        def get_posteriors(outputs):
            output_filenames = [x.name for x in outputs]
            posteriors_starting_index = 0
            for averaged_output in list(averaged_filenames_by_type.values()):
                if averaged_output in output_filenames:
                    posteriors_starting_index += 1
            return outputs[posteriors_starting_index:]

        @pydra.mark.task
        def print_input(x, element):
            print(f"{element} ({type(x)}): {x}")
            return x

        @pydra.mark.task
        def set_inputVolumes(inputVolumeCropped, inputVolumes):
            inputVolumes[0] = inputVolumeCropped
            print(f"inputVolumes: {inputVolumes}")
            return inputVolumes

        @pydra.mark.task
        def set_implicitOutputs(inputVolumeTypes):
            if "T2" in inputVolumeTypes:
                implicitOutputs = (
                    [experiment_configuration[configkey].get("t1_average")]
                    + [experiment_configuration[configkey].get("t2_average")]
                    + experiment_configuration[configkey].get("posteriors")
                )
            else:
                implicitOutputs = [
                    experiment_configuration[configkey].get("t1_average")
                ] + experiment_configuration[configkey].get("posteriors")
            return implicitOutputs

        workflow_name = "abc_workflow1"
        configkey = "BRAINSABC1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        abc_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=[
                "inputVolumes",
                "inputVolumeCropped",
                "inputVolumeTypes",
                "restoreState",
            ],
            inputVolumes=inputVolumes,
            inputVolumeTypes=inputVolumeTypes,
            inputVolumeCropped=inputVolumeCropped,
            restoreState=restoreState,
        )
        abc_workflow.add(
            make_filename(
                name="outputVolumes",
                filename=abc_workflow.lzin.inputVolumes,
                append_str="_corrected",
                extension=".nii.gz",
            )
        )
        abc_workflow.add(
            set_inputVolumes(
                name="set_inputVolumes",
                inputVolumeCropped=abc_workflow.lzin.inputVolumeCropped,
                inputVolumes=abc_workflow.lzin.inputVolumes,
            )
        )
        abc_workflow.add(
            set_implicitOutputs(
                name="set_implicitOutputs",
                inputVolumeTypes=abc_workflow.lzin.inputVolumeTypes,
            )
        )

        # Create the pydra-sem generated task
        abc_task = BRAINSABC(
            name="BRAINSABC",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        abc_task.qsub_args = f"-l h_rt=02:00:00 -l mem_free=15G -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        abc_task.inputs.numberOfThreads = experiment_configuration[configkey].get(
            "threads"
        )

        # Set task inputs
        abc_task.inputs.inputVolumes = abc_workflow.set_inputVolumes.lzout.out
        abc_task.inputs.restoreState = abc_workflow.lzin.restoreState
        abc_task.inputs.inputVolumeTypes = abc_workflow.lzin.inputVolumeTypes
        abc_task.inputs.outputVolumes = abc_workflow.outputVolumes.lzout.out

        abc_task.inputs.atlasDefinition = experiment_configuration[configkey].get(
            "atlasDefinition"
        )
        abc_task.inputs.atlasToSubjectTransform = experiment_configuration[
            configkey
        ].get("atlasToSubjectTransform")
        abc_task.inputs.atlasToSubjectTransformType = experiment_configuration[
            configkey
        ].get("atlasToSubjectTransformType")
        abc_task.inputs.debuglevel = experiment_configuration[configkey].get(
            "debuglevel"
        )
        abc_task.inputs.filterIteration = experiment_configuration[configkey].get(
            "filterIteration"
        )
        abc_task.inputs.filterMethod = experiment_configuration[configkey].get(
            "filterMethod"
        )
        abc_task.inputs.interpolationMode = experiment_configuration[configkey].get(
            "interpolationMode"
        )
        abc_task.inputs.maxBiasDegree = experiment_configuration[configkey].get(
            "maxBiasDegree"
        )
        abc_task.inputs.maxIterations = experiment_configuration[configkey].get(
            "maxIterations"
        )
        abc_task.inputs.posteriorTemplate = experiment_configuration[configkey].get(
            "posteriorTemplate"
        )
        abc_task.inputs.purePlugsThreshold = experiment_configuration[configkey].get(
            "purePlugsThreshold"
        )
        abc_task.inputs.saveState = experiment_configuration[configkey].get("saveState")
        abc_task.inputs.useKNN = experiment_configuration[configkey].get("useKNN")
        abc_task.inputs.outputFormat = experiment_configuration[configkey].get(
            "outputFormat"
        )
        abc_task.inputs.outputDir = experiment_configuration[configkey].get("outputDir")
        abc_task.inputs.outputDirtyLabels = experiment_configuration[configkey].get(
            "outputDirtyLabels"
        )
        abc_task.inputs.outputLabels = experiment_configuration[configkey].get(
            "outputLabels"
        )
        abc_task.inputs.implicitOutputs = abc_workflow.set_implicitOutputs.lzout.out

        abc_workflow.add(abc_task)

        abc_workflow.add(
            get_averaged_volume(
                name="get_t1_average",
                outputs=abc_task.lzout.implicitOutputs,
                filetype="T1",
            )
        )
        abc_workflow.add(
            get_averaged_volume(
                name="get_t2_average",
                outputs=abc_task.lzout.implicitOutputs,
                filetype="T2",
            )
        )
        abc_workflow.add(
            get_averaged_volume(
                name="get_pd_average",
                outputs=abc_task.lzout.implicitOutputs,
                filetype="PD",
            )
        )
        abc_workflow.add(
            get_averaged_volume(
                name="get_fl_average",
                outputs=abc_task.lzout.implicitOutputs,
                filetype="FL",
            )
        )
        abc_workflow.add(
            get_posteriors(
                name="get_posteriors",
                outputs=abc_task.lzout.implicitOutputs,
            )
        )
        abc_workflow.set_output(
            [
                ("outputVolumes", abc_workflow.BRAINSABC.lzout.outputVolumes),
                ("outputDirtyLabels", abc_workflow.BRAINSABC.lzout.outputDirtyLabels),
                ("outputLabels", abc_workflow.BRAINSABC.lzout.outputLabels),
                (
                    "atlasToSubjectTransform",
                    abc_workflow.BRAINSABC.lzout.atlasToSubjectTransform,
                ),
                ("t1_average", abc_workflow.get_t1_average.lzout.out),
                ("t2_average", abc_workflow.get_t2_average.lzout.out),
                ("pd_average", abc_workflow.get_pd_average.lzout.out),
                ("fl_average", abc_workflow.get_fl_average.lzout.out),
                ("posteriors", abc_workflow.get_posteriors.lzout.out),
            ]
        )

        return abc_workflow

    def make_resample_workflow2(
        inputVolume, referenceVolume, warpTransform
    ) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample

        workflow_name = "resample_workflow2"
        configkey = "BRAINSResample2"
        print(f"Making task {workflow_name}")

        @pydra.mark.task
        def print_input(x):
            print(x)
            return x

        # Define the workflow and its lazy inputs
        resample_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["referenceVolume", "warpTransform", "inputVolume"],
            referenceVolume=referenceVolume,
            warpTransform=warpTransform,
            inputVolume=inputVolume,
        )
        resample_workflow.add(
            make_filename(
                name="outputVolume", filename=resample_workflow.lzin.inputVolume
            )
        )

        # Create the pydra-sem generated task
        resample_task = BRAINSResample(
            "BRAINSResample",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        resample_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"
        # Set task inputs
        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.warpTransform = resample_workflow.lzin.warpTransform
        resample_task.inputs.inputVolume = resample_workflow.lzin.inputVolume
        resample_task.inputs.outputVolume = resample_workflow.outputVolume.lzout.out
        resample_task.inputs.interpolationMode = experiment_configuration[
            configkey
        ].get("interpolationMode")
        resample_task.inputs.pixelType = experiment_configuration[configkey].get(
            "pixelType"
        )

        resample_workflow.add(resample_task)
        resample_workflow.set_output(
            [("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)]
        )

        return resample_workflow

    def make_resample_workflow3(inputVolume, referenceVolume) -> pydra.Workflow:
        from sem_tasks.registration import BRAINSResample

        workflow_name = "resample_workflow3"
        configkey = "BRAINSResample3"
        print(f"Making task {workflow_name}")

        resample_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["referenceVolume", "inputVolume"],
            referenceVolume=referenceVolume,
            inputVolume=inputVolume,
        )
        # Create the pydra-sem generated task
        resample_task = BRAINSResample(
            "BRAINSResample",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        resample_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        resample_task.inputs.referenceVolume = resample_workflow.lzin.referenceVolume
        resample_task.inputs.inputVolume = resample_workflow.lzin.inputVolume
        resample_task.inputs.outputVolume = experiment_configuration[configkey].get(
            "outputVolume"
        )
        resample_task.inputs.interpolationMode = experiment_configuration[
            configkey
        ].get("interpolationMode")
        resample_task.inputs.pixelType = experiment_configuration[configkey].get(
            "pixelType"
        )

        resample_workflow.add(resample_task)
        resample_workflow.set_output(
            [("outputVolume", resample_workflow.BRAINSResample.lzout.outputVolume)]
        )
        return resample_workflow

    def make_createLabelMapFromProbabilityMaps_workflow1(
        inputProbabilityVolume, nonAirRegionMask
    ) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import (
            BRAINSCreateLabelMapFromProbabilityMaps,
        )

        workflow_name = "createLabelMapFromProbabilityMaps_workflow1"
        configkey = "BRAINSCreateLabelMapFromProbabilityMaps1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        label_map_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputProbabilityVolume", "nonAirRegionMask"],
            inputProbabilityVolume=inputProbabilityVolume,
            nonAirRegionMask=nonAirRegionMask,
        )

        # Create the pydra-sem generated task
        label_map_task = BRAINSCreateLabelMapFromProbabilityMaps(
            name="BRAINSCreateLabelMapFromProbabilityMaps",
            executable=experiment_configuration[configkey]["executable"],
        ).get_task()


        label_map_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        label_map_task.inputs.inputProbabilityVolume = (
            label_map_workflow.lzin.inputProbabilityVolume
        )
        label_map_task.inputs.nonAirRegionMask = (
            label_map_workflow.lzin.nonAirRegionMask
        )
        label_map_task.inputs.cleanLabelVolume = experiment_configuration[
            configkey
        ].get("cleanLabelVolume")
        label_map_task.inputs.dirtyLabelVolume = experiment_configuration[
            configkey
        ].get("dirtyLabelVolume")
        label_map_task.inputs.foregroundPriors = experiment_configuration[
            configkey
        ].get("foregroundPriors")
        label_map_task.inputs.priorLabelCodes = experiment_configuration[configkey].get(
            "priorLabelCodes"
        )
        label_map_task.inputs.inclusionThreshold = experiment_configuration[
            configkey
        ].get("inclusionThreshold")

        label_map_workflow.add(label_map_task)
        label_map_workflow.set_output(
            [
                (
                    "cleanLabelVolume",
                    label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.cleanLabelVolume,
                ),
                (
                    "dirtyLabelVolume",
                    label_map_workflow.BRAINSCreateLabelMapFromProbabilityMaps.lzout.dirtyLabelVolume,
                ),
            ]
        )
        return label_map_workflow

    def make_landmarkInitializer_workflow3(
        inputFixedLandmarkFilename, inputMovingLandmarkFilename
    ) -> pydra.Workflow:
        from sem_tasks.utilities.brains import BRAINSLandmarkInitializer

        workflow_name = f"landmarkInitializer_workflow3"
        configkey = f"BRAINSLandmarkInitializer3"
        print(f"Making task {workflow_name}")

        @pydra.mark.task
        def get_parent_directory(filepath):
            return Path(filepath).parent.name

        # Define the workflow and its lazy inputs
        landmark_initializer_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputFixedLandmarkFilename", "inputMovingLandmarkFilename"],
            inputFixedLandmarkFilename=inputFixedLandmarkFilename,
            inputMovingLandmarkFilename=inputMovingLandmarkFilename,
        )

        landmark_initializer_workflow.add(
            get_parent_directory(
                name="get_parent_directory",
                filepath=landmark_initializer_workflow.lzin.inputMovingLandmarkFilename,
            )
        )
        landmark_initializer_workflow.add(
            make_filename(
                name="outputTransformFilename",
                before_str="landmarkInitializer_",
                filename=landmark_initializer_workflow.get_parent_directory.lzout.out,
                append_str="_to_subject_transform",
                extension=".h5",
            )
        )

        # Create the pydra-sem generated task
        landmark_initializer_task = BRAINSLandmarkInitializer(
            name="BRAINSLandmarkInitializer",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()


        landmark_initializer_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        landmark_initializer_task.inputs.inputFixedLandmarkFilename = (
            landmark_initializer_workflow.lzin.inputFixedLandmarkFilename
        )
        landmark_initializer_task.inputs.inputMovingLandmarkFilename = (
            landmark_initializer_workflow.lzin.inputMovingLandmarkFilename
        )
        landmark_initializer_task.inputs.outputTransformFilename = (
            landmark_initializer_workflow.outputTransformFilename.lzout.out
        )  # experiment_configuration[configkey].get('outputTransformFilename')
        landmark_initializer_task.inputs.inputWeightFilename = experiment_configuration[
            configkey
        ].get("inputWeightFilename")

        landmark_initializer_workflow.add(landmark_initializer_task)
        landmark_initializer_workflow.set_output(
            [
                (
                    "outputTransformFilename",
                    landmark_initializer_workflow.BRAINSLandmarkInitializer.lzout.outputTransformFilename,
                ),
                (
                    "atlas_id",
                    landmark_initializer_workflow.get_parent_directory.lzout.out,
                ),
            ]
        )

        return landmark_initializer_workflow

    def make_antsRegistration_workflow3_without_T2(
        fixed_image, fixed_image_masks, initial_moving_transform
    ) -> pydra.Workflow:

        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import Registration

        @pydra.mark.task
        def get_atlas_id_from_landmark_initializer_transform(
            landmark_initializer_transform,
        ):
            atlas_id = Path(landmark_initializer_transform).name.split("_")[1]
            return atlas_id

        workflow_name = "antsRegistration_workflow3"
        configkey = "ANTSRegistration3_without_T2"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["fixed_image", "fixed_image_masks", "initial_moving_transform"],
            fixed_image=fixed_image,
            fixed_image_masks=fixed_image_masks,
            initial_moving_transform=initial_moving_transform,
        )

        antsRegistration_workflow.add(
            get_atlas_id_from_landmark_initializer_transform(
                name="atlas_id",
                landmark_initializer_transform=antsRegistration_workflow.lzin.initial_moving_transform,
            )
        )

        antsRegistration_workflow.add(
            make_filename(
                name="make_moving_image",
                directory=experiment_configuration[configkey].get("moving_image_dir"),
                parent_dir=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "moving_image_filename"
                ),
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_moving_image_masks",
                directory=experiment_configuration[configkey].get("moving_image_dir"),
                parent_dir=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "moving_image_masks_filename"
                ),
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_output_transform_prefix",
                before_str=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "output_transform_prefix_suffix"
                ),
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_output_warped_image",
                before_str=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "output_warped_image_suffix"
                ),
            )
        )

        registration = Registration()
        registration._cmd = experiment_configuration[configkey].get("executable")

        registration.inputs.num_threads = -1
        antsRegistration_task = Nipype1Task(registration)
        antsRegistration_task.qsub_args = f"-l h_rt=02:30:00 -q all.q -l mem_free=15G -pe smp {experiment_configuration[configkey].get('threads')}"
        # Set task inputs
        antsRegistration_task.inputs.fixed_image = (
            antsRegistration_workflow.lzin.fixed_image
        )
        antsRegistration_task.inputs.fixed_image_masks = (
            antsRegistration_workflow.lzin.fixed_image_masks
        )
        antsRegistration_task.inputs.initial_moving_transform = (
            antsRegistration_workflow.lzin.initial_moving_transform
        )
        antsRegistration_task.inputs.moving_image = (
            antsRegistration_workflow.make_moving_image.lzout.out
        )
        antsRegistration_task.inputs.moving_image_masks = (
            antsRegistration_workflow.make_moving_image_masks.lzout.out
        )
        antsRegistration_task.inputs.transforms = experiment_configuration[
            configkey
        ].get("transforms")
        antsRegistration_task.inputs.transform_parameters = experiment_configuration[
            configkey
        ].get("transform_parameters")
        antsRegistration_task.inputs.number_of_iterations = experiment_configuration[
            configkey
        ].get("number_of_iterations")
        antsRegistration_task.inputs.dimension = experiment_configuration[
            configkey
        ].get("dimensionality")
        antsRegistration_task.inputs.write_composite_transform = (
            experiment_configuration[configkey].get("write_composite_transform")
        )
        antsRegistration_task.inputs.collapse_output_transforms = (
            experiment_configuration[configkey].get("collapse_output_transforms")
        )
        antsRegistration_task.inputs.verbose = experiment_configuration[configkey].get(
            "verbose"
        )
        antsRegistration_task.inputs.initialize_transforms_per_stage = (
            experiment_configuration[configkey].get("initialize_transforms_per_stage")
        )
        antsRegistration_task.inputs.float = experiment_configuration[configkey].get(
            "float"
        )
        antsRegistration_task.inputs.metric = experiment_configuration[configkey].get(
            "metric"
        )
        antsRegistration_task.inputs.metric_weight = experiment_configuration[
            configkey
        ].get("metric_weight")
        antsRegistration_task.inputs.radius_or_number_of_bins = (
            experiment_configuration[configkey].get("radius_or_number_of_bins")
        )
        antsRegistration_task.inputs.sampling_strategy = experiment_configuration[
            configkey
        ].get("sampling_strategy")
        antsRegistration_task.inputs.sampling_percentage = experiment_configuration[
            configkey
        ].get("sampling_percentage")
        antsRegistration_task.inputs.convergence_threshold = experiment_configuration[
            configkey
        ].get("convergence_threshold")
        antsRegistration_task.inputs.convergence_window_size = experiment_configuration[
            configkey
        ].get("convergence_window_size")
        antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration[
            configkey
        ].get("smoothing_sigmas")
        antsRegistration_task.inputs.sigma_units = experiment_configuration[
            configkey
        ].get("sigma_units")
        antsRegistration_task.inputs.shrink_factors = experiment_configuration[
            configkey
        ].get("shrink_factors")
        antsRegistration_task.inputs.use_estimate_learning_rate_once = (
            experiment_configuration[configkey].get("use_estimate_learning_rate_once")
        )
        antsRegistration_task.inputs.use_histogram_matching = experiment_configuration[
            configkey
        ].get("use_histogram_matching")
        antsRegistration_task.inputs.winsorize_lower_quantile = (
            experiment_configuration[configkey].get("winsorize_lower_quantile")
        )
        antsRegistration_task.inputs.winsorize_upper_quantile = (
            experiment_configuration[configkey].get("winsorize_upper_quantile")
        )

        # Set the variables that set output file names
        antsRegistration_task.inputs.output_transform_prefix = (
            antsRegistration_workflow.make_output_transform_prefix.lzout.out
        )
        antsRegistration_task.inputs.output_warped_image = (
            antsRegistration_workflow.make_output_warped_image.lzout.out
        )

        antsRegistration_workflow.add(antsRegistration_task)
        antsRegistration_workflow.set_output(
            [
                (
                    "composite_transform",
                    antsRegistration_task.lzout.composite_transform,
                ),
                (
                    "inverse_composite_transform",
                    antsRegistration_task.lzout.inverse_composite_transform,
                ),
                ("warped_image", antsRegistration_task.lzout.warped_image),
            ]
        )

        return antsRegistration_workflow

    def make_antsRegistration_workflow3_with_T2(
        fixed_image_T1, fixed_image_T2, fixed_image_masks, initial_moving_transform
    ) -> pydra.Workflow:

        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import Registration

        @pydra.mark.task
        def get_atlas_id_from_landmark_initializer_transform(
            landmark_initializer_transform,
        ):
            atlas_id = Path(landmark_initializer_transform).name.split("_")[1]
            return atlas_id

        @pydra.mark.task
        def get_fixed_images(fixed_image_T1, fixed_image_T2):
            return [fixed_image_T1, fixed_image_T2]


        workflow_name = "antsRegistration_workflow3"
        configkey = "ANTSRegistration3_with_T2"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsRegistration_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=[
                "fixed_image_T1",
                "fixed_image_T2",
                "fixed_image_masks",
                "initial_moving_transform",
            ],
            fixed_image_T1=fixed_image_T1,
            fixed_image_T2=fixed_image_T2,
            fixed_image_masks=fixed_image_masks,
            initial_moving_transform=initial_moving_transform,
        )

        antsRegistration_workflow.add(
            get_atlas_id_from_landmark_initializer_transform(
                name="atlas_id",
                landmark_initializer_transform=antsRegistration_workflow.lzin.initial_moving_transform,
            )
        )

        antsRegistration_workflow.add(
            make_filename(
                name="make_moving_image",
                directory=experiment_configuration[configkey].get("moving_image_dir"),
                parent_dir=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "moving_image_filename"
                ),
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_moving_image_masks",
                directory=experiment_configuration[configkey].get("moving_image_dir"),
                parent_dir=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "moving_image_masks_filename"
                ),
            )
        )
        antsRegistration_workflow.add(
            get_fixed_images(
                name="get_fixed_images",
                fixed_image_T1=antsRegistration_workflow.lzin.fixed_image_T1,
                fixed_image_T2=antsRegistration_workflow.lzin.fixed_image_T2,
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_output_transform_prefix",
                before_str=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "output_transform_prefix_suffix"
                ),
            )
        )
        antsRegistration_workflow.add(
            make_filename(
                name="make_output_warped_image",
                before_str=antsRegistration_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "output_warped_image_suffix"
                ),
            )
        )

        registration = Registration()
        registration._cmd = experiment_configuration[configkey].get("executable")

        registration.inputs.num_threads = -1
        antsRegistration_task = Nipype1Task(registration)
        antsRegistration_task.qsub_args = f"-l h_rt=02:30:00 -q all.q -l mem_free=15G -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        antsRegistration_task.inputs.fixed_image = (
            antsRegistration_workflow.get_fixed_images.lzout.out
        )
        antsRegistration_task.inputs.fixed_image_masks = (
            antsRegistration_workflow.lzin.fixed_image_masks
        )
        antsRegistration_task.inputs.initial_moving_transform = (
            antsRegistration_workflow.lzin.initial_moving_transform
        )
        antsRegistration_task.inputs.moving_image = (
            antsRegistration_workflow.make_moving_image.lzout.out
        )
        antsRegistration_task.inputs.moving_image_masks = (
            antsRegistration_workflow.make_moving_image_masks.lzout.out
        )
        antsRegistration_task.inputs.transforms = experiment_configuration[
            configkey
        ].get("transforms")
        antsRegistration_task.inputs.transform_parameters = experiment_configuration[
            configkey
        ].get("transform_parameters")
        antsRegistration_task.inputs.number_of_iterations = experiment_configuration[
            configkey
        ].get("number_of_iterations")
        antsRegistration_task.inputs.dimension = experiment_configuration[
            configkey
        ].get("dimensionality")
        antsRegistration_task.inputs.write_composite_transform = (
            experiment_configuration[configkey].get("write_composite_transform")
        )
        antsRegistration_task.inputs.collapse_output_transforms = (
            experiment_configuration[configkey].get("collapse_output_transforms")
        )
        antsRegistration_task.inputs.verbose = experiment_configuration[configkey].get(
            "verbose"
        )
        antsRegistration_task.inputs.initialize_transforms_per_stage = (
            experiment_configuration[configkey].get("initialize_transforms_per_stage")
        )
        antsRegistration_task.inputs.float = experiment_configuration[configkey].get(
            "float"
        )
        antsRegistration_task.inputs.metric = experiment_configuration[configkey].get(
            "metric"
        )
        antsRegistration_task.inputs.metric_weight = experiment_configuration[
            configkey
        ].get("metric_weight")
        antsRegistration_task.inputs.radius_or_number_of_bins = (
            experiment_configuration[configkey].get("radius_or_number_of_bins")
        )
        antsRegistration_task.inputs.sampling_strategy = experiment_configuration[
            configkey
        ].get("sampling_strategy")
        antsRegistration_task.inputs.sampling_percentage = experiment_configuration[
            configkey
        ].get("sampling_percentage")
        antsRegistration_task.inputs.convergence_threshold = experiment_configuration[
            configkey
        ].get("convergence_threshold")
        antsRegistration_task.inputs.convergence_window_size = experiment_configuration[
            configkey
        ].get("convergence_window_size")
        antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration[
            configkey
        ].get("smoothing_sigmas")
        antsRegistration_task.inputs.sigma_units = experiment_configuration[
            configkey
        ].get("sigma_units")
        antsRegistration_task.inputs.shrink_factors = experiment_configuration[
            configkey
        ].get("shrink_factors")
        antsRegistration_task.inputs.use_estimate_learning_rate_once = (
            experiment_configuration[configkey].get("use_estimate_learning_rate_once")
        )
        antsRegistration_task.inputs.use_histogram_matching = experiment_configuration[
            configkey
        ].get("use_histogram_matching")
        antsRegistration_task.inputs.winsorize_lower_quantile = (
            experiment_configuration[configkey].get("winsorize_lower_quantile")
        )
        antsRegistration_task.inputs.winsorize_upper_quantile = (
            experiment_configuration[configkey].get("winsorize_upper_quantile")
        )

        # Set the variables that set output file names
        antsRegistration_task.inputs.output_transform_prefix = (
            antsRegistration_workflow.make_output_transform_prefix.lzout.out
        )
        antsRegistration_task.inputs.output_warped_image = (
            antsRegistration_workflow.make_output_warped_image.lzout.out
        )

        antsRegistration_workflow.add(antsRegistration_task)
        antsRegistration_workflow.set_output(
            [
                (
                    "composite_transform",
                    antsRegistration_task.lzout.composite_transform,
                ),
                (
                    "inverse_composite_transform",
                    antsRegistration_task.lzout.inverse_composite_transform,
                ),
                ("warped_image", antsRegistration_task.lzout.warped_image),
            ]
        )

        return antsRegistration_workflow

    def make_roi_workflow3(inputVolume) -> pydra.Workflow:
        from sem_tasks.segmentation.specialized import BRAINSROIAuto

        workflow_name = "roi_workflow3"
        configkey = "BRAINSROIAuto3"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        roi_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["inputVolume"],
            inputVolume=inputVolume,
        )

        # Create the pydra-sem generated task
        roi_task = BRAINSROIAuto(
            "BRAINSROIAuto",
            executable=experiment_configuration[configkey].get("executable"),
        ).get_task()

        roi_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"

        # Set task inputs
        roi_task.inputs.inputVolume = roi_workflow.lzin.inputVolume
        roi_task.inputs.ROIAutoDilateSize = experiment_configuration[configkey].get(
            "ROIAutoDilateSize"
        )
        roi_task.inputs.outputROIMaskVolume = experiment_configuration[configkey].get(
            "outputROIMaskVolume"
        )

        roi_workflow.add(roi_task)
        roi_workflow.set_output(
            [
                (
                    "outputROIMaskVolume",
                    roi_workflow.BRAINSROIAuto.lzout.outputROIMaskVolume,
                ),
            ]
        )

        return roi_workflow

    def make_antsApplyTransforms_workflow(
        index, output_image_end, reference_image, transform
    ):
        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import ApplyTransforms

        @pydra.mark.task
        def get_atlas_id_from_transform(transform):
            # From 68653_ToSubjectPreJointFusion_SyNComposite.h5 get 68653
            atlas_id = Path(transform).name.split("_")[0]
            return atlas_id

        workflow_name = f"antsApplyTransforms_workflow{index}"
        configkey = f"ANTSApplyTransforms{index}"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsApplyTransforms_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=["reference_image", "transform"],
            reference_image=reference_image,
            transform=transform,
        )

        antsApplyTransforms_workflow.add(
            get_atlas_id_from_transform(
                name="atlas_id", transform=antsApplyTransforms_workflow.lzin.transform
            )
        )

        antsApplyTransforms_workflow.add(
            make_filename(
                name="input_image",
                directory=experiment_configuration[configkey].get("input_image_dir"),
                parent_dir=antsApplyTransforms_workflow.atlas_id.lzout.out,
                filename=experiment_configuration[configkey].get(
                    "input_image_filename"
                ),
            )
        )
        antsApplyTransforms_workflow.add(
            make_filename(
                name="output_image",
                before_str=antsApplyTransforms_workflow.atlas_id.lzout.out,
                filename=output_image_end,
            )
        )

        applyTransforms = ApplyTransforms()
        applyTransforms._cmd = experiment_configuration[configkey].get("executable")

        applyTransforms.inputs.num_threads = -1
        antsApplyTransforms_task = Nipype1Task(applyTransforms)
        antsApplyTransforms_task.qsub_args = f"-l h_rt=00:15:00 -q all.q -pe smp {experiment_configuration[configkey].get('threads')}"
        # Set task inputs
        antsApplyTransforms_task.inputs.input_image = (
            antsApplyTransforms_workflow.input_image.lzout.out
        )
        antsApplyTransforms_task.inputs.output_image = (
            antsApplyTransforms_workflow.output_image.lzout.out
        )
        antsApplyTransforms_task.inputs.reference_image = (
            antsApplyTransforms_workflow.lzin.reference_image
        )
        antsApplyTransforms_task.inputs.transforms = (
            antsApplyTransforms_workflow.lzin.transform
        )
        antsApplyTransforms_task.inputs.dimension = experiment_configuration[
            configkey
        ].get("dimension")
        antsApplyTransforms_task.inputs.float = experiment_configuration[configkey].get(
            "float"
        )
        antsApplyTransforms_task.inputs.interpolation = experiment_configuration[
            configkey
        ].get("interpolation")

        antsApplyTransforms_workflow.add(antsApplyTransforms_task)
        antsApplyTransforms_workflow.set_output(
            [
                ("output_image", antsApplyTransforms_task.lzout.output_image),
            ]
        )

        return antsApplyTransforms_workflow

    def make_antsJointFusion_workflow1(
        atlas_image, atlas_segmentation_image, target_image, mask_image
    ):

        from pydra.tasks.nipype1.utils import Nipype1Task
        from nipype.interfaces.ants import JointFusion

        @pydra.mark.task
        def to_list(value):
            return [value]

        workflow_name = f"antsJointFusion_workflow1"
        configkey = f"ANTSJointFusion1"
        print(f"Making task {workflow_name}")

        # Define the workflow and its lazy inputs
        antsJointFusion_workflow = pydra.Workflow(
            plugin="cf",
            name=workflow_name,
            input_spec=[
                "atlas_image",
                "atlas_segmentation_image",
                "target_image",
                "mask_image",
            ],
            atlas_image=atlas_image,
            atlas_segmentation_image=atlas_segmentation_image,
            target_image=target_image,
            mask_image=mask_image,
        )
        antsJointFusion_workflow.add(
            to_list(name="to_list", value=antsJointFusion_workflow.lzin.target_image)
        )

        jointFusion = JointFusion()
        jointFusion._cmd = experiment_configuration[configkey].get("executable")
        # antsJointFusion_task = Nipype1Task(jointFusion)

        # if environment_configuration["set_threads"]:
        #     jointFusion.inputs.num_threads = experiment_configuration[configkey].get(
        #         "threads"
        #     )
        #     # Set the number of threads to be used by ITK
        #     # antsJointFusion_task = jointFusion
        #     # antsJointFusion_task.set_default_num_threads(
        #     #     experiment_configuration[configkey].get("threads")
        #     # )
        #     # antsJointFusion_task.inputs.num_threads = experiment_configuration[
        #     #     configkey
        #     # ].get("threads")
        #     antsJointFusion_task = Nipype1Task(jointFusion)

        #     antsJointFusion_task.inputs.num_threads = experiment_configuration[
        #         configkey
        #     ].get("threads")
        # else:
        #     # Use the default number of threads
        #     antsJointFusion_task = Nipype1Task(jointFusion)
        jointFusion.inputs.num_threads = -1
        antsJointFusion_task = Nipype1Task(jointFusion)
        antsJointFusion_task.qsub_args = f"-l h_rt=02:30:00 -q all.q -l mem_free=15G -pe smp {experiment_configuration[configkey].get('threads')}"
        # antsJointFusion_task.inputs.num_threads = -1
        antsJointFusion_task.inputs.atlas_image = (
            antsJointFusion_workflow.lzin.atlas_image
        )
        antsJointFusion_task.inputs.atlas_segmentation_image = (
            antsJointFusion_workflow.lzin.atlas_segmentation_image
        )
        antsJointFusion_task.inputs.mask_image = (
            antsJointFusion_workflow.lzin.mask_image
        )
        antsJointFusion_task.inputs.target_image = (
            antsJointFusion_workflow.to_list.lzout.out
        )
        antsJointFusion_task.inputs.alpha = experiment_configuration[configkey].get(
            "alpha"
        )
        antsJointFusion_task.inputs.beta = experiment_configuration[configkey].get(
            "beta"
        )
        antsJointFusion_task.inputs.dimension = experiment_configuration[configkey].get(
            "dimension"
        )
        antsJointFusion_task.inputs.out_label_fusion = experiment_configuration[
            configkey
        ].get("out_label_fusion")
        antsJointFusion_task.inputs.search_radius = experiment_configuration[
            configkey
        ].get("search_radius")
        antsJointFusion_task.inputs.verbose = experiment_configuration[configkey].get(
            "verbose"
        )

        antsJointFusion_workflow.add(antsJointFusion_task)
        antsJointFusion_workflow.set_output(
            [("out_label_fusion", antsJointFusion_task.lzout.out_label_fusion)]
        )

        return antsJointFusion_workflow

    @pydra.mark.task
    def get_firstT1(inputVolumes, inputVolumeTypes):
        inputVolumesT1 = []
        # print(f"inputVolumeTypes: {inputVolumeTypes}")
        if inputVolumeTypes != None:
            for index, ele in enumerate(inputVolumeTypes):
                # print(f"ele: {ele}")
                if ele == "T1":
                    inputVolumesT1.append(inputVolumes[index])
            # print(f"inputVolumesT1: {inputVolumesT1}")
        return inputVolumesT1[0]

    @pydra.mark.task
    def print_inputs(input, input_type):
        print(f"{input_type}: {input}")
        return input

    # Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow4)
    source_node = pydra.Workflow(
        # plugin="cf",
        name="source_node",
        input_spec=["input_data_with_T2", "input_data_without_T2"],
        cache_dir=experiment_configuration["cache_dir"],
    )
    source_node.inputs.input_data_with_T2 = input_data_dictionary.get(
        "sessions_with_T2"
    )
    source_node.inputs.input_data_without_T2 = input_data_dictionary.get(
        "sessions_without_T2"
    )

    # Make the processing workflow to take the input data, process it, and pass the processed data to the sink_node

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        processing_node_with_T2 = pydra.Workflow(
            plugin="cf",
            name="processing_node_with_T2",
            input_spec=["input_data_with_T2"],
            input_data_with_T2=source_node.lzin.input_data_with_T2,
        ).split("input_data_with_T2")

    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        processing_node_without_T2 = pydra.Workflow(
            plugin="cf",
            name="processing_node_without_T2",
            input_spec=["input_data_without_T2"],
            input_data_without_T2=source_node.lzin.input_data_without_T2,
        ).split("input_data_without_T2")

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        # Fill prejointFusion_node_with_T2 with the tasks coming before JointFusion
        prejointFusion_node_with_T2 = pydra.Workflow(
            plugin="cf",
            name="prejointFusion_node_with_T2",
            input_spec=["input_data"],
            input_data=processing_node_with_T2.lzin.input_data_with_T2,
        )
        prejointFusion_node_with_T2.add(
            get_inputs_workflow(my_source_node=prejointFusion_node_with_T2)
        )

        prejointFusion_node_with_T2.add(
            get_firstT1(
                name="get_firstT1",
                inputVolumes=prejointFusion_node_with_T2.inputs_workflow.lzout.inputVolumes,
                inputVolumeTypes=prejointFusion_node_with_T2.inputs_workflow.lzout.inputVolumeTypes,
            )
        )
        prejointFusion_node_with_T2.add(
            make_bcd_workflow1(
                inputVolume=prejointFusion_node_with_T2.get_firstT1.lzout.out,
                inputLandmarksEMSP=prejointFusion_node_with_T2.inputs_workflow.lzout.inputLandmarksEMSP,
            )
        )
        prejointFusion_node_with_T2.add(
            make_roi_workflow1(
                inputVolume=prejointFusion_node_with_T2.bcd_workflow1.lzout.outputResampledVolume
            )
        )
        prejointFusion_node_with_T2.add(
            make_landmarkInitializer_workflow1(
                inputMovingLandmarkFilename=prejointFusion_node_with_T2.bcd_workflow1.lzout.outputLandmarksInInputSpace
            )
        )
        prejointFusion_node_with_T2.add(
            make_landmarkInitializer_workflow2(
                inputFixedLandmarkFilename=prejointFusion_node_with_T2.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace
            )
        )
        prejointFusion_node_with_T2.add(
            make_resample_workflow1(
                inputVolume=prejointFusion_node_with_T2.get_firstT1.lzout.out,
                warpTransform=prejointFusion_node_with_T2.landmarkInitializer_workflow1.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_with_T2.add(
            make_roi_workflow2(
                inputVolume=prejointFusion_node_with_T2.roi_workflow1.lzout.outputVolume
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsRegistration_workflow1(
                fixed_image=prejointFusion_node_with_T2.roi_workflow1.lzout.outputVolume,
                fixed_image_masks=prejointFusion_node_with_T2.roi_workflow2.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_with_T2.landmarkInitializer_workflow2.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsRegistration_workflow2(
                fixed_image=prejointFusion_node_with_T2.roi_workflow1.lzout.outputVolume,
                fixed_image_masks=prejointFusion_node_with_T2.roi_workflow2.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_with_T2.antsRegistration_workflow1.lzout.composite_transform,
            )
        )
        prejointFusion_node_with_T2.add(
            make_abc_workflow1(
                inputVolumes=prejointFusion_node_with_T2.inputs_workflow.lzout.inputVolumes,
                inputVolumeTypes=prejointFusion_node_with_T2.inputs_workflow.lzout.inputVolumeTypes,
                inputVolumeCropped=prejointFusion_node_with_T2.roi_workflow1.lzout.outputVolume,
                restoreState=prejointFusion_node_with_T2.antsRegistration_workflow2.lzout.save_state,
            )
        )
        prejointFusion_node_with_T2.add(
            make_resample_workflow2(
                referenceVolume=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                warpTransform=prejointFusion_node_with_T2.abc_workflow1.lzout.atlasToSubjectTransform,
                inputVolume=experiment_configuration["BRAINSResample2"].get(
                    "inputVolumes"
                ),
            ).split("inputVolume")
        )

        prejointFusion_node_with_T2.add(
            make_resample_workflow3(
                referenceVolume=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                inputVolume=prejointFusion_node_with_T2.abc_workflow1.lzout.t2_average,
            )
        )

        prejointFusion_node_with_T2.add(
            make_createLabelMapFromProbabilityMaps_workflow1(
                inputProbabilityVolume=prejointFusion_node_with_T2.abc_workflow1.lzout.posteriors,
                nonAirRegionMask=prejointFusion_node_with_T2.roi_workflow2.lzout.outputROIMaskVolume,
            )
        )
        prejointFusion_node_with_T2.add(
            make_landmarkInitializer_workflow3(
                inputMovingLandmarkFilename=experiment_configuration[
                    "BRAINSLandmarkInitializer3"
                ].get("inputMovingLandmarkFilename"),
                inputFixedLandmarkFilename=prejointFusion_node_with_T2.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace,
            ).split("inputMovingLandmarkFilename")
        )
        prejointFusion_node_with_T2.add(
            make_roi_workflow3(
                inputVolume=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsRegistration_workflow3_with_T2(
                fixed_image_T1=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                fixed_image_T2=prejointFusion_node_with_T2.abc_workflow1.lzout.t2_average,
                fixed_image_masks=prejointFusion_node_with_T2.roi_workflow3.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_with_T2.landmarkInitializer_workflow3.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsApplyTransforms_workflow(
                index=1,
                output_image_end=experiment_configuration["ANTSApplyTransforms1"].get(
                    "output_image_end"
                ),
                reference_image=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                transform=prejointFusion_node_with_T2.antsRegistration_workflow3.lzout.composite_transform,
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsApplyTransforms_workflow(
                index=2,
                output_image_end=experiment_configuration["ANTSApplyTransforms2"].get(
                    "output_image_end"
                ),
                reference_image=prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                transform=prejointFusion_node_with_T2.antsRegistration_workflow3.lzout.composite_transform,
            )
        )
        prejointFusion_node_with_T2.add(
            make_antsApplyTransforms_workflow(
                index=3,
                output_image_end=experiment_configuration["ANTSApplyTransforms3"].get(
                    "output_image_end"
                ),
                reference_image=prejointFusion_node_with_T2.abc_workflow1.lzout.t2_average,
                transform=prejointFusion_node_with_T2.antsRegistration_workflow3.lzout.composite_transform,
            )
        )

    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        # Fill prejointFusion_node_without_T2 with the tasks coming before JointFusion
        prejointFusion_node_without_T2 = pydra.Workflow(
            plugin="cf",
            name="prejointFusion_node_without_T2",
            input_spec=["input_data"],
            input_data=processing_node_without_T2.lzin.input_data_without_T2,
        )
        prejointFusion_node_without_T2.add(
            get_inputs_workflow(my_source_node=prejointFusion_node_without_T2)
        )

        prejointFusion_node_without_T2.add(
            get_firstT1(
                name="get_firstT1",
                inputVolumes=prejointFusion_node_without_T2.inputs_workflow.lzout.inputVolumes,
                inputVolumeTypes=prejointFusion_node_without_T2.inputs_workflow.lzout.inputVolumeTypes,
            )
        )
        prejointFusion_node_without_T2.add(
            make_bcd_workflow1(
                inputVolume=prejointFusion_node_without_T2.get_firstT1.lzout.out,
                inputLandmarksEMSP=prejointFusion_node_without_T2.inputs_workflow.lzout.inputLandmarksEMSP,
            )
        )
        prejointFusion_node_without_T2.add(
            make_roi_workflow1(
                inputVolume=prejointFusion_node_without_T2.bcd_workflow1.lzout.outputResampledVolume
            )
        )
        prejointFusion_node_without_T2.add(
            make_landmarkInitializer_workflow1(
                inputMovingLandmarkFilename=prejointFusion_node_without_T2.bcd_workflow1.lzout.outputLandmarksInInputSpace
            )
        )
        prejointFusion_node_without_T2.add(
            make_landmarkInitializer_workflow2(
                inputFixedLandmarkFilename=prejointFusion_node_without_T2.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace
            )
        )
        prejointFusion_node_without_T2.add(
            make_resample_workflow1(
                inputVolume=prejointFusion_node_without_T2.get_firstT1.lzout.out,
                warpTransform=prejointFusion_node_without_T2.landmarkInitializer_workflow1.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_without_T2.add(
            make_roi_workflow2(
                inputVolume=prejointFusion_node_without_T2.roi_workflow1.lzout.outputVolume
            )
        )
        prejointFusion_node_without_T2.add(
            make_antsRegistration_workflow1(
                fixed_image=prejointFusion_node_without_T2.roi_workflow1.lzout.outputVolume,
                fixed_image_masks=prejointFusion_node_without_T2.roi_workflow2.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_without_T2.landmarkInitializer_workflow2.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_without_T2.add(
            make_antsRegistration_workflow2(
                fixed_image=prejointFusion_node_without_T2.roi_workflow1.lzout.outputVolume,
                fixed_image_masks=prejointFusion_node_without_T2.roi_workflow2.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_without_T2.antsRegistration_workflow1.lzout.composite_transform,
            )
        )
        prejointFusion_node_without_T2.add(
            make_abc_workflow1(
                inputVolumes=prejointFusion_node_without_T2.inputs_workflow.lzout.inputVolumes,
                inputVolumeTypes=prejointFusion_node_without_T2.inputs_workflow.lzout.inputVolumeTypes,
                inputVolumeCropped=prejointFusion_node_without_T2.roi_workflow1.lzout.outputVolume,
                restoreState=prejointFusion_node_without_T2.antsRegistration_workflow2.lzout.save_state,
            )
        )
        prejointFusion_node_without_T2.add(
            make_resample_workflow2(
                referenceVolume=prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average,
                warpTransform=prejointFusion_node_without_T2.abc_workflow1.lzout.atlasToSubjectTransform,
                inputVolume=experiment_configuration["BRAINSResample2"].get(
                    "inputVolumes"
                ),
            ).split("inputVolume")
        )
        prejointFusion_node_without_T2.add(
            make_createLabelMapFromProbabilityMaps_workflow1(
                inputProbabilityVolume=prejointFusion_node_without_T2.abc_workflow1.lzout.posteriors,
                nonAirRegionMask=prejointFusion_node_without_T2.roi_workflow2.lzout.outputROIMaskVolume,
            )
        )
        prejointFusion_node_without_T2.add(
            make_landmarkInitializer_workflow3(
                inputMovingLandmarkFilename=experiment_configuration[
                    "BRAINSLandmarkInitializer3"
                ].get("inputMovingLandmarkFilename"),
                inputFixedLandmarkFilename=prejointFusion_node_without_T2.bcd_workflow1.lzout.outputLandmarksInACPCAlignedSpace,
            ).split("inputMovingLandmarkFilename")
        )
        prejointFusion_node_without_T2.add(
            make_roi_workflow3(
                inputVolume=prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average
            )
        )
        prejointFusion_node_without_T2.add(
            make_antsRegistration_workflow3_without_T2(
                fixed_image=prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average,
                fixed_image_masks=prejointFusion_node_without_T2.roi_workflow3.lzout.outputROIMaskVolume,
                initial_moving_transform=prejointFusion_node_without_T2.landmarkInitializer_workflow3.lzout.outputTransformFilename,
            )
        )
        prejointFusion_node_without_T2.add(
            make_antsApplyTransforms_workflow(
                index=1,
                output_image_end=experiment_configuration["ANTSApplyTransforms1"].get(
                    "output_image_end"
                ),
                reference_image=prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average,
                transform=prejointFusion_node_without_T2.antsRegistration_workflow3.lzout.composite_transform,
            )
        )
        prejointFusion_node_without_T2.add(
            make_antsApplyTransforms_workflow(
                index=2,
                output_image_end=experiment_configuration["ANTSApplyTransforms2"].get(
                    "output_image_end"
                ),
                reference_image=prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average,
                transform=prejointFusion_node_without_T2.antsRegistration_workflow3.lzout.composite_transform,
            )
        )

    # Combine the results of the processing to this point into lists as input to JointFusion
    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        prejointFusion_node_with_T2.set_output(
            [
                ("bcd_workflow1", prejointFusion_node_with_T2.bcd_workflow1.lzout.all_),
                ("roi_workflow1", prejointFusion_node_with_T2.roi_workflow1.lzout.all_),
                (
                    "landmarkInitializer_workflow1",
                    prejointFusion_node_with_T2.landmarkInitializer_workflow1.lzout.all_,
                ),
                (
                    "landmarkInitializer_workflow2",
                    prejointFusion_node_with_T2.landmarkInitializer_workflow2.lzout.all_,
                ),
                (
                    "resample_workflow1",
                    prejointFusion_node_with_T2.resample_workflow1.lzout.all_,
                ),
                ("roi_workflow2", prejointFusion_node_with_T2.roi_workflow2.lzout.all_),
                (
                    "antsRegistration_workflow1",
                    prejointFusion_node_with_T2.antsRegistration_workflow1.lzout.all_,
                ),
                (
                    "antsRegistration_workflow2",
                    prejointFusion_node_with_T2.antsRegistration_workflow2.lzout.all_,
                ),
                ("abc_workflow1", prejointFusion_node_with_T2.abc_workflow1.lzout.all_),
                (
                    "resample_workflow2",
                    prejointFusion_node_with_T2.resample_workflow2.lzout.all_,
                ),
                (
                    "resample_workflow3",
                    prejointFusion_node_with_T2.resample_workflow3.lzout.all_,
                ),
                (
                    "createLabelMapFromProbabilityMaps_workflow1",
                    prejointFusion_node_with_T2.createLabelMapFromProbabilityMaps_workflow1.lzout.all_,
                ),
                (
                    "landmarkInitializer_workflow3",
                    prejointFusion_node_with_T2.landmarkInitializer_workflow3.lzout.all_,
                ),
                ("roi_workflow3", prejointFusion_node_with_T2.roi_workflow3.lzout.all_),
                (
                    "antsRegistration_workflow3",
                    prejointFusion_node_with_T2.antsRegistration_workflow3.lzout.all_,
                ),
                (
                    "antsApplyTransforms_workflow1",
                    prejointFusion_node_with_T2.antsApplyTransforms_workflow1.lzout.all_,
                ),
                (
                    "antsApplyTransforms_workflow2",
                    prejointFusion_node_with_T2.antsApplyTransforms_workflow2.lzout.all_,
                ),
                (
                    "atlas_image",
                    prejointFusion_node_with_T2.antsRegistration_workflow3.lzout.warped_image,
                ),
                (
                    "atlas_segmentation_image",
                    prejointFusion_node_with_T2.antsApplyTransforms_workflow2.lzout.output_image,
                ),
                (
                    "target_image",
                    prejointFusion_node_with_T2.abc_workflow1.lzout.t1_average,
                ),
                (
                    "mask_image",
                    prejointFusion_node_with_T2.roi_workflow2.lzout.outputROIMaskVolume,
                ),
            ]
        )

    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        prejointFusion_node_without_T2.set_output(
            [
                (
                    "bcd_workflow1",
                    prejointFusion_node_without_T2.bcd_workflow1.lzout.all_,
                ),
                (
                    "roi_workflow1",
                    prejointFusion_node_without_T2.roi_workflow1.lzout.all_,
                ),
                (
                    "landmarkInitializer_workflow1",
                    prejointFusion_node_without_T2.landmarkInitializer_workflow1.lzout.all_,
                ),
                (
                    "landmarkInitializer_workflow2",
                    prejointFusion_node_without_T2.landmarkInitializer_workflow2.lzout.all_,
                ),
                (
                    "resample_workflow1",
                    prejointFusion_node_without_T2.resample_workflow1.lzout.all_,
                ),
                (
                    "roi_workflow2",
                    prejointFusion_node_without_T2.roi_workflow2.lzout.all_,
                ),
                (
                    "antsRegistration_workflow1",
                    prejointFusion_node_without_T2.antsRegistration_workflow1.lzout.all_,
                ),
                (
                    "antsRegistration_workflow2",
                    prejointFusion_node_without_T2.antsRegistration_workflow2.lzout.all_,
                ),
                (
                    "abc_workflow1",
                    prejointFusion_node_without_T2.abc_workflow1.lzout.all_,
                ),
                (
                    "resample_workflow2",
                    prejointFusion_node_without_T2.resample_workflow2.lzout.all_,
                ),
                (
                    "createLabelMapFromProbabilityMaps_workflow1",
                    prejointFusion_node_without_T2.createLabelMapFromProbabilityMaps_workflow1.lzout.all_,
                ),
                (
                    "landmarkInitializer_workflow3",
                    prejointFusion_node_without_T2.landmarkInitializer_workflow3.lzout.all_,
                ),
                (
                    "roi_workflow3",
                    prejointFusion_node_without_T2.roi_workflow3.lzout.all_,
                ),
                (
                    "antsRegistration_workflow3",
                    prejointFusion_node_without_T2.antsRegistration_workflow3.lzout.all_,
                ),
                (
                    "antsApplyTransforms_workflow1",
                    prejointFusion_node_without_T2.antsApplyTransforms_workflow1.lzout.all_,
                ),
                (
                    "antsApplyTransforms_workflow2",
                    prejointFusion_node_without_T2.antsApplyTransforms_workflow2.lzout.all_,
                ),
                (
                    "atlas_image",
                    prejointFusion_node_without_T2.antsRegistration_workflow3.lzout.warped_image,
                ),
                (
                    "atlas_segmentation_image",
                    prejointFusion_node_without_T2.antsApplyTransforms_workflow2.lzout.output_image,
                ),
                (
                    "target_image",
                    prejointFusion_node_without_T2.abc_workflow1.lzout.t1_average,
                ),
                (
                    "mask_image",
                    prejointFusion_node_without_T2.roi_workflow2.lzout.outputROIMaskVolume,
                ),
            ]
        )

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        jointFusion_node_with_T2 = pydra.Workflow(
            plugin="cf",
            name="jointFusion_node_with_T2",
            input_spec=[
                "atlas_image",
                "atlas_segmentation_image",
                "target_image",
                "mask_image",
            ],
            atlas_image=prejointFusion_node_with_T2.lzout.atlas_image,
            atlas_segmentation_image=prejointFusion_node_with_T2.lzout.atlas_segmentation_image,
            target_image=prejointFusion_node_with_T2.lzout.target_image,
            mask_image=prejointFusion_node_with_T2.lzout.mask_image,
        )
        jointFusion_node_with_T2.add(
            make_antsJointFusion_workflow1(
                atlas_image=jointFusion_node_with_T2.lzin.atlas_image,
                atlas_segmentation_image=jointFusion_node_with_T2.lzin.atlas_segmentation_image,
                target_image=jointFusion_node_with_T2.lzin.target_image,
                mask_image=jointFusion_node_with_T2.lzin.mask_image,
            )
        )
        jointFusion_node_with_T2.set_output(
            [
                (
                    "jointFusion_node_with_T2_out",
                    jointFusion_node_with_T2.antsJointFusion_workflow1.lzout.out_label_fusion,
                )
            ]
        )

    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        jointFusion_node_without_T2 = pydra.Workflow(
            plugin="cf",
            name="jointFusion_node_without_T2",
            input_spec=[
                "atlas_image",
                "atlas_segmentation_image",
                "target_image",
                "mask_image",
            ],
            atlas_image=prejointFusion_node_without_T2.lzout.atlas_image,
            atlas_segmentation_image=prejointFusion_node_without_T2.lzout.atlas_segmentation_image,
            target_image=prejointFusion_node_without_T2.lzout.target_image,
            mask_image=prejointFusion_node_without_T2.lzout.mask_image,
        )
        jointFusion_node_without_T2.add(
            make_antsJointFusion_workflow1(
                atlas_image=jointFusion_node_without_T2.lzin.atlas_image,
                atlas_segmentation_image=jointFusion_node_without_T2.lzin.atlas_segmentation_image,
                target_image=jointFusion_node_without_T2.lzin.target_image,
                mask_image=jointFusion_node_without_T2.lzin.mask_image,
            )
        )
        jointFusion_node_without_T2.set_output(
            [
                (
                    "jointFusion_node_without_T2_out",
                    jointFusion_node_without_T2.antsJointFusion_workflow1.lzout.out_label_fusion,
                )
            ]
        )

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        processing_node_with_T2.add(prejointFusion_node_with_T2)
    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        processing_node_without_T2.add(prejointFusion_node_without_T2)
    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        processing_node_with_T2.add(jointFusion_node_with_T2)
    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        processing_node_without_T2.add(jointFusion_node_without_T2)

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        processing_node_with_T2.set_output(
            [
                (
                    "prejointFusion_out",
                    processing_node_with_T2.prejointFusion_node_with_T2.lzout.all_,
                ),
                (
                    "jointFusion_out",
                    processing_node_with_T2.jointFusion_node_with_T2.lzout.all_,
                ),
            ]
        )
    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        processing_node_without_T2.set_output(
            [
                (
                    "prejointFusion_out",
                    processing_node_without_T2.prejointFusion_node_without_T2.lzout.all_,
                ),
                (
                    "jointFusion_out",
                    processing_node_without_T2.jointFusion_node_without_T2.lzout.all_,
                ),
            ]
        )

    if len(input_data_dictionary["sessions_with_T2"]) > 0:
        source_node.add(processing_node_with_T2)
    if len(input_data_dictionary["sessions_without_T2"]) > 0:
        source_node.add(processing_node_without_T2)

    # Set the output of the source node to the same as the output of the sink_node
    if (
        len(input_data_dictionary["sessions_without_T2"]) > 0
        and len(input_data_dictionary["sessions_with_T2"]) > 0
    ):
        source_node.set_output(
            [
                ("out_with_T2", source_node.processing_node_with_T2.lzout.all_),
                ("out_without_T2", source_node.processing_node_without_T2.lzout.all_),
            ]
        )
    elif len(input_data_dictionary["sessions_with_T2"]) > 0:
        source_node.set_output(
            [
                ("out_with_T2", source_node.processing_node_with_T2.lzout.all_),
            ]
        )
    elif len(input_data_dictionary["sessions_without_T2"]) > 0:
        source_node.set_output(
            [
                ("out_without_T2", source_node.processing_node_without_T2.lzout.all_),
            ]
        )


    with pydra.Submitter(
        "sge",
        write_output_files=False,
        qsub_args="-q all.q",
        default_qsub_args="-q all.q -pe smp 8",
        indirect_submit_host="argon-login-2",
        max_job_array_length=100,
        poll_delay=5,
        default_threads_per_task=8,
        poll_for_result_file=True,
        collect_jobs_delay=30,
        polls_before_checking_evicted=12,
        max_mem_free=450,
    ) as sub:
        sub(source_node)

    @pydra.mark.task
    def copy(output_directory, session):
        p = Path(output_directory)
        output_files = []
        output_dir = Path(experiment_configuration.get("output_dir")) / Path(session)
        output_dir.mkdir(exist_ok=True, parents=True)
        # Find all files created in the source_node workflow (the entire pipeline) that do not start with an underscore (not _result.pklz or _task.pklz)
        for cache_filepath in p.glob("**/[!_]*"):
            output_files.append(cache_filepath)
            output_filepath = output_dir / cache_filepath.name
            # Remove a file if it already exists so it can be replaced by a new file or hardlink
            if output_filepath.exists():
                output_filepath.unlink()
            if environment_configuration.get("hard_links"):
                print(f"Hardlinking {cache_filepath} to {output_filepath}")
                cache_filepath.link_to(output_filepath)
            else:
                print(f"Copying {cache_filepath} to {output_filepath}")
                copyfile(cache_filepath, output_filepath)
        return output_files

    f = open(source_node.output_dir / "_task.pklz", "rb")
    data = pickle.load(f)
    f.close()

    # After processing all the files, copy the results to a local output directory
    sessions_with_T2 = [
        sess_data["session"]
        for sess_data in data.processing_node_with_T2.inputs.input_data_with_T2
    ]
    sessions_without_T2 = [
        sess_data["session"]
        for sess_data in data.processing_node_without_T2.inputs.input_data_without_T2
    ]

    sink_node = pydra.Workflow(
        name="sink_node",
        input_spec=[
            "output_directory_with_T2",
            "session_with_T2",
            "output_directory_without_T2",
            "session_without_T2",
        ],
        output_directory_with_T2=data.processing_node_with_T2.output_dir,
        session_with_T2=sessions_with_T2,
        output_directory_without_T2=data.processing_node_without_T2.output_dir,
        session_without_T2=sessions_without_T2,
    )
    sink_node.add(
        copy(
            name="copy_with_T2",
            output_directory=sink_node.lzin.output_directory_with_T2,
            session=sink_node.lzin.session_with_T2,
        ).split(("output_directory", "session"))
    )
    sink_node.add(
        copy(
            name="copy_without_T2",
            output_directory=sink_node.lzin.output_directory_without_T2,
            session=sink_node.lzin.session_without_T2,
        ).split(("output_directory", "session"))
    )
    sink_node.set_output(
        [
            ("output_with_T2", sink_node.copy_with_T2.lzout.out),
            ("output_without_T2", sink_node.copy_without_T2.lzout.out),
        ]
    )
    with pydra.Submitter(plugin="cf") as sub:
        sub(sink_node)
