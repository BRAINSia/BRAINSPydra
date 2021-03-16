from pydra.tasks.nipype1.utils import Nipype1Task
import json
from nipype.interfaces.ants import AntsJointFusion

# with open("/mnt/c/2020_Grad_School/Research/BRAINSPydra/config_experimental.json") as f:
#     experiment_configuration = json.load(f)

antsJointFusion_task = AntsJointFusion()
# antsJointFusion_task = Nipype1Task(AntsJointFusion())
antsJointFusion_task.inputs.alpha       = 0.1
antsJointFusion_task.inputs.atlas_image = [
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/13512_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/14165_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/21003_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/23163_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/23687_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/27612_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/35888_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/37960_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/49543_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/52712_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/53657_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/55648_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/58446_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/68653_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/75094_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/75909_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2subject.nii.gz'],
    # ['/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2subject.nii.gz'],
    ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/93075_2subject.nii.gz'],
    ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/99056_2subject.nii.gz']]
antsJointFusion_task.inputs.atlas_segmentation_image = [
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/13512_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/14165_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/21003_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/23163_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/23687_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/27612_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/35888_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/37960_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/49543_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/52712_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/53657_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/55648_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/58446_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/68653_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/75094_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/75909_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91300_2_subj_lbl.nii.gz",
    # "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/91626_2_subj_lbl.nii.gz",
    "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/93075_2_subj_lbl.nii.gz",
    "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/99056_2_subj_lbl.nii.gz"]

antsJointFusion_task.inputs.beta = 2.0
antsJointFusion_task.inputs.dimension = 3
antsJointFusion_task.inputs.mask_image = "/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/fixedImageROIAutoMask.nii.gz"
antsJointFusion_task.inputs.out_label_fusion = "JointFusion_HDAtlas20_2015_label.nii.gz"
antsJointFusion_task.inputs.search_radius = [3]
antsJointFusion_task.inputs.target_image = ['/localscratch/Users/cjohnson30/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz']
antsJointFusion_task.inputs.verbose = True

# print(antsJointFusion_task.cmdline)

res = antsJointFusion_task()
print(res)
