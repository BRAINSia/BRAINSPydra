from pydra.tasks.nipype1.utils import Nipype1Task
from nipype.interfaces import ants
import pydra
import copy, pprint
from nipype.interfaces.ants import Registration
import attr

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

# antsRegistration_task = Registration()

registration = Registration()
# registration.inputs.num_threads = 8
# registration._cmd = "/Shared/johnsonhj/Binaries/Linux/CentOS/Core/apps/BRAINSTools/20200913/bin/antsRegistration"
# # if environment_configuration["set_threads"]:
#     # Set the number of threads to be used by ITK
# antsRegistration_task = registration
# antsRegistration_task.set_default_num_threads(8)
# antsRegistration_task.inputs.num_threads = 8

registration.inputs.num_threads = 8
#     antsRegistration_task = registration
#     antsRegistration_task.set_default_num_threads(1)
#     antsRegistration_task.inputs.num_threads = 1
#     antsRegistration_task = Nipype1Task(antsRegistration_task)
antsRegistration_task = Nipype1Task(registration)
# else:
#     # Use the default number of threads (1)
#     antsRegistration_task = Nipype1Task(registration)

antsRegistration_task.inputs.num_threads = 8

# antsRegistration_task = Nipype1Task(registration)





# antsRegistration_task.inp

# antsRegistration_task.set_default_num_threads(28)
# antsRegistration_task.inputs.num_threads = 28
# antsRegistration_task = Nipype1Task(antsRegistration_task)

# # bcd_task.input_spec.fields

# antsRegistration_task.input_spec.fields.append(SGE_THREADS_INPUT_SPEC)
# # print(antsRegistration_task.input_spec.fields)

# updated_input_spec = antsRegistration_task.input_spec
# antsRegistration_task.input_spec = updated_input_spec
# # antsRegistration_task = Registration(input_spec=updated_input_spec)

# # antsRegistration_task.input_spec = updated_input_spec

# # # Add an input spec field for the number of SGE Threads to be used
# # bcd_task = ShellCommandTask(
# #     name=bcd_task.name,
# #     executable=bcd_task.inputs.executable,
# #     input_spec=updated_input_spec,
# #     output_spec=bcd_task.output_spec,
# # )

# # # print(bcd_task.input_spec)

# antsRegistration_task.inputs.sgeThreads = 4

antsRegistration_task.cache_dir="/Shared/sinapse/pydra-cjohnson/test"

antsRegistration_task.inputs.num_threads = 8

