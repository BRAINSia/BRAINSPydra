import pydra
import nest_asyncio
import attr
from pathlib import Path
from shutil import copyfile

nest_asyncio.apply()


@pydra.mark.task
def get_subject(sub):
    return sub


@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path


# Get the list of two files of the pattern subject*.txt images in this directory
t1_list = []
p = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files")
for t1 in p.glob("subject*.txt"):
    t1_list.append(t1)

# Put the files into the pydra cache and split them into iterable objects
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

# Specify the input for the shell command tasks
my_input_spec = pydra.specs.SpecInfo(
    name="Input",
    fields=[
        (
            "t1",
            attr.ib(
                type=pydra.specs.File,
                metadata={
                    "position": 1,
                    "argstr": "",
                    "help_string": "text",
                    "mandatory": True,
                    "copyfile": True,
                },
            ),
        ),
    ],
    bases=(pydra.specs.ShellSpec,),
)

# Specify the output for the shell command tasks
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

# Setup the workflow to process the files
preliminary_workflow2 = pydra.Workflow(name="preliminary_workflow2", input_spec=["t1"])
preliminary_workflow2.add(source_node)
preliminary_workflow2.add(
    pydra.ShellCommandTask(
        name="BRAINSConstellationDetector2",
        executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSConstellationDetector2.sh",
        t1=preliminary_workflow2.source_node.lzout.t1,
        input_spec=my_input_spec,
        output_spec=my_output_spec,
    )
)
preliminary_workflow2.add(
    pydra.ShellCommandTask(
        name="BRAINSResample2",
        executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSResample2.sh",
        t1=preliminary_workflow2.BRAINSConstellationDetector2.lzout.out,
        input_spec=my_input_spec,
        output_spec=my_output_spec,
    )
)
preliminary_workflow2.set_output(
    [("processed_files", preliminary_workflow2.BRAINSConstellationDetector2.lzout.out)]
)

# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"])
sink_node.add(preliminary_workflow2)
sink_node.add(
    copy_from_cache(
        name="copy_from_cache",
        output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir",
    ).split(
        "cache_path", cache_path=sink_node.preliminary_workflow2.lzout.processed_files
    )
)
sink_node.set_output([("output", sink_node.copy_from_cache.lzout.out)])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result = sink_node.result()
print(result)
