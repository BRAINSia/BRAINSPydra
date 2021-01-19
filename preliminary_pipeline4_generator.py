import configparser
import json

config = configparser.ConfigParser()
config.optionxform = str # Read configuration parameters and maintain capitalization
config.read('config.ini')

WORKFLOW_NAME = "preliminary_workflow4"

def get_inputs():
    return config['INPUT']['input']

def get_workflow_components():
    workflow_components_contents = ""
    # print(json.loads(config['TASKS']['workflow_components']))
    for workflow_component in json.loads(config['TASKS']['workflow_components']):
        filename_components = ""
        task_components = ""
        task_components += f'{workflow_component}_task = {config[workflow_component]["SEM_class"]}(name="{workflow_component}", executable={config[workflow_component]["executable"]}).get_task()\n'
        config[workflow_component].pop('executable')
        config[workflow_component].pop('SEM_class')
        for parameter in config[workflow_component]:

            value = config[workflow_component][parameter]
            try: # Try to read the value as a json-style entry - it should be a dictionary
                value_dict = json.loads(value)
                if value_dict['function'] == 'out':
                    if value_dict['section'] == "INPUT":
                        task_input = f'{workflow_component}_task.inputs.{parameter} = {WORKFLOW_NAME}.lzin.{value_dict["variable"]}'
                    else:
                        task_input = f'{workflow_component}_task.inputs.{parameter} = {WORKFLOW_NAME}.{value_dict["section"]}.lzout.{value_dict["variable"]}'
                    task_components += f"{task_input}\n"
                elif value_dict['function'] == 'append':
                    if value_dict['section'] == "INPUT":
                        filename_task = f'{WORKFLOW_NAME}.add(append_filename(name="{parameter}", filename={WORKFLOW_NAME}.lzin.{value_dict["variable"]}, appended_str="{value_dict["appended"]}", extension="{value_dict["extension"]}"))'
                    else:
                        filename_task = f'{WORKFLOW_NAME}.add(append_filename(name="{parameter}", filename={WORKFLOW_NAME}.{value_dict["section"]}.lzout.{value_dict["variable"]}, appended_str="{value_dict["appended"]}", extension="{value_dict["extension"]}"))'
                    task_input = f'{workflow_component}_task.inputs.{parameter} = {WORKFLOW_NAME}.{parameter}.lzout.out'
                    filename_components += f'{filename_task}\n'
                    task_components += f'{task_input}\n'
            except: # If the entry is not json-style, read it as a normal configuration parameter
                # print(value, int(value))
                value = f'{workflow_component}_task.inputs.{parameter} = {value}'
                task_components += f'{value}\n'
        task_components += f'{WORKFLOW_NAME}.add({workflow_component}_task)'

        workflow_components_contents += f'{filename_components}\n'
        workflow_components_contents += f'{task_components}\n'
        workflow_components_contents += '\n'

    return workflow_components_contents

pipeline_contents = f"""
import pydra
import nest_asyncio
from pathlib import Path
from shutil import copyfile
from registration import BRAINSResample
from segmentation.specialized import BRAINSConstellationDetector

@pydra.mark.task
def get_subject(sub):
    return sub

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}}{{append_str}}{{extension}}"
    return new_filename

@pydra.mark.task
def copy_from_cache(cache_path, output_dir):
    copyfile(cache_path, Path(output_dir) / Path(cache_path).name)
    out_path = Path(output_dir) / Path(cache_path).name
    copyfile(cache_path, out_path)
    return out_path

nest_asyncio.apply()

# Get the list of two files of the pattern subject*.txt images in this directory
input = {get_inputs()}

# Put the files into the pydra cache and split them into iterable objects. Then pass these iterables into the processing node (preliminary_workflow3)
source_node = pydra.Workflow(name="source_node", input_spec=["input"])
{WORKFLOW_NAME} = pydra.Workflow(name="{WORKFLOW_NAME}", input_spec=["input"], input=source_node.lzin.input)
source_node.add({WORKFLOW_NAME})
source_node.split("input") # Create an iterable for each t1 input file (for preliminary pipeline 3, the input files are .txt)
source_node.inputs.input = input

{get_workflow_components()}

# Set the outputs of the processing node and the source node so they are output to the sink node
{WORKFLOW_NAME}.set_output([("outputLandmarksInInputSpace",             {WORKFLOW_NAME}.BCD.lzout.outputLandmarksInInputSpace),
                                  ("outputResampledVolume",             {WORKFLOW_NAME}.BCD.lzout.outputResampledVolume),
                                  ("outputTransform",                   {WORKFLOW_NAME}.BCD.lzout.outputTransform),
                                  ("outputLandmarksInACPCAlignedSpace", {WORKFLOW_NAME}.BCD.lzout.outputLandmarksInACPCAlignedSpace),
                                  ("writeBranded2DImage",               {WORKFLOW_NAME}.BCD.lzout.writeBranded2DImage),
                                  ("outputVolume",                      {WORKFLOW_NAME}.RESAMPLE.lzout.outputVolume)])
source_node.set_output([("outputLandmarksInInputSpace",       source_node.{WORKFLOW_NAME}.lzout.outputLandmarksInInputSpace),
                        ("outputResampledVolume",             source_node.{WORKFLOW_NAME}.lzout.outputResampledVolume),
                        ("outputTransform",                   source_node.{WORKFLOW_NAME}.lzout.outputTransform),
                        ("outputLandmarksInACPCAlignedSpace", source_node.{WORKFLOW_NAME}.lzout.outputLandmarksInACPCAlignedSpace),
                        ("writeBranded2DImage",               source_node.{WORKFLOW_NAME}.lzout.writeBranded2DImage),
                        ("outputVolume",                      source_node.{WORKFLOW_NAME}.lzout.outputVolume)])

# The sink converts the cached files to output_dir, a location on the local machine
sink_node = pydra.Workflow(name="sink_node", input_spec=["processed_files"], cache_dir="{config['OUTPUT']['cache_dir']}")
sink_node.add(source_node)
sink_node.add(copy_from_cache(name="outputLandmarksInInputSpace",       output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.outputLandmarksInInputSpace))
sink_node.add(copy_from_cache(name="outputResampledVolume",             output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.outputResampledVolume))
sink_node.add(copy_from_cache(name="outputTransform",                   output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.outputTransform))
sink_node.add(copy_from_cache(name="outputLandmarksInACPCAlignedSpace", output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.outputLandmarksInACPCAlignedSpace))
sink_node.add(copy_from_cache(name="writeBranded2DImage",               output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.writeBranded2DImage))
sink_node.add(copy_from_cache(name="outputVolume",                      output_dir="{config['OUTPUT']['output_dir']}", cache_path=sink_node.source_node.lzout.outputVolume))
sink_node.set_output([("output", sink_node.outputVolume.lzout.out)])

# Run the entire workflow
with pydra.Submitter(plugin="cf") as sub:
    sub(sink_node)
result=sink_node.result()
print(result)
"""
with open("preliminary_pipeline4.py", "w") as f:
    f.write(pipeline_contents)