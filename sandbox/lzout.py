import pydra


@pydra.mark.task
def add2(x):
    return x + 2


# RETURN source_node.add2.lzout.out
@pydra.mark.task
def add0(node):
    # node is NOTHING in here
    return node.add2.lzout.out


source_node = pydra.Workflow(name="wf", input_spec=["x"])
source_node.inputs.x = [1, 6, 9]
source_node.split("x")

source_node.add(add2(name="add2", x=source_node.lzin.x))
source_node.add(add0(name="add0", node=source_node))

source_node.set_output([("add0", source_node.add0.lzout.out)])

with pydra.Submitter(plugin="cf") as sub:
    sub(source_node)
results = source_node.result()
print(results)
