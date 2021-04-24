import pydra
import time
from pathlib import Path
import uuid


@pydra.mark.task
def add_one(x):
    return x + 1


@pydra.mark.task
def pydra_sleep(seconds):
    time.sleep(seconds)
    return seconds


wf = pydra.Workflow(
    name="wf",
    input_spec=["x"],
    x=list(range(1, 60)),
    cache_dir=Path("/Shared/sinapse/pydra-cjohnson/sge_cache_dir") / str(uuid.uuid1()),
).split(("x"))
wf.add(pydra_sleep(name="sleep", seconds=2))
wf.add(add_one(name="add_one", x=wf.lzin.x))

wf.set_output([("out", wf.sleep.lzout.out)])
wf

t0 = time.time()
with pydra.Submitter(
    "sge",
    qsub_args="-o /Shared/sinapse/pydra-cjohnson/log -e /Shared/sinapse/pydra-cjohnson/error -q HJ -pe smp 1",
) as sub:
    # with pydra.Submitter("cf") as sub:
    sub(wf)
print(f"Total time: {time.time() - t0}")
print(wf.result())

# 231356