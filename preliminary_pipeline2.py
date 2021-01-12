import pydra
import nest_asyncio
import attr
from pathlib import Path
from shutil import copyfile

nest_asyncio.apply()

@pydra.mark.task
def get_subject(sub):
    # print(sub)
    return sub

@pydra.mark.task
def read_file(file):
    print(f"Reading {file}")
    with open(file, "r") as f:
        print(f.read())
    return file

@pydra.mark.task
def append(t1, appended):
    return t1 + appended

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    print(f"filename: {filename}")
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    print(f"cache_path: {cache_path}")
    print(f"output_dir: {output_dir}")
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path

# Get the list of two files by the patter subject*.txt images in this directory
t1_list = []
p = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files")
for t1 in p.glob("subject*.txt"):
    t1_list.append(t1)
# print(t1_list)

# Put the files into the pydra cache and split them into iterable objects
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

my_input_spec = pydra.specs.SpecInfo(
    name="Input",
    fields=[
        (
            "t1",
            attr.ib(
                type=pydra.specs.File,
                metadata={"position": 1, "argstr": "", "help_string": "text", "mandatory": True, "copyfile":True},
                ),
        ),
    ],
    bases=(pydra.specs.ShellSpec,),
)
my_output_spec = pydra.specs.SpecInfo(
    name="Output",
    fields=[
        (
            "out",
            attr.ib(
                type=pydra.specs.File,
                metadata={
                    "output_file_template": "{t1}",
                    "help_string": "output file",
                },
            ),
        )
    ],
    bases=(pydra.specs.ShellOutSpec,),
)

preliminary_workflow2 = pydra.Workflow(name="preliminary_workflow2", input_spec=["t1"])
preliminary_workflow2.add(source_node)
preliminary_workflow2.add(pydra.ShellCommandTask(name="BRAINSResample", executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSResample.sh", t1=preliminary_workflow2.source_node.lzout.t1, input_spec=my_input_spec, output_spec=my_output_spec))
preliminary_workflow2.add(pydra.ShellCommandTask(name="BRAINSConstellationDetector", executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSConstellationDetector.sh", t1=preliminary_workflow2.BRAINSResample.lzout.out, input_spec=my_input_spec, output_spec=my_output_spec))
preliminary_workflow2.set_output([("processed_files", preliminary_workflow2.BRAINSResample.lzout.out)])

sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"])
sink_node.add(preliminary_workflow2)
sink_node.add(get_subject(name="get_subject", sub=sink_node.preliminary_workflow2.lzout.processed_files))
# sink_node.split("processed_files", processed_files=sink_node.preliminary_workflow2.lzout.processed_files)
# # sink_node.inputs.processed_files = sink_node.preliminary_workflow2.lzout.processed_files
# sink_node.add(copy_from_cache(name="copy_from_cache", cache_path=sink_node.lzin.processed_files, output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir").split("cache_path"))
sink_node.set_output([("output_file", sink_node.get_subject.lzout.out)])

#
# with pydra.Submitter(plugin="cf") as sub:
#     sub(source_node)
# result=source_node.result()
# print(result)
# with pydra.Submitter(plugin="cf") as sub:
#     sub(preliminary_workflow2)
# result=preliminary_workflow2.result()
# print(result)
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)
#
