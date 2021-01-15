import pydra
import nest_asyncio
import attr
from pathlib import Path
from shutil import copyfile
from registration import BRAINSResample


nest_asyncio.apply()

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    # Path(new_filename).touch()
    return new_filename

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
preliminary_workflow3 = pydra.Workflow(name="preliminary_workflow3", input_spec=["t1"], t1=source_node.lzin.t1_list)
source_node.add(preliminary_workflow3)
source_node.split("t1_list")
source_node.inputs.t1_list = t1_list

resampledOutputVolumeTask = append_filename(name="resampledOutputVolume", filename=preliminary_workflow3.lzin.t1, append_str="_resampled", extension=".txt", directory="")
preliminary_workflow3.add(resampledOutputVolumeTask)

resample_task = BRAINSResample("BRAINSResample3").get_task()
resample_task.inputs.inputVolume = preliminary_workflow3.lzin.t1
resample_task.inputs.interpolationMode = "Linear"
resample_task.inputs.pixelType =         "binary"
resample_task.inputs.referenceVolume =   "/localscratch/Users/cjohnson30/resample_refs/t1_average_BRAINSABC.nii.gz"
resample_task.inputs.warpTransform =     "/localscratch/Users/cjohnson30/resample_refs/atlas_to_subject.h5" # outputTransform
resample_task.inputs.outputVolume =      preliminary_workflow3.resampledOutputVolume.lzout.out
preliminary_workflow3.add(resample_task)

preliminary_workflow3.set_output([("t1", preliminary_workflow3.BRAINSResample3.lzout.outputVolume)])
source_node.set_output([("t1", source_node.preliminary_workflow3.lzout.t1)])



# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"])
sink_node.add(source_node)
sink_node.add(copy_from_cache(name="copy_from_cache", output_dir="/mnt/c/2020_Grad_School/Research/BRAINSPydra/output_dir", cache_path=sink_node.source_node.lzout.t1))#.split("cache_path", cache_path=sink_node.source_node.lzout.t1))
sink_node.set_output([("output", sink_node.copy_from_cache.lzout.out)])


# # Run the entire workflow
# with pydra.Submitter(plugin="cf") as sub:
#     sub(source_node)
# result=source_node.result()
# print(result)

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)