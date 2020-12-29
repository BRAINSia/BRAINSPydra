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

from resample_cmd import fill_resample_task
from bcd_cmd import fill_bcd_task

if __name__ == '__main__':
    task_resample = fill_resample_task()
    task_bcd = fill_bcd_task()
    
    wf = pydra.Workflow(name="wf", input_spec=["cmd1", "cmd2"])
    
    wf.inputs.cmd1 = "BRAINSResample"
    wf.inputs.cmd2 = "BRAINSConstellationDetector"
    
    wf.add(task_resample)
    task_bcd.inputVolume = wf.BRAINSResample.lzout.outputVolume
    wf.add(task_bcd)
    
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
