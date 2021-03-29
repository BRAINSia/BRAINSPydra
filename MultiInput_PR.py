import pydra
from pydra.engine.specs import (
    MultiInputFile,
    SpecInfo,
    ShellSpec,
)
from pydra import ShellCommandTask
import attr

print(f"{pydra.__version__}")

input_fields = [
    (
        "inputFiles",
        attr.ib(
            type=MultiInputFile,
            metadata={
                "argstr": "--inputFiles ...",
                "help_string": "The list of input image files to be segmented.",
            },
        ),
    ),
]

output_fields = [
    (
        "outputFiles",
        attr.ib(
            type=pydra.specs.MultiOutputFile,
            metadata={
                "help_string": "Corrected Output Images: should specify the same number of images as inputVolume, if only one element is given, then it is used as a file pattern where %s is replaced by the imageVolumeType, and %d by the index list location.",
                "output_file_template": "{inputFiles}",
            },
        ),
    )
]


input_spec = SpecInfo(name="Input", fields=input_fields, bases=(ShellSpec,))
output_spec = SpecInfo(
    name="Output", fields=output_fields, bases=(pydra.specs.ShellOutSpec,)
)

task = ShellCommandTask(
    name="echoMultiple",
    executable="echo",
    input_spec=input_spec,
    output_spec=output_spec,
)
wf = pydra.Workflow(name="wf", input_spec=["inputFiles"], inputFiles=["test1", "test2"])


task.inputs.inputFiles = wf.lzin.inputFiles

wf.add(task)
wf.set_output([("out", wf.echoMultiple.lzout.outputFiles)])

with pydra.Submitter(plugin="cf") as sub:
    sub(wf)
result = wf.result()
print(f"result: {result}")
