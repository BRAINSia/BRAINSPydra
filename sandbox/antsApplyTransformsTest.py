from pydra.tasks.nipype1.utils import Nipype1Task
from nipype.interfaces import ants
import json


import copy, pprint
from nipype.interfaces.ants import Registration

with open("/mnt/c/2020_Grad_School/Research/BRAINSPydra/config_experimental.json") as f:
    experiment_configuration = json.load(f)

antsRegistration_task = Nipype1Task(Registration())
antsRegistration_task.inputs.fixed_image =              "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz"  # antsRegistration_workflow.lzin.fixed_image
antsRegistration_task.inputs.fixed_image_masks =        "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz"  # antsRegistration_workflow.lzin.fixed_image_masks
antsRegistration_task.inputs.initial_moving_transform = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/landmarkInitializer_91300_to_subject_transform.h5"  # antsRegistration_workflow.lzin.initial_moving_transform

configkey = 'ANTSRegistration3'

antsRegistration_task.inputs.moving_image = experiment_configuration[configkey].get('moving_image')
antsRegistration_task.inputs.moving_image_masks = experiment_configuration[configkey].get('moving_image_masks')
antsRegistration_task.inputs.save_state = experiment_configuration[configkey].get('save_state')
antsRegistration_task.inputs.transforms = experiment_configuration[configkey].get('transforms')
antsRegistration_task.inputs.transform_parameters = experiment_configuration[configkey].get('transform_parameters')
antsRegistration_task.inputs.number_of_iterations = experiment_configuration[configkey].get('number_of_iterations')
antsRegistration_task.inputs.dimension = experiment_configuration[configkey].get('dimensionality')
antsRegistration_task.inputs.write_composite_transform = experiment_configuration[configkey].get(
    'write_composite_transform')
antsRegistration_task.inputs.collapse_output_transforms = experiment_configuration[configkey].get(
    'collapse_output_transforms')
antsRegistration_task.inputs.verbose = experiment_configuration[configkey].get('verbose')
antsRegistration_task.inputs.initialize_transforms_per_stage = experiment_configuration[configkey].get(
    'initialize_transforms_per_stage')
antsRegistration_task.inputs.float = experiment_configuration[configkey].get('float')
antsRegistration_task.inputs.metric = experiment_configuration[configkey].get('metric')
antsRegistration_task.inputs.metric_weight = experiment_configuration[configkey].get('metric_weight')
antsRegistration_task.inputs.radius_or_number_of_bins = experiment_configuration[configkey].get(
    'radius_or_number_of_bins')
antsRegistration_task.inputs.sampling_strategy = experiment_configuration[configkey].get('sampling_strategy')
antsRegistration_task.inputs.sampling_percentage = experiment_configuration[configkey].get('sampling_percentage')
antsRegistration_task.inputs.convergence_threshold = experiment_configuration[configkey].get('convergence_threshold')
antsRegistration_task.inputs.convergence_window_size = experiment_configuration[configkey].get(
    'convergence_window_size')
antsRegistration_task.inputs.smoothing_sigmas = experiment_configuration[configkey].get('smoothing_sigmas')
antsRegistration_task.inputs.sigma_units = experiment_configuration[configkey].get('sigma_units')
antsRegistration_task.inputs.shrink_factors = experiment_configuration[configkey].get('shrink_factors')
antsRegistration_task.inputs.use_estimate_learning_rate_once = experiment_configuration[configkey].get(
    'use_estimate_learning_rate_once')
antsRegistration_task.inputs.use_histogram_matching = experiment_configuration[configkey].get('use_histogram_matching')
antsRegistration_task.inputs.winsorize_lower_quantile = experiment_configuration[configkey].get(
    'winsorize_lower_quantile')
antsRegistration_task.inputs.winsorize_upper_quantile = experiment_configuration[configkey].get(
    'winsorize_upper_quantile')

# Set the variables that set output file names
antsRegistration_task.inputs.output_transform_prefix = experiment_configuration[configkey].get(
    'output_transform_prefix')
antsRegistration_task.inputs.output_warped_image = experiment_configuration[configkey].get('output_warped_image')
antsRegistration_task.inputs.output_inverse_warped_image = experiment_configuration[configkey].get(
    'output_inverse_warped_image')

print(antsRegistration_task.input_spec)
# print(antsRegistration_task.output_names)
# print(antsRegistration_task.lzout.composite_transform)
res = antsRegistration_task()
print(res)
# print(antsRegistration_task.cmdline)
# 'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] --initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'
# antsRegistration_task.run()

# antsRegistration_taskistration_task = Nipype1Task(antsRegistration_task)
# print(antsRegistration_taskistration_task.cmdline)