import pydra
from pathlib import Path
import nest_asyncio
import time

import attr
from nipype.interfaces.base import (
    Directory,
    File,
)
from pydra import ShellCommandTask
from pydra.engine.specs import SpecInfo, ShellSpec

from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector

#from resample_cmd import fill_resample_task
from bcd_cmd import fill_bcd_task

if __name__ == '__main__':
    subject1_json = {"in": {"t1": ["/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-052823_ses-43817_run-002_T1w.nii.gz",
                                   "/localscratch/Users/cjohnson30/BCD_Practice/t1w_examples2/sub-066260_ses-21713_run-002_T1w.nii.gz"], 
                            "ref": "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz", 
                            "transform": "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5"},
                     "out":{"output_dir": "/localscratch/Users/cjohnson30/output_dir"}}

    resample = BRAINSResample()
    bcd = BRAINSConstellationDetector()
    wf = pydra.Workflow(name="wf", input_spec=["t1", "ref", "transform"], output_spec=["outputDir"])
    wf.inputs.t1 = subject1_json['in']['t1']
    wf.inputs.ref = subject1_json['in']['ref']
    wf.inputs.transform = subject1_json['in']['transform']
    
    

    wf.add(resample.task)
    wf.add(bcd.task)
   
    wf.set_output(
        [
            ("outVol", wf.BRAINSResample.lzout.outputVolume),
            ("outputLandmarksInACPCAlignedSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInACPCAlignedSpace),
            ("outputLandmarksInInputSpace", wf.BRAINSConstellationDetector.lzout.outputLandmarksInInputSpace),
            ("outputResampledVolume", wf.BRAINSConstellationDetector.lzout.outputResampledVolume),
            ("outputTransform", wf.BRAINSConstellationDetector.lzout.outputTransform),
        ]
    )
    
    with pydra.Submitter(plugin="cf") as sub:
        sub(wf)
    result = wf.result()
    print(result)
