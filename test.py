import attr
from nipype.interfaces.base import (
    Directory,
    File,
    InputMultiPath,
    OutputMultiPath,
    traits,
)
from pydra import ShellCommandTask
from pydra.engine.specs import SpecInfo, ShellSpec, MultiInputFile, MultiOutputFile, MultiInputObj, ShellOutSpec
import pydra

file = '/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh'

cmd = "bash"
new_files_id = ["file1.txt", "file2.txt", "file3.txt"]

my_input_spec = SpecInfo(
    name="Input",
    fields=[
        (
            "script",
            attr.ib(
                type=File,
                metadata={
                    "help_string": "script file",
                    "mandatory": True,
                    "position": 1,
                    "argstr": "",
                },
            ),
        ),
        (
            "files_id",
            attr.ib(
                type=MultiInputFile,
                metadata={
                    "argstr": "--output",
                    "sep": ",",
                    "help_string": "list of name indices",
                    "mandatory": True,
                },
            ),
        ),
    ],
    bases=(ShellSpec,),
)

my_output_spec = SpecInfo(
    name="Output",
    fields=[
        (
            "new_files",
            attr.ib(
                type=MultiOutputFile,
                metadata={
                    "output_file_template": "{files_id}",
                    "help_string": "output file",
                },
            ),
        )
    ],
    bases=(ShellOutSpec,),
)

shelly = ShellCommandTask(
    name="shelly",
    executable=cmd,
    input_spec=my_input_spec,
    output_spec=my_output_spec,
    script=file,
    files_id=new_files_id,
)


print(shelly.cmdline)
# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(shelly)
result = shelly.result()
print(result)