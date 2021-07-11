from pydra.engine.helpers import load_task, save
from pathlib import Path

cache_dir = Path("/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/SGEWorker_scripts/")

errored_task_pklz = cache_dir.glob("*/*_task.pklz")


# errored_task_pklz = ["/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_4a260fa732384d64f0c77e8976794cdbbc21d4ec1e944513566cb2a5d840f45f/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_eb3812f50db89406e5aa712040619d14c8d4c100e27acddb01bd0a66f7889e4e/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_a4d58c1af72697063cefa369990eef9b3fa6562c21dbf9be24267b81977181a8/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_eccfc7f23119813b10a2d3a0684007893f0a7e0e95845f75ed35ec7df6b94829/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_ea14f6e193b55520c83dcb9e8d33f6767868be407c3d3ab0a9630743930a1185/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_50e177e989c2caf1c46d2694abf37a27cec88c654eedb08981e762731ef22109/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_bb546dfbd7303d72e794de02cb1f20f1b22c9f068e23394d9e6e7ecfefca4aa3/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_a15ddf0486ec8ae827a0d3ec7f55e8402b98e89893d8bcf6a96d2dec8b2f899f/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_451a910a91c43dcdc6e541388e0bcb5faab0799446cb8137fa767ee2688fe5c1/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_2127106a9536ed5e91b2109f3c4cb6afcb458c49ffa810a775ab34df3755f82c/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_924b24127fe43cbb019884562a5c8a6d17684af6f1f32bc588fabb07b74b559b/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_564937785322bbb24ebb37d6294b4b4fe0f40e562176ee3e7b86cc88360fd95c/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_5a37f7aa450593d16813f4bce229f81e3e51451d7eafbbe566f93a8b8a02905b/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_db6c8a782f0476213aa0447d23bfb9082b392ad0bddc5f7e3be4a45f97d59a31/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_4773bf8497ce7d39aa9792dd40aad04dcf05af60834459fada21835c8a08d8dc/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_13455d32fd668debbf1de7727bedd726b23f5692293cafb63728b58dcca6adc4/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_4e6c75fe884fbb566c5f52560848a2911d0cb9121bc12f122e006407d1b297d5/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_ded6a1d36f96d45b59b497551fa572888f4ce0fe3a5e6456b8ab167b45f73d06/_task.pklz",
# "/Shared/sinapse/pydra-cjohnson/cache_dir_10_4threads/Workflow_b838d3598d686a119bc3c5b242c8088a308774b0324b837b5bc491aabacba3f6/_task.pklz"]

for pickle in errored_task_pklz:
    # print(pickle)
    task_pkl = pickle.parent / "_task.pklz"
    # print(task_pkl)
    task = load_task(task_pkl)
    print(task._errored)
#     task._result = None
#     print(task._result)
#     # Path(pickle).unlink()
#     # print(f"Saving to {Path(pickle).parent}")
#     # save(Path(pickle).parent, result=None, task=task)