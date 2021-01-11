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

# outer = pydra.Workflow(name="outer", input_spec=["t1_list"], t1_list=t1_list)


source_node = pydra.Workflow(name="source_node", input_spec=["t1_list"])
source_node.split("t1_list", t1_list=t1_list)
source_node.add(get_subject(name="get_subject", sub=source_node.lzin.t1_list))
source_node.set_output([("t1", source_node.get_subject.lzout.out)])

wf = pydra.Workflow(name="wf", input_spec=["t1"])
wf.add(source_node)
wf.add(append(name="append1", t1=wf.source_node.lzout.t1))
wf.add(append(name="append2", t1=wf.append1.lzout.out))
wf.add(append(name="append3", t1=wf.append2.lzout.out))
wf.set_output([("output_in_cache1", wf.append1.lzout.out),
               ("output_in_cache2", wf.append2.lzout.out),
               ("output_in_cache3", wf.append3.lzout.out)])

sink_node = pydra.Workflow(name="sink_node", input_spec=["output_in_cache1"])
sink_node.add(wf)

# sink_node.add(wf)
# sink_node.add(source_node)
# # sink_node.split("output_in_cache", output_in_cache=sink_node.wf.lzout.output_in_cache)
# sink_node.add(get_subject(name="get_subject", subj=sink_node.lzin.output_in_cache))
# sink_node.add(append(name="append", t1=sink_node.wf.lzout.output_in_cache3))
sink_node.set_output([("output_not_in_cache", sink_node.wf.lzout.output_in_cache3)])
#
#
# outer.add(source_node)
# outer.add(wf)
# outer.add(sink_node)
# outer.set_output([("t1", outer.source_node.lzout.t1)])
                  # ("output", outer.wf.lzout.output_in_cache),
                  # ("output_not_cached", outer.sink_node.lzout.output_not_in_cache)])



with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
# with pydra.Submitter(plugin="cf") as sub:
#     sub(outer)
# result=outer.result()
print(result)

