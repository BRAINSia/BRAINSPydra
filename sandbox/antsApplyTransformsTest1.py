from pydra.tasks.nipype1.utils import Nipype1Task
import json
from nipype.interfaces.ants import ApplyTransforms

antsApplyTransforms_task = Nipype1Task(ApplyTransforms())

antsApplyTransforms_task.inputs.dimension = 3
antsApplyTransforms_task.inputs.float = False
antsApplyTransforms_task.inputs.input_image = "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/91300/wholeBrain_label.nii.gz"
antsApplyTransforms_task.inputs.interpolation = "MultiLabel"
antsApplyTransforms_task.inputs.output_image = "91300fswm_2_subj_lbl.nii.gz"
antsApplyTransforms_task.inputs.reference_image = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz"
antsApplyTransforms_task.inputs.transforms = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5"

# print(applyTransforms.cmdline)
print(antsApplyTransforms_task.output_spec)
res = antsApplyTransforms_task()
print(res)
