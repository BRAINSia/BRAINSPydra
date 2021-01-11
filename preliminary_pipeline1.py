import pydra
import nest_asyncio
nest_asyncio.apply()

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append(t1):
    return t1 + "_append"

t1_list = ["subject1.nii.gz", "subject2.nii.gz"]

source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

preliminary_workflow1 = pydra.Workflow(name="wf", input_spec=["t1"])
preliminary_workflow1.add(source_node)
preliminary_workflow1.add(append(name="append1", t1=preliminary_workflow1.source_node.lzout.t1))
preliminary_workflow1.add(append(name="append2", t1=preliminary_workflow1.append1.lzout.out))
preliminary_workflow1.add(append(name="append3", t1=preliminary_workflow1.append2.lzout.out))
preliminary_workflow1.set_output([("output_in_cache1", preliminary_workflow1.append1.lzout.out),
                                  ("output_in_cache2", preliminary_workflow1.append2.lzout.out),
                                  ("output_in_cache3", preliminary_workflow1.append3.lzout.out)])

sink_node = pydra.Workflow(name="sink_node", input_spec=["output_in_cache1"])
sink_node.add(preliminary_workflow1)
sink_node.add(append(name="append").split("t1", t1=sink_node.wf.lzout.output_in_cache3))
sink_node.set_output([("output_not_in_cache", sink_node.append.lzout.out)])

with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)