antsRegistration_task.inputs.fixed_image = "/Shared/sinapse/pydra-cjohnson/output_dir/sub-052823_ses-43817/Cropped_BCD_ACPC_Aligned.nii.gz"
antsRegistration_task.inputs.moving_image = "/Shared/johnsonhj/Binaries/Linux/CentOS/Core/apps/BRAINSTools/20200913/bin/Atlas/Atlas_20131115/template_t1_denoised_gaussian.nii.gz"
antsRegistration_task.inputs.fixed_image_masks = [
    "/Shared/sinapse/pydra-cjohnson/output_dir/sub-052823_ses-43817/fixedImageROIAutoMask.nii.gz",
    "/Shared/sinapse/pydra-cjohnson/output_dir/sub-052823_ses-43817/fixedImageROIAutoMask.nii.gz",
    "/Shared/sinapse/pydra-cjohnson/output_dir/sub-052823_ses-43817/fixedImageROIAutoMask.nii.gz",
]
antsRegistration_task.inputs.moving_image_masks = [
    "/Shared/johnsonhj/Binaries/Linux/CentOS/Core/apps/BRAINSTools/20200913/bin/Atlas/Atlas_20131115/template_headregion.nii.gz",
    "/Shared/johnsonhj/Binaries/Linux/CentOS/Core/apps/BRAINSTools/20200913/bin/Atlas/Atlas_20131115/template_headregion.nii.gz",
    "/Shared/johnsonhj/Binaries/Linux/CentOS/Core/apps/BRAINSTools/20200913/bin/Atlas/Atlas_20131115/template_headregion.nii.gz",
]
antsRegistration_task.inputs.output_transform_prefix = "AtlasToSubjectPreBABC_Rigid"
antsRegistration_task.inputs.initial_moving_transform = "/Shared/sinapse/pydra-cjohnson/output_dir/sub-052823_ses-43817/landmarkInitializer_atlas_to_subject_transform.h5"
antsRegistration_task.inputs.transforms = ["Rigid", "Affine", "Affine"]
antsRegistration_task.inputs.transform_parameters = [(0.1,), (0.1,), (0.1,)]
antsRegistration_task.inputs.number_of_iterations = [
    [1000, 1000, 1000],
    [1000, 1000, 500],
    [500, 500],
]
antsRegistration_task.inputs.dimension = 3
antsRegistration_task.inputs.write_composite_transform = True
antsRegistration_task.inputs.collapse_output_transforms = False
antsRegistration_task.inputs.verbose = True
antsRegistration_task.inputs.initialize_transforms_per_stage = True
antsRegistration_task.inputs.float = True
antsRegistration_task.inputs.metric = ["MI"] * 3
antsRegistration_task.inputs.metric_weight = [
    1
] * 3  # Default (value ignored currently by ANTs)
antsRegistration_task.inputs.radius_or_number_of_bins = [32] * 3
antsRegistration_task.inputs.sampling_strategy = ["Regular", "Regular", "Regular"]
antsRegistration_task.inputs.sampling_percentage = [0.5, 0.5, 0.5]
antsRegistration_task.inputs.convergence_threshold = [5.0e-8, 5.0e-8, 5.0e-7]
antsRegistration_task.inputs.convergence_window_size = [12] * 3
antsRegistration_task.inputs.smoothing_sigmas = [[3, 2, 1], [3, 2, 1], [1, 0]]
antsRegistration_task.inputs.sigma_units = ["vox"] * 3
antsRegistration_task.inputs.shrink_factors = [[8, 4, 2], [8, 4, 2], [2, 1]]
antsRegistration_task.inputs.use_estimate_learning_rate_once = [False, False, False]
antsRegistration_task.inputs.use_histogram_matching = [
    True,
    True,
    True,
]  # This is the default
antsRegistration_task.inputs.output_warped_image = "atlas2subjectRigid.nii.gz"
antsRegistration_task.inputs.output_inverse_warped_image = "subject2atlasRigid.nii.gz"
antsRegistration_task.inputs.winsorize_lower_quantile = 0.01
antsRegistration_task.inputs.winsorize_upper_quantile = 0.99



print(antsRegistration_task.inputs)



with pydra.Submitter(
    "sge",
    # qsub_args="-o /Shared/sinapse/pydra-cjohnson/log -e /Shared/sinapse/pydra-cjohnson/error -q all.q",
    write_output_files=False,
    qsub_args="-q HJ",
    # max_jobs=1500,
    indirect_submit_host="argon-login-2",
    max_job_array_length=50,
    # rerun=True
    poll_delay=5,
    default_threads_per_task=8,
    max_threads=500,
    poll_for_result_file=True,
    collect_jobs_delay=30,
    polls_before_checking_evicted=12,
) as sub:
    sub(antsRegistration_task)

# with pydra.Submitter(plugin="cf") as sub:
#     sub(antsRegistration_task)


# result = antsRegistration_task.result()
# print(result)
# print(antsRegistration_task.input_spec)
# print(antsRegistration_task.output_names)
# print(antsRegistration_task.lzout.composite_transform)
# res = antsRegistration_task()
# print(res)
# print(antsRegistration_task.cmdline)
# 'antsRegistration --collapse-output-transforms 0 --dimensionality 3 --initial-moving-transform [ trans.mat, 0 ] --initialize-transforms-per-stage 0 --interpolation Linear --output [ output_, output_warped_image.nii.gz ] --transform Affine[ 2.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32, Random, 0.05 ] --convergence [ 1500x200, 1e-08, 20 ] --smoothing-sigmas 1.0x0.0vox --shrink-factors 2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --transform SyN[ 0.25, 3.0, 0.0 ] --metric Mattes[ fixed1.nii, moving1.nii, 1, 32 ] --convergence [ 100x50x30, 1e-09, 20 ] --smoothing-sigmas 2.0x1.0x0.0vox --shrink-factors 3x2x1 --use-estimate-learning-rate-once 1 --use-histogram-matching 1 --winsorize-image-intensities [ 0.0, 1.0 ]  --write-composite-transform 1'
# antsRegistration_task.run()

# antsRegistration_taskistration_task = Nipype1Task(antsRegistration_task)
# print(antsRegistration_taskistration_task.cmdline)
