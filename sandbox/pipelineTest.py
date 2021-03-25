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
    # print(cache_dir)
    return cache_dir

@pydra.mark.task
def make_output_filename(filename="", before_str="", append_str="", extension="", directory="", unused=""):
    # print("Making output filename")
    if filename is None:
        print("filename is none")
        return None
    else:
        if type(filename) is list:
            new_filename = []
            for f in filename:
                if extension == "":
                    extension = "".join(Path(f).suffixes)
                new_filename.append(f"{Path(Path(directory) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}")
                # Path(new_filename[-1]).touch()
        else:
            # If an extension is not specified and the filename has an extension, use the filename's extension
            if extension == "":
                extension = "".join(Path(filename).suffixes)
            new_filename = f"{Path(Path(directory) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
            # Path(new_filename).touch()
        # print(f"filename: {filename}")
        # print(f"new_filename: {new_filename}")
        return new_filename

@pydra.mark.task
def get_self(x):
    return x


@pydra.mark.task
def get_None():
    x = 4

    return x


@pydra.mark.task
def get_processed_outputs(processed_dict: dict):
    return list(processed_dict.values())

@pydra.mark.task
def copy_from_cache(cache_path, output_dir, input_data):
    input_filename = Path(input_data.get('t1')).with_suffix('').with_suffix('').name
    file_output_dir = Path(output_dir) / Path(input_filename)
    file_output_dir.mkdir(parents=True, exist_ok=True)
    if cache_path is None:
        print(f"cache_path: {cache_path}")
        return "" # Don't return a cache_path if it is None
    else:
        if type(cache_path) is list:
            output_list = []
            for path in cache_path:
                out_path = Path(file_output_dir) / Path(path).name
                print(f"Copying from {path} to {out_path}")
                copyfile(path, out_path)
                output_list.append(out_path)
            return output_list
        else:
            out_path = Path(file_output_dir) / Path(cache_path).name
            print(f"Copying from {cache_path} to {out_path}")
            copyfile(cache_path, out_path)
            return cache_path

file = '/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh'

cmd = "bash"

input_data = [
    {
      "session": "sub-052823_ses-43817",
      "t1": "/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-052823_ses-43817_run-002_T1w.nii.gz",
      "inputLandmarksEMSP": "/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-052823_ses-43817_run-002_T1w.fcsv"
    },
    {
      "session": "sub-273625_ses-47445",
      "t1": "/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-273625_ses-47445_run-002_T1w.nii.gz",
      "inputLandmarksEMSP": "/localscratch/Users/cjohnson30/wf_ref/t1w_examples2/sub-273625_ses-47445_run-002_T1w.fcsv"
    }
  ]

source_node = pydra.Workflow(name="source_node", input_spec=["input_data"])
# source_node.inputs.input_data = ["sub1", "sub2"]
source_node.inputs.input_data = input_data
source_node.split("input_data")  # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)

