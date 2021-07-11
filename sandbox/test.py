from pydra.engine.helpers import load_task
from pathlib import Path
import sys

task = load_task(
    task_pkl="/Shared/sinapse/pydra-cjohnson/cache_dir_1_4123/ShellCommandTask_6c6678fb059dbe0f925ec23a863719e6a5a05c0e8da4b49959f4623f6a9a8ab7/_task.pklz",
    ind=None,
)
print(task.inputs.inputVolume)

p = Path()
