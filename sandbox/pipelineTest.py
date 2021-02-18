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
from shutil import copyfile
from pathlib import Path
import string
@pydra.mark.task
def get_input_field(input_dict: dict, field):
    # print(input_dict[field])
    return input_dict[field]

@pydra.mark.task
def make_cache_dir(input_sub):
    cache_dir = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/cache_dir") / Path(input_sub).with_suffix("").with_suffix("").name
    print(cache_dir)
    return cache_dir

@pydra.mark.task
def make_output_filename(filename="", before_str="", append_str="", extension="", directory="", unused=""):
    if filename is None:
        return None
    else:
        # If an extension is not specified and the filename has an extension, use the filename's extension
        if extension == "":
            extension = "".join(Path(filename).suffixes)
        new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
        return new_filename

file = '/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh'

cmd = "bash"

source_node = pydra.Workflow(name="source_node", input_spec=["input_data"])
# source_node.inputs.input_data = ["sub1", "sub2"]
source_node.inputs.input_data =[
    {"t1": "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/subject1.txt",
     "inputMovingLandmarkFilename": "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/LandmarkInitialize/BCD/BCD_Original.fcsv"
     },
    {
        "t1": "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/subject2.txt",
        "inputMovingLandmarkFilename": "/Shared/sinapse/CACHE/20200915_PREDICTHD_base_CACHE/singleSession_sub-697343_ses-50028/LandmarkInitialize/BCD/BCD_Original.fcsv"
    }
]
source_node.split("input_data")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

my_input_spec = SpecInfo(
    name="Input",
    fields=[
        (
            "input",
            attr.ib(
                type=MultiInputFile,
                metadata={
                    "argstr": "--input",
                    "sep": ",",
                    "help_string": "list of name indices",
                },
            ),
        ),
        (
            "default",
            attr.ib(
                type=MultiInputFile,
                metadata={
                    "argstr": "--default",
                    "sep": ",",
                    "help_string": "list of name indices",
                },
            ),
        ),
        (
            "output",
            attr.ib(
                type=File,
                metadata={
                    "argstr": "--output",
                    "sep": ",",
                    "help_string": "list of name indices",
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
                type=pydra.specs.File,
                metadata={
                    "output_file_template": "{output}",
                    "help_string": "output file"
                },
            ),
        )
    ],
    bases=(ShellOutSpec,),
)

shelly_workflow = pydra.Workflow(name="shelly_workflow", input_spec=["input_data"], input_data=source_node.lzin.input_data)


shelly = ShellCommandTask(
    name="shelly",
    executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh",
    input_spec=my_input_spec,
    output_spec=my_output_spec,
)
shelly_workflow.add(get_input_field(name="get_t1", input_dict=shelly_workflow.lzin.input_data, field="t1"))
shelly_workflow.add(make_output_filename(name="output", filename=shelly_workflow.get_t1.lzout.out, append_str="_corrected", extension=".nii.gz"))
shelly_workflow.add(shelly)
# new_output = ["file1.txt", "file2.txt"]
# new_output = "file1.txt"

# shelly.inputs.input = shelly_workflow.lzin.input_data
shelly.inputs.input = shelly_workflow.get_t1.lzout.out
shelly.inputs.output = shelly_workflow.output.lzout.out

shelly.inputs.default = "%s_corrected_%d.nii.gz"
shelly_workflow.set_output([("out", shelly_workflow.shelly.lzout.new_files)])


@pydra.mark.task
def get_self(x):
    return x


@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    to_return = None
    # print(list(processed_dict.values()))
    # if type(list(processed_dict.values())[0]) is list:
    #     print("its a list")
    #     to_return = list(processed_dict.values())
    # else:
    #     print("not a list")
    #     to_return = [list(processed_dict.values())]
    to_return = list(processed_dict.values())
    # print(to_return)
    return to_return

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    pass
    # print("in copy_from_cache")
    # print(cache_path)
    # if cache_path is None:
    #     return "" # Don't return a cache_path if it is None
    # else:
    #     if type(cache_path) is list:
    #         output_list = []
    #         for path in cache_path:
    #             copyfile(path, Path(output_dir) / Path(path).name)
    #             out_path = Path(output_dir) / Path(path).name
    #             copyfile(path, out_path)
    #             output_list.append(out_path)
    #         return output_list
    #     else:
    #         copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    #         out_path = Path(output_dir) / Path(cache_path).name
    #         copyfile(cache_path, out_path)
    #         return cache_path
    # return "test"

sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files'], processed_files=shelly_workflow.lzout.all_)
sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
# sink_node.add(copy_from_cache(name="copy_from_cache", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.get_processed_outputs.lzout.out).split("cache_path"))
# sink_node.set_output([("output_files", sink_node.copy_from_cache.lzout.out)])
sink_node.set_output([("output_files", sink_node.get_processed_outputs.lzout.out)])


source_node.add(shelly_workflow)
# source_node.add(sink_node)
# source_node.set_output([("output_files", source_node.sink_node.lzout.output_files)])
source_node.set_output([("output_files", source_node.shelly_workflow.lzout.out)])



# print(shelly.cmdline)
# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
# result = source_node.result(return_inputs=True)
result = source_node.result()
print(result)