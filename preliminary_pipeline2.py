import pydra
import nest_asyncio
import attr
from pathlib import Path
nest_asyncio.apply()

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append(t1, appended):
    return t1 + appended

# Get the list of two files by the patter subject*.txt images in this directory
t1_list = []
p = Path("/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files")
for t1 in p.glob("subject*.txt"):
    t1_list.append(t1)
print(t1_list)

# Put the files into the pydra cache and split them into iterable objects
source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

# my_input_spec = pydra.specs.SpecInfo(
#     name="Input",
#     fields=[
#         (
#             "t1",
#             attr.ib(
#                 type=pydra.specs.File,
#                 metadata={"position": 1, "argstr": "", "help_string": "text", "mandatory": True},
#                 ),
#         )
#     ],
#     bases=(pydra.specs.ShellSpec,),
# )
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
args = ["newfile_1.txt", "newfile_2.txt"]
preliminary_workflow2 = pydra.Workflow(name="preliminary_workflow2", input_spec=["t1"], t1=source_node.lzout.t1)
preliminary_workflow2.add(source_node)
preliminary_workflow2.add(pydra.ShellCommandTask(name="BRAINSResample", executable="echo", args=args, output_spec=my_output_spec).split("args"))
# preliminary_workflow2.add(append(name="BRAINSResample", t1=preliminary_workflow2.source_node.lzout.t1, appended="_resampled"))
# preliminary_workflow2.add(append(name="BRAINSConstellationDetector", t1=preliminary_workflow2.BRAINSResample.lzout.out, appended="_bcd"))
preliminary_workflow2.set_output([("processed", preliminary_workflow2.BRAINSResample.lzout.out)])
#
# sink_node = pydra.Workflow(name="sink_node", input_spec=["output_in_cache1"])
# sink_node.add(preliminary_workflow2)
# sink_node.add(append(name="append", appended="_output").split("t1", t1=sink_node.preliminary_workflow2.lzout.processed))
# sink_node.set_output([("output", sink_node.append.lzout.out)])
#
# with pydra.Submitter(plugin="cf") as sub:
#     sub(source_node)
# result=source_node.result()
with pydra.Submitter(plugin="cf") as sub:
    sub(preliminary_workflow2)
result=preliminary_workflow2.result()
# with pydra.Submitter(plugin="cf") as sub:
#     sub(sink_node)
# result=sink_node.result()
print(result)
#
