from dask.distributed import Client
import pydra
from dask_jobqueue import SGECluster

if __name__ == "__main__":

    cluster = SGECluster(
        queue="HJ",
        cores=12,
        # walltime="1500000",
        processes=10,  # we request 10 processes per worker
        memory="20GB",  # for memory requests, this must be specified
        interface="ib0",
        # resource_spec="m_mem_free=20G",  # for memory requests, this also needs to be specified
    )
    cluster.scale(jobs=2)
    client = Client(
        cluster,
        asynchronous=True,
        # interface="ib0",
        # scheduler_file="/Shared/sinapse/pydra-cjohnson/scheduler.json",
    )
    # @pydra.mark.task
    # def add_one(x):
    #     return x + 1

    # # wf = pydra.Workflow(name="wf", input_spec=["x"], x=1)
    # # wf.add(add_one(name="add_one", x=wf.lzin.x))
    # # wf.set_output([("out", wf.add_one.lzout.out)])

    # print("Hello World!")
    # client = Client(
    #     # "172.29.6.181:8786"
    #     # scheduler_file="/Shared/sinapse/pydra-cjohnson/scheduler.json", processses=False
    # )  # start local workers as processes
    # # or
    # # client = Client(processes=False)  # start local workers as threads

    def inc(x):
        return x + 1

    def add(x, y):
        return x + y

    # a = client.submit(inc, 10)  # calls inc(10) in background thread or process
    # b = client.submit(inc, 20)  # calls inc(20) in background thread or process

    # c = client.submit(add, a, b)  # calls add on the results of a and b

    futures = client.map(inc, range(2))

    # print(c.result())

    results = client.gather(futures)  # this can be faster

    print(results)
