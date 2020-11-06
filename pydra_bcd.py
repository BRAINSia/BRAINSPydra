import pydra
import os


def run_bcd():
    os.system("bash run_bcd.sh")


@pydra.mark.task
def run_bcd_pydra():
    os.system("bash run_bcd.sh")


cmd = ["bash", "/localscratch/Users/cjohnson30/BRAINSPydra/run_bcd.sh"]

shelly = pydra.ShellCommandTask(name="shelly", executable=cmd)
with pydra.Submitter(plugin="cf") as sub:
    sub(shelly)
print(shelly.result())

# run_bcd()
# bcd_task = run_bcd_pydra()
# bcd_task.result()
