import pydra
import time
from pathlib import Path
import uuid
import random


@pydra.mark.task
def add_one(x):
    time.sleep(20)
    return x + 1

@pydra.mark.task
def add_two(x):
    return x + 2

@pydra.mark.task
def add_three(x):
    return x + 3

wf = pydra.Workflow(
    name="wf",
    input_spec=["x"],
    x=list(range(0, 10)),
    cache_dir=Path("/Shared/sinapse/pydra-cjohnson/sge_cache_dir") / Path(str(uuid.uuid1())),
).split(("x"))
add_one_task = add_one(name="add_one", x=wf.lzin.x)
add_one_task.qsub_args = "-l h_rt=10 -q HJ -pe smp 10"
# add_one_task.qsub_args = "-l mem_256G -pe smp 10"
wf.add(add_one_task)
add_three_task = add_one(name="add_three", x=wf.lzin.x)
add_three_task.qsub_args = "-l mem_256G -q HJ -pe smp 10"
wf.add(add_three_task)
wf.add(add_two(name="add_two", x=wf.add_one.lzout.out))

wf.set_output([("out", wf.add_two.lzout.out),
               ("out2", wf.add_three.lzout.out)])

t0 = time.time()
with pydra.Submitter(
    "sge",
    write_output_files=False,
    qsub_args="-q UI",
    default_qsub_args="-pe smp 8",
    indirect_submit_host="argon-login-2",
    max_job_array_length=50,
    poll_delay=2,
    default_threads_per_task=2,
    # max_threads=50,
    poll_for_result_file=True,
    collect_jobs_delay=10,
    polls_before_checking_evicted=3,) as sub:
# with pydra.Submitter("cf") as sub:
    sub(wf, rerun=True)
print(f"Total time: {time.time() - t0}")
print(wf.result())

# 231356