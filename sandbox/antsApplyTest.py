from pydra.tasks.nipype1.utils import Nipype1Task
from nipype.interfaces.ants import ApplyTransforms
import json

with open("../config_experimental.json") as f:
    experiment_configuration = json.load(f)

# antsApplyTransforms_task = ApplyTransforms()
antsApplyTransforms_task = Nipype1Task(ApplyTransforms())

# Set the variables that set output file names
antsApplyTransforms_task.inputs.default_value = 0
antsApplyTransforms_task.inputs.dimension = 3
antsApplyTransforms_task.inputs.input_image = "/Shared/johnsonhj/ReferenceData/20160523_HDAdultAtlas/35888/wholeBrain_label.nii.gz"
antsApplyTransforms_task.inputs.interpolation = "MultiLabel"
antsApplyTransforms_task.inputs.output_image = "35888fswm_2_subj_lbl.nii.gz"
antsApplyTransforms_task.inputs.reference_image = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/TissueClassify/BABC/t1_average_BRAINSABC.nii.gz"
antsApplyTransforms_task.inputs.transforms = ["/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/JointFusion/SyN_AtlasToSubjectANTsPreJointFusion_13512/13512_ToSubjectPreJointFusion_SyNComposite.h5"]
antsApplyTransforms_task.inputs.invert_transform_flags = [False]

print(antsApplyTransforms_task.cmdline)

