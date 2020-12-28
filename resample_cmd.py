from pathlib import Path
from registration import BRAINSResample


def resample_cmd(input_vol_path="/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/",
                 input_vol_glob="*",
                 sess_output_dir="/localscratch/Users/cjohnson30/output_dir",
                 interpolationMode="Linear",
                 pixelType = "binary",
                 referenceVolume="/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz",
                 warpTransform="/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5",
                 splitTuple=("inputVolume", "outputVolume")):
    resample = BRAINSResample()
    task_resample = resample.task
    input_spec_resample = resample.input_spec
    output_spec_resample = resample.output_spec
    
    # Create a list of all the files to be resampled
    p = Path(input_vol_path)
    all_t1 = p.glob(input_vol_glob)
    filename_objs = list(all_t1)
    input_vols = []
    for t1 in filename_objs:
        input_vols.append(str(t1))
    
    # Define the inputs in the input_spec of the pydra task
    SESS_OUTPUT_DIR = sess_output_dir
#    SESS_OUTPUT_DIR = "/localscratch/Users/cjohnson30/output_dir"
    task_resample.inputs.inputVolume = input_vols
    task_resample.inputs.interpolationMode = interpolationMode 
    task_resample.inputs.outputVolume = [
        f"{SESS_OUTPUT_DIR}/{Path(x).with_suffix('').with_suffix('').name}_resampled.nii.gz"
        for x in input_vols
    ]
    task_resample.inputs.pixelType = pixelType
    #task.inputs.referenceVolume = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/TissueClassify/BABC/t1_average_BRAINSABC.nii.gz"
    #task.inputs.warpTransform = "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/TissueClassify/BABC/atlas_to_subject.h5"
    
    # Original locations for referenceVolume and warpTransform:
    #/Shared/sinapse/chdi_bids/PREDICTHD_BIDS_DEFACE/derivatives/20200915_PREDICTHD_base_Results/sub-343219/ses-23544/TissueClassify/t1_average_BRAINSABC.nii.gz
    #/Shared/sinapse/chdi_bids/PREDICTHD_BIDS_DEFACE/derivatives/20200915_PREDICTHD_base_Results/sub-343219/ses-23544/TissueClassify/atlas_to_subject.h5
    task_resample.inputs.referenceVolume = referenceVolume
    task_resample.inputs.warpTransform = warpTransform
    
    # Use a scalar splitter to create the outputVolume from a given inputVolume
    task_resample.split(splitTuple)
    return task_resample
