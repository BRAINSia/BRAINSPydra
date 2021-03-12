from pydra.tasks.nipype1.utils import Nipype1Task
import json
from nipype.interfaces.ants import ApplyTransforms
import pydra

wf = pydra.Workflow(name="wf", input_spec=["input"], input="91300")
antsApplyTransforms_workflow = pydra.Workflow(name="applyTransforms", input_spec=["atlas_id"], atlas_id="91300")
antsApplyTransforms_task = Nipype1Task(ApplyTransforms())

antsApplyTransforms_task.inputs.dimension       = 3
antsApplyTransforms_task.inputs.float           = False
antsApplyTransforms_task.inputs.input_image     = "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/91300/wholeBrain_label.nii.gz"
antsApplyTransforms_task.inputs.interpolation   = "MultiLabel"
antsApplyTransforms_task.inputs.output_image    = "91300fswm_2_subj_lbl.nii.gz"
antsApplyTransforms_task.inputs.reference_image = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/t1_average_BRAINSABC.nii.gz"
antsApplyTransforms_task.inputs.transforms      = "/mnt/c/2020_Grad_School/Research/output_dir/sub-052823_ses-43817_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5"
wf.add(antsApplyTransforms_workflow)


antsApplyTransforms_workflow.add(antsApplyTransforms_task)
antsApplyTransforms_workflow.set_output([("output_image", antsApplyTransforms_task.lzout.output_image)])
wf.set_output([("out", antsApplyTransforms_workflow.lzout.output_image)])

with pydra.Submitter(plugin="cf") as sub:
    sub(antsApplyTransforms_workflow)
result = antsApplyTransforms_workflow.result()
print(result)