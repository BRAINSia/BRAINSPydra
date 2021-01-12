import pydra
import nest_asyncio
nest_asyncio.apply()

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append(t1, appended):
    return t1 + appended

t1_list = ["subject1.nii.gz", "subject2.nii.gz"]

source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

preliminary_workflow1 = pydra.Workflow(name="preliminary_workflow1", input_spec=["t1"])
preliminary_workflow1.add(source_node)
preliminary_workflow1.add(append(name="BRAINSResample1", t1=preliminary_workflow1.source_node.lzout.t1, appended="_resampled"))
preliminary_workflow1.add(append(name="BRAINSConstellationDetector1", t1=preliminary_workflow1.BRAINSResample1.lzout.out, appended="_bcd"))
preliminary_workflow1.set_output([("processed", preliminary_workflow1.BRAINSConstellationDetector1.lzout.out)])

sink_node = pydra.Workflow(name="sink_node", input_spec=["output_in_cache1"])
sink_node.add(preliminary_workflow1)
sink_node.add(append(name="append", appended="_output").split("t1", t1=sink_node.preliminary_workflow1.lzout.processed))
sink_node.set_output([("output", sink_node.append.lzout.out)])

with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)

