import sys
from pydra.engine.helpers import load_and_run

task_pkls = [
    (
        "/Shared/sinapse/pydra-cjohnson/tmp/31da89c9-f25b-4999-bb61-6080510e247e/SGEWorker_scripts/6b3031fa06e841b49c8bceffe0505614/_task.pklz",
        None,
        False,
    )
]
task_index = int(sys.argv[1]) - 1
load_and_run(
    task_pkl=task_pkls[task_index][0],
    ind=task_pkls[task_index][1],
    rerun=task_pkls[task_index][2],
)
