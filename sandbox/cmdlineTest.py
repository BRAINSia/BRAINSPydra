import pydra
import attr

cmd = "echo"
filename = "newfile_1.txt"


@pydra.mark.task
def append_filename(filename):
    return filename + "_appended"


wf = pydra.Workflow(name="wf", input_spec=["filename"], filename=filename)

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
shelly = pydra.ShellCommandTask(
    name="shelly",
    executable=cmd,
    args=wf.append_filename.lzout.out,
    output_spec=my_output_spec,
)
wf.add(shelly)
wf.set_output([("out", wf.shelly.lzout.out)])

print("cmndline = ", shelly.cmdline)

with pydra.Submitter(plugin="cf") as sub:
    sub(wf)
wf.result()
