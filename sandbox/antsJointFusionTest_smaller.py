from nipype.interfaces.ants import AntsJointFusion
import pydra

antsJointFusion_task = AntsJointFusion()
antsJointFusion_task.inputs.atlas_image = [
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2subject.nii.gz']
    ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2subject.nii.gz'],
    ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2subject.nii.gz'],
]
antsJointFusion_task.inputs.atlas_segmentation_image = [
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2_subj_lbl.nii.gz"
    "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2_subj_lbl.nii.gz",
    "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2_subj_lbl.nii.gz",
]

antsJointFusion_task.inputs.beta = 2.0
antsJointFusion_task.inputs.dimension = 3
antsJointFusion_task.inputs.search_radius = [3]
antsJointFusion_task.inputs.target_image = ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz']
antsJointFusion_task.inputs.mask_image = "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz"
# antsJointFusion_task.inputs.target_image = ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz']
# antsJointFusion_task.inputs.mask_image = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz"
antsJointFusion_task.inputs.out_label_fusion = "JointFusion_HDAtlas20_2015_label.nii.gz"
antsJointFusion_task.inputs.verbose = True
# antsJointFusion_task.set_default_num_threads(28)
antsJointFusion_task.inputs.num_threads = 28

# print(antsJointFusion_task.input_spec)
# antsJointFusion_task.inputs.num_threads(56)
# antsJointFusion_task.set_default_num_threads(24)

print(antsJointFusion_task.cmdline)
result = antsJointFusion_task.run()
print(result)
