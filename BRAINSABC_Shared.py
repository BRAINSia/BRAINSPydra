import pydra
from sem_tasks.segmentation.specialized import BRAINSABC
import json
from pathlib import Path

with open(
    # "/mnt/c/2020_Grad_School/Research/BRAINSPydra/config_experimental_20200915.json"
    # "/home/cjohnson30/BRAINSPydra/config_experimental_20200915.json"
    # "/localscratch/Users/cjohnson30/BRAINSPydra/config_experimental_20200915.json"
    "./config_experimental_dendrite.json"
) as f:
    experiment_configuration = json.load(f)


@pydra.mark.task
def get_t1_average(outputs):
    return outputs[0]


@pydra.mark.task
def get_posteriors(outputs):
    return outputs[1:]


@pydra.mark.task
def make_filename(
    filename="", before_str="", append_str="", extension="", directory="", parent_dir=""
):
    if filename is None:
        return None
    else:
        # if the input filename is a list, set the filename for each element in the list
        if type(filename) is list:
            new_filename = []
            for f in filename:
                # If an extension is not specified and the filename has an extension, use the filename's extension(s)
                if extension == "":
                    extension = "".join(Path(f).suffixes)
                new_filename.append(
                    f"{Path(Path(directory) / Path(parent_dir) / Path(before_str + Path(f).with_suffix('').with_suffix('').name))}{append_str}{extension}"
                )
        else:
            # If an extension is not specified and the filename has an extension, use the filename's extension(s)
            if extension == "":
                extension = "".join(Path(filename).suffixes)
            new_filename = f"{Path(Path(directory) / Path(parent_dir) / Path(before_str+Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
        return new_filename


workflow_name = "abc_workflow1"
configkey = "BRAINSABC1"
print(f"Making task {workflow_name}")


inputVolumes = "/Shared/sinapse/pydra-cjohnson/output_dir_from_argon/sub-052823_ses-43817/Cropped_BCD_ACPC_Aligned.nii.gz"

inputT1 = "/Shared/sinapse/chdi_bids/DELETEME/PREDICTHD_BIDS/derivatives/physicalACPC/sub-052823/ses-43817/sub-052823_ses-43817_run-002_rec-physicalACPC_T1w.nii.gz"

restoreState = "/Shared/sinapse/pydra-cjohnson/output_dir_from_argon/sub-052823_ses-43817/SavedInternalSyNState.h5"


# Define the workflow and its lazy inputs
abc_workflow = pydra.Workflow(
    name=workflow_name,
    input_spec=["inputVolumes", "inputT1", "restoreState"],
    inputVolumes=inputVolumes,
    inputT1=inputT1,
    restoreState=restoreState,
)
# abc_workflow.split(("inputVolumes", "restoreState", "inputT1"))
abc_workflow.add(
    make_filename(
        name="outputVolumes",
        filename=abc_workflow.lzin.inputT1,
        append_str="_corrected",
        extension=".nii.gz",
    )
)


@pydra.mark.task
def print_input(x):
    print(x)


abc_workflow.add(
    print_input(name="printinputVolumes", x=abc_workflow.lzin.inputVolumes)
)

abc_task = BRAINSABC(
    name="BRAINSABC", executable=experiment_configuration[configkey]["executable"]
).get_task()
abc_task.inputs.inputVolumes = abc_workflow.lzin.inputVolumes
abc_task.inputs.restoreState = abc_workflow.lzin.restoreState
abc_task.inputs.outputVolumes = abc_workflow.outputVolumes.lzout.out

abc_task.inputs.atlasDefinition = experiment_configuration[configkey].get(
    "atlasDefinition"
)
abc_task.inputs.atlasToSubjectTransform = experiment_configuration[configkey].get(
    "atlasToSubjectTransform"
)
abc_task.inputs.atlasToSubjectTransformType = experiment_configuration[configkey].get(
    "atlasToSubjectTransformType"
)
abc_task.inputs.debuglevel = experiment_configuration[configkey].get("debuglevel")
abc_task.inputs.filterIteration = experiment_configuration[configkey].get(
    "filterIteration"
)
abc_task.inputs.filterMethod = experiment_configuration[configkey].get("filterMethod")
abc_task.inputs.inputVolumeTypes = experiment_configuration[configkey].get(
    "inputVolumeTypes"
)
abc_task.inputs.interpolationMode = experiment_configuration[configkey].get(
    "interpolationMode"
)
abc_task.inputs.maxBiasDegree = experiment_configuration[configkey].get("maxBiasDegree")
abc_task.inputs.maxIterations = experiment_configuration[configkey].get("maxIterations")
abc_task.inputs.posteriorTemplate = experiment_configuration[configkey].get(
    "POSTERIOR_%s.nii.gz"
)
abc_task.inputs.purePlugsThreshold = experiment_configuration[configkey].get(
    "purePlugsThreshold"
)
abc_task.inputs.saveState = experiment_configuration[configkey].get("saveState")
abc_task.inputs.useKNN = experiment_configuration[configkey].get("useKNN")
abc_task.inputs.outputFormat = experiment_configuration[configkey].get("outputFormat")
abc_task.inputs.outputDir = experiment_configuration[configkey].get("outputDir")
abc_task.inputs.outputDirtyLabels = experiment_configuration[configkey].get(
    "outputDirtyLabels"
)
abc_task.inputs.outputLabels = experiment_configuration[configkey].get("outputLabels")
abc_task.inputs.implicitOutputs = [
    experiment_configuration[configkey].get("t1_average")
] + experiment_configuration[configkey].get("posteriors")

abc_workflow.add(abc_task)
abc_workflow.add(
    get_t1_average(name="get_t1_average", outputs=abc_task.lzout.implicitOutputs)
)
abc_workflow.add(
    get_posteriors(name="get_posteriors", outputs=abc_task.lzout.implicitOutputs)
)
abc_workflow.set_output(
    [
        ("outputVolumes", abc_workflow.BRAINSABC.lzout.outputVolumes),
        ("outputDirtyLabels", abc_workflow.BRAINSABC.lzout.outputDirtyLabels),
        ("outputLabels", abc_workflow.BRAINSABC.lzout.outputLabels),
        (
            "atlasToSubjectTransform",
            abc_workflow.BRAINSABC.lzout.atlasToSubjectTransform,
        ),
        ("t1_average", abc_workflow.get_t1_average.lzout.out),
        ("posteriors", abc_workflow.get_posteriors.lzout.out),
    ]
)

with pydra.Submitter(plugin="cf") as sub:
    sub(abc_workflow)
result = abc_workflow.result()
print(f"result: {result}")
