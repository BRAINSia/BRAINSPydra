import pydra
import random
import uuid
from pathlib import Path


# @pydra.mark.task
# def pass_odds(x):
#     if x % 2 == 0:
#         print(f"x%2 = {x % 2} (error)")
#         raise Exception("0 error")
#     else:
#         print(f"x%2 = {x % 2}")
#         return x

# task = pass_odds(name="pass_odds", x=[1, 2, 3, 4, 5]).split("x")
# # task = pass_odds(name="pass_odds", x=[1, 2, 3, 4, 5], cache_dir=Path("./test") / Path(str(uuid.uuid4()))).split("x")


# try:
#     task()
#     print(task.result())
# except:
#     pass

# print("\n\n\n\n\nIN BETWEEN \n\n\n\n\n\n")

# try:
#     task()
#     print(f"task.result(): {task.result()}")
# except:
#     pass

@pydra.mark.task
def error_3(x):
    if x == 3:
        print(f"{x} (error)")
        raise Exception("x was 3")
    else:
        print(f"{x}")
        return x

wf = pydra.Workflow(
    name="wf",
    input_spec=["x"],
    x=[1, 2, 3],
    cache_dir=Path("./test") / Path(str(uuid.uuid4()))
).split("x")
wf.add(error_3(name="error_3", x=wf.lzin.x))
wf.set_output([("out", wf.error_3.lzout.out)])


with pydra.Submitter("cf") as sub:
    sub(wf)
print(f"\n\n\n\n\n\n\n\n\n\nwf.result(): {wf.result()}\n\n\n\n\n\n\n\n\n\n")

# @pydra.mark.task
# def pass_odds(x):
#     if x % 2 == 0:
#         print(f"{x}%2 = {x % 2} (error)")
#         raise Exception("even error")
#     else:
#         print(f"{x}%2 = {x % 2}")
#         return x
#
# wf = pydra.Workflow(
#     name="wf",
#     input_spec=["x"],
#     x=[1, 2, 3, 4, 5, 6, 7, 8, 9],
#     # cache_dir= Path("./test") / Path(str(uuid.uuid4()))
#
# ).split("x")
# wf.add(pass_odds(name="pass_odds", x=wf.lzin.x))
# wf.set_output([("out", wf.pass_odds.lzout.out)])
#
# print("First run")
# # try:
# wf()
# print(wf.result())

# except:
#     pass

# print("Second run")
# try:
#     wf()
#     print(wf.result())
# except:
#     pass
#
# print("\n\n\n\n\nIN BETWEEN \n\n\n\n\n\n")
#
# try:
#     wf()
#     print(wf.result())
# except:
#     pass
#
# print("\n\n\n\n\nIN BETWEEN \n\n\n\n\n\n")
#
# try:
#     wf()
#     print(wf.result())
# except:
#     pass


# print("\n\n\n\n\nIN BETWEEN \n\n\n\n\n\n")
#
# try:
#     wf()
#     # with pydra.Submitter("cf") as sub:
#     #     sub(wf)
#     print(wf.result())
# except:
#     pass

# import pydra
# import random
#
# @pydra.mark.task
# def add_one(x):
#     return x+1
#
# @pydra.mark.task
# def pass_odds(x):
#     # x = random.randint(0,x)
#     if x % 2 == 0:
#         # print(f"x%2 = {x % 2}")
#         print(f"{x}%2 = {x % 2} (error)")
#         raise Exception("even error")
#     else:
#         print(f"{x}%2 = {x % 2}")
#         return x
#
# wf = pydra.Workflow(
#     name="wf",
#     input_spec=["x"],
#     x=[1, 2, 3, 4, 5],
#     cache_dir="/Shared/sinapse/pydra-cjohnson/rerun_errored"
# ).split("x")
#
# processing_node = pydra.Workflow(
#     name="processing_node",
#     input_spec=["x"],
#     x = wf.lzin.x
# )
# inside_node = pydra.Workflow(
#     name="inside_node",
#     input_spec=["x"],
#     x = processing_node.lzin.x
# )
# # inside_node.add(add_one(name="add_one", x=inside_node.lzin.x))
#
# # inside_node.add(pass_odds(name="pass_odds", x=inside_node.add_one.lzout.out))
# inside_node.add(pass_odds(name="pass_odds", x=inside_node.lzin.x))
#
# inside_node.set_output([("out", inside_node.pass_odds.lzout.out)])
#
# processing_node.add(inside_node)
# processing_node.set_output([("out", processing_node.inside_node.lzout.out)])
# wf.add(processing_node)
# wf.set_output([("out", wf.processing_node.lzout.out)])
#
# try:
#     with pydra.Submitter("cf") as sub:
#         sub(wf)
#     print(wf.result())
# except:
#     pass
#
# print("\n\n\n\n\nIN BETWEEN \n\n\n\n\n\n")
#
# try:
#     with pydra.Submitter("cf") as sub:
#         sub(wf)
#     print(wf.result())
# except:
#     pass
# with pydra.Submitter("cf") as sub:
#     sub(wf)
# print(wf.result())
#
# with pydra.Submitter("cf") as sub:
#     sub(wf)
# print(wf.result())