my_input_spec = SpecInfo(
    name="Input",
    fields=[
        (
            "createFiles",
            attr.ib(
                type=MultiOutputFile,
                metadata={
                    "argstr": "--createFiles ",
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
                    "argstr": "--output ",
                    "help_string": "list of name indices",
                },
            ),
        ),
        (
            "contents",
            attr.ib(
                type=list,
                metadata={
                    "argstr": "--contents ",
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
            "createFiles",
            attr.ib(
                type=pydra.specs.MultiOutputFile,
                metadata={
                    "output_file_template": "{createFiles}",
                    "help_string": "output file"
                },
            ),
        ),
        (
            "output",
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

processing_node = pydra.Workflow(name="processing_node", input_spec=["input_data"], input_data=source_node.lzin.input_data)
shelly_workflow = pydra.Workflow(name="shelly_workflow", input_spec=["input_data"], input_data=processing_node.lzin.input_data)


shelly_createFiles = ShellCommandTask(
    name="shelly_createFiles",
    executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh",
    input_spec=my_input_spec,
    output_spec=my_output_spec,
)
shelly_createFiles.inputs.createFiles = ["test1", "test2"]

shelly_writeOutput = ShellCommandTask(
    name="shelly_writeOutput",
    executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/dummy_shell_scripts/test.sh",
    input_spec=my_input_spec,
    output_spec=my_output_spec,
)

shelly_workflow.add(get_input_field(name="get_t1", input_dict=shelly_workflow.lzin.input_data, field="t1"))
source_node.add(get_input_field(name="get_session", input_dict=source_node.lzin.input_data, field="session"))
shelly_workflow.add(make_output_filename(name="output", filename=shelly_workflow.get_t1.lzout.out, append_str="_corrected", extension=".txt"))

shelly_workflow.add(shelly_createFiles)
shelly_writeOutput.inputs.contents = shelly_workflow.shelly_createFiles.lzout.createFiles
shelly_writeOutput.inputs.output = shelly_workflow.output.lzout.out
shelly_workflow.add(shelly_writeOutput)

shelly_workflow.set_output([("out", shelly_workflow.shelly_writeOutput.lzout.output),
                            ])
processing_node.add(shelly_workflow)
processing_node.set_output([("out", processing_node.shelly_workflow.lzout.all_),
                            # ("session", processing_node.get_session.lzout.out)])
                            ])
source_node.add(processing_node)

@pydra.mark.task
def get_output_dir(node):
    print(f"{node.name} output_dir: {node.output_dir}")
    p = Path(node.output_dir)
    # for cache_filepath in p.glob("**/*"):
    # return node.output_dir

@pydra.mark.task
def copy(source_output_dir):
    # print(f"input_data: {input_data}")
    print(f"output_dir in sink: {source_output_dir}")
    p = Path(source_output_dir)
    # for cache_filepath in p.glob("**/[!_]*"):
    for cache_filepath in p.glob("**/*"):
        print("Here")
        print(cache_filepath)
        # # if Path(cache_path).is_file():
        # #     out_path = Path(output_dir) / Path(cache_path).name
        # #     print(f"Copying from {cache_path} to {out_path}")
        # #     copyfile(cache_path, out_path)
        #
        # input_filename = Path(input_data.get('t1')).with_suffix('').with_suffix('').name
        # # file_output_dir = Path(output_dir) / Path(input_filename)
        # # file_output_dir.mkdir(parents=True, exist_ok=True)
        #
        # output_directory = Path(experiment_configuration["output_dir"]) / Path(input_filename)
        # output_directory.mkdir(parents=True, exist_ok=True)
        # output_filepath = Path(output_directory) / Path(cache_filepath).name
        # print(f"Copying {cache_filepath} to {output_filepath}")
        # print(type(cache_filepath))
        # print(type(output_filepath))
        # cache_filepath.link_to(output_filepath)
    return source_output_dir

# sink_node = pydra.Workflow(name="sink_node", input_spec=['processed_files', 'input_data'], processed_files=shelly_workflow.lzout.all_, input_data=source_node.lzin.input_data)
# sink_node.add(get_processed_outputs(name="get_processed_outputs", processed_dict=sink_node.lzin.processed_files))
# # sink_node.add(copy_from_cache(name="copy_from_cache", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.get_processed_outputs.lzout.out, input_data=sink_node.lzin.input_data).split("cache_path"))
# sink_node.add(get_output_dir(name="get_output_dir", node=processing_node))
# # sink_node.add(copy(name="copy", source_output_dir=sink_node.get_output_dir.lzout.out))
# sink_node.set_output([
#     ("out_dir", sink_node.get_processed_outputs.lzout.out),
#     # ("out_dir_in_copy", sink_node.copy.lzout.out)
#     # ("output_files", sink_node.copy_from_cache.lzout.out),
#       # ("output_dir", sink_node.get_output_dir.lzout.out)])
#     ])



source_node.add(shelly_workflow)
# source_node.add(sink_node)
source_node.set_output([
    ("output_files", source_node.processing_node.lzout.all_),
    ("session", source_node.get_session.lzout.out),
])

output_dir = "/mnt/c/2020_Grad_School/Research/output_dir"

environment_configuration = {}
environment_configuration["hard_links"] = False
experiment_configuration = {
  "output_dir": "/mnt/c/2020_Grad_School/Research/output_dir_full_run_multithreaded",
  "cache_dir": "/mnt/c/2020_Grad_School/Research/cache_dir_full_run_multithreaded",
  "graph_dir": "/mnt/c/2020_Grad_School/Research/graph_dir"}

@pydra.mark.task
def copy(source_output_dir, session):
    print(f"session: {session}")
    print(f"output_dir in sink: {source_output_dir}")
    p = Path(source_output_dir)
    output_files = []
    output_dir = Path(experiment_configuration.get("output_dir")) / Path(session)
    output_dir.mkdir(exist_ok=True, parents=True)
    for cache_filepath in p.glob("**/[!_]*"):
        print(cache_filepath)
        output_files.append(cache_filepath)
        output_filepath = output_dir / cache_filepath.name
        print(f"Copying {cache_filepath} to {output_filepath}")
        if environment_configuration.get('hard_links'):
            cache_filepath.link_to(output_filepath)
        else:
            copyfile(cache_filepath, output_filepath)
    return output_files

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
result = source_node.result()
print(result)
# print(result.get_output_field("session"))

sessions = [sess_data['session'] for sess_data in input_data]
sink_node2 = pydra.Workflow(name="sink_node", input_spec=["output_directory", "session"], output_directory=source_node.output_dir, session=sessions)
sink_node2.add(copy(name="copy4", source_output_dir=sink_node2.lzin.output_directory, session=sink_node2.lzin.session).split(("source_output_dir", "session")))
sink_node2.set_output([("files_out", sink_node2.copy4.lzout.out)])

with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node2)