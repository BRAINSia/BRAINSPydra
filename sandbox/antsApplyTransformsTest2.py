from pydra.tasks.nipype1.utils import Nipype1Task
import json
from nipype.interfaces.ants import ApplyTransforms
import pydra

@pydra.mark.task
def get_self(x):
    print(x)
    return x

# with open("/mnt/c/2020_Grad_School/Research/BRAINSPydra/config_experimental.json") as f:
#     experiment_configuration = json.load(f)
input_image = ["/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/91300/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/99056/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/91626/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/93075/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/53657/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/75094/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/75909/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/55648/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/27612/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/49543/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/58446/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/52712/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/68653/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/37960/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/35888/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/23687/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/14165/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/13512/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/23163/wholeBrain_label.nii.gz",
                                                   # "/mnt/c/2020_Grad_School/Research/wf_ref/20160523_HDAdultAtlas/21003/wholeBrain_label.nii.gz"
                                                   ]

processing_node = pydra.Workflow(name="processing_node", input_spec=["input_image"], input_image=input_image)
processing_node.split("input_image")

antsApplyTransforms_workflow = pydra.Workflow(name="antsApplyTransforms_workflow1", input_spec=["input_image", "reference_image", "transforms"], input_image=processing_node.lzin.input_image)
antsApplyTransforms_workflow.inputs.reference_image = ["/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/t1_average_BRAINSABC.nii.gz",
                                                   "/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/t1_average_BRAINSABC.nii.gz"]
antsApplyTransforms_workflow.inputs.transforms      = ["/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5",
                                                   "/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5"]

antsApplyTransforms_task = Nipype1Task(ApplyTransforms())


antsApplyTransforms_task.inputs.dimension       = 3
antsApplyTransforms_task.inputs.float           = False
antsApplyTransforms_task.inputs.input_image     = antsApplyTransforms_workflow.lzin.input_image

# antsApplyTransforms_task.

antsApplyTransforms_task.inputs.interpolation   = "MultiLabel"
antsApplyTransforms_task.inputs.output_image    = "91300_2_subj_lbl.nii.gz"
antsApplyTransforms_task.inputs.reference_image = antsApplyTransforms_workflow.lzin.reference_image
antsApplyTransforms_task.inputs.transforms = antsApplyTransforms_workflow.lzin.transforms
# antsApplyTransforms_task.inputs.reference_image = ["/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/t1_average_BRAINSABC.nii.gz",
#                                                    "/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/t1_average_BRAINSABC.nii.gz"]
# antsApplyTransforms_task.inputs.transforms      = ["/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5",
#                                                    "/mnt/c/2020_Grad_School/Research/output_dir/sub-273625_ses-47445_run-002_T1w/AtlasToSubjectPreBABC_SyNComposite.h5"]
antsApplyTransforms_task.split(("reference_image", "transforms"))

antsApplyTransforms_workflow.add(get_self(name="get_self", x=antsApplyTransforms_task.inputs.reference_image))

antsApplyTransforms_workflow.add(antsApplyTransforms_task)
antsApplyTransforms_workflow.set_output([("output_image", antsApplyTransforms_task.lzout.output_image)])

processing_node.add(antsApplyTransforms_workflow)
processing_node.set_output([("out", antsApplyTransforms_workflow.lzout.output_image)])

with pydra.Submitter(plugin="cf") as sub:
    sub(processing_node)
result = processing_node.result()
print(result)

# # print(antsApplyTransforms_task.cmdline)
# res = antsApplyTransforms_task()
# print(res)
