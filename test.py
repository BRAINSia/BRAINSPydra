import pydra
import nest_asyncio

nest_asyncio.apply()

@pydra.mark.task
def get_self(x):
    return x

@pydra.mark.task
def add2(x):
    return x + 2

@pydra.mark.task
def multiply(x, y):
    return x * y

@pydra.mark.task
def get_num(x):
    return x

@pydra.mark.task
def extract_from_outall_dict(d: dict):
    print(d)
    print(list(d.values()))
    print(d)
    return list(d.values())

source_node = pydra.Workflow(name="wf_st_3", input_spec=["x"])
source_node.add(add2(name="add2", x=source_node.lzin.x))
source_node.inputs.x = [2, 4]
source_node.split("x")

processing_node = pydra.Workflow(name="processing_node", input_spec=["x"], x=source_node.add2.lzout.out)
processing_node.add(add2(name="add2", x=processing_node.lzin.x))
processing_node.set_output([("out", processing_node.add2.lzout.out)])

sink_node = pydra.Workflow(name="sink_node", input_spec=["x"], x=processing_node.lzout.out)
sink_node.add(add2(name="add2", x=sink_node.lzin.x))
sink_node.set_output([("out", sink_node.add2.lzout.out)])

source_node.add(processing_node)
source_node.add(sink_node)

source_node.set_output([("out", source_node.sink_node.lzout.out)])

with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
results = source_node.result()
print(results)







# source_node = pydra.Workflow(name="source_node", input_spec=["x"])
# wf = pydra.Workflow(name="wf", input_spec=["x"], x=source_node.lzin.x)
# source_node.add(wf)
# source_node.split("x")
# source_node.inputs.x = [1, 2]
#
# wf.add(add2(name="add2_1", x=wf.lzin.x))
# wf.add(add2(name="add2_2", x=wf.add2_1.lzout.out))
# wf.add(add2(name="add2_3", x=wf.add2_2.lzout.out))
# wf.add(multiply(name="mult2", x=wf.add2_3.lzout.out, y=wf.add2_2.lzout.out))
# wf.set_output([("add2_1", wf.add2_1.lzout.out),
#                ("add2_2", wf.add2_2.lzout.out),
#                ("add2_3", wf.add2_3.lzout.out),
#                ("mult2", wf.mult2.lzout.out)])
#
# source_node.set_output([("add2_1", source_node.wf.lzout.add2_1),
#                         ("add2_2", source_node.wf.lzout.add2_2),
#                         ("add2_3", source_node.wf.lzout.add2_3),
#                         ("mult2",  source_node.wf.lzout.mult2)])
#
# sink_node = pydra.Workflow(name="sink_node", input_spec=["out_all"])
# sink_node.add(source_node)
# sink_node.inputs.out_all = sink_node.source_node.lzout.all_
# sink_node.add(get_self(name="get_self", x=sink_node.lzin.out_all))
# sink_node.set_output([("all", sink_node.get_self.lzout.out)])
#
#
# with pydra.Submitter(plugin="cf") as sub:
#     sub(source_node)
# results = source_node.result()
# print(results)
# with pydra.Submitter(plugin="cf") as sub:
#     sub(sink_node)
# results = sink_node.result()
# print(results)