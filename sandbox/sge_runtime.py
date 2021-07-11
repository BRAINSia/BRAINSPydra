import pydra
from pathlib import Path
import time
import uuid


@pydra.mark.task
def fun_addvar(a, b):
    return a + b


@pydra.mark.task
def fun_addtwo(a):
    import time

    time.sleep(1)
    if a == 3:
        time.sleep(50)
    return a + 2


def gen_basic_wf(name="basic-wf"):
    """
    Generates `Workflow` of two tasks

    Task Input
    ----------
    x : int (5)

    Task Output
    -----------
    out : int (9)
    """
    wf = pydra.Workflow(name=name, input_spec=["x"])
    wf.inputs.x = 3
    add_two = fun_addtwo(name="task1", a=wf.lzin.x, b=0)
    add_two.qsub_args = "-q HJ -l h_rt=10 -pe smp 8"
    wf.add(add_two)
    wf.add(fun_addvar(name="task2", a=wf.task1.lzout.out, b=2))
    # wf.add(fun_addvar(name="task2", a=wf.lzin.x, b=2))
    wf.set_output([("out", wf.task2.lzout.out)])
    return wf


t0 = time.time()
wf = gen_basic_wf()
wf.plugin = "cf"
tmpdir = Path("/Shared/sinapse/pydra-cjohnson/tmp") / Path(str(uuid.uuid4()))
wf.cache_dir = tmpdir
# submit workflow and every task as slurm job
with pydra.Submitter(
        "sge",
        write_output_files=False,
        qsub_args="-q all.q",
        default_qsub_args="-q all.q -pe smp 8",
        indirect_submit_host="argon-login-2",
        max_job_array_length=15,
        poll_delay=10,
        default_threads_per_task=8,
        # max_threads=500,
        poll_for_result_file=True,
        collect_jobs_delay=30,
        polls_before_checking_evicted=12,
) as sub:
    sub(wf)

res = wf.result()
print(f"Total time: {time.time() - t0}")
