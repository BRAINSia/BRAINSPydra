import pydra
import attr
import time

cmd = "touch"
filename = "newfile_1.txt"


@pydra.mark.task
def append_filename(filename):
    # time.sleep(5)
    return filename + "_appended"

@pydra.mark.task
def wait():
    time.sleep(10)

wf = pydra.Workflow(name="wf", input_spec=["filename"], filename=filename, cache_dir="/Shared/sinapse/pydra-cjohnson/test")

my_output_spec = pydra.specs.SpecInfo(
    name="Output",
    fields=[
        (
            "out",
            attr.ib(
                type=pydra.specs.File,
                metadata={
                    "output_file_template": "{args}",
                    "help_string": "output file",
                },
            ),
        )
    ],
    bases=(pydra.specs.ShellOutSpec,),
)

wf.add(append_filename(name="append_filename", filename=wf.lzin.filename))

shell_wf = pydra.Workflow(name="shell_wf", input_spec=["filename"], filename=wf.append_filename.lzout.out)
shell_wf.add(wait(name="wait"))
shelly = pydra.ShellCommandTask(
    name="shelly",
    executable=cmd,
    args=shell_wf.lzin.filename,
    output_spec=my_output_spec,
)
shelly
shell_wf.add(shelly)
shell_wf.set_output([("out", shell_wf.shelly.lzout.out)])
wf.add(shell_wf)
wf.set_output([("out", wf.shell_wf.lzout.out)])

# print("cmndline = ", shelly.cmdline)

with pydra.Submitter(plugin="cf") as sub:
    sub(wf)

# with pydra.Submitter(
#     "sge",
#     write_output_files=False,
#     qsub_args="-q HJ",
#     indirect_submit_host="argon-login-2",
#     max_job_array_length=50,
#     poll_delay=2,
#     default_threads_per_task=8,
#     max_threads=500,
#     poll_for_result_file=True,
#     collect_jobs_delay=2,
#     polls_before_checking_evicted=12,
# ) as sub:
#     sub(wf)

print(wf.result())
