import pydra
import time


@pydra.mark.task
def add_one(x):
    return x + 1


@pydra.mark.task
def pydra_sleep(x):
    time.sleep(x)


wf = pydra.Workflow(
    name="wf",
    input_spec=["x"],
    x=1,
    cache_dir="/Shared/sinapse/pydra-cjohnson/sge_cache_dir",
)
# wf.add(pydra_sleep(name="sleep", x=5))
wf.add(add_one(name="add_one", x=wf.lzin.x))

wf.set_output([("out", wf.add_one.lzout.out)])
wf

with pydra.Submitter("sge") as sub:
    sub(wf)

print(wf.result())

# 231356