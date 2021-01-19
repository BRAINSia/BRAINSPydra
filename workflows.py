import pydra
from pathlib import Path
from segmentation.specialized import BRAINSConstellationDetector

@pydra.mark.task
def append_filename(filename="", append_str="", extension="", directory=""):
    new_filename = f"{Path(Path(directory) / Path(Path(filename).with_suffix('').with_suffix('').name))}{append_str}{extension}"
    return new_filename


def make_preliminary_workflow3(mysource_node: pydra.Workflow) -> pydra.Workflow:
    preliminary_workflow3 = pydra.Workflow(name="preliminary_workflow3", input_spec=["t1"])
    preliminary_workflow3.inputs.t1 = mysource_node.lzin.t1_list
    # Set the filenames for the output of the BRAINSConstellationDetector task
    preliminary_workflow3.add(
        append_filename(name="outputLandmarksInInputSpace", filename=preliminary_workflow3.lzin.t1,
                        append_str="_BCD_Original", extension=".fcsv"))
    preliminary_workflow3.add(
        append_filename(name="outputResampledVolume", filename=preliminary_workflow3.lzin.t1, append_str="_BCD_ACPC",
                        extension=".nii.gz"))
    preliminary_workflow3.add(append_filename(name="outputTransform", filename=preliminary_workflow3.lzin.t1,
                                              append_str="_BCD_Original2ACPC_transform", extension=".h5"))
    preliminary_workflow3.add(
        append_filename(name="outputLandmarksInACPCAlignedSpace", filename=preliminary_workflow3.lzin.t1,
                        append_str="_BCD_ACPC_Landmarks", extension=".fcsv"))
    preliminary_workflow3.add(append_filename(name="writeBranded2DImage", filename=preliminary_workflow3.lzin.t1,
                                              append_str="_BCD_Branded2DQCimage", extension=".png"))

    # Create and fill a task to run a dummy BRAINSConstellationDetector script that runs touch for all the output files
    bcd_task = BRAINSConstellationDetector(name="BRAINSConstellationDetector3",
                                           executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSConstellationDetector3.sh").get_task()
    bcd_task.inputs.inputVolume = preliminary_workflow3.lzin.t1
    bcd_task.inputs.inputTemplateModel = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/T1_50Lmks.mdl"
    bcd_task.inputs.LLSModel = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/LLSModel_50Lmks.h5"
    bcd_task.inputs.atlasLandmarkWeights = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_weights_50Lmks.wts"
    bcd_task.inputs.atlasLandmarks = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/input_files/20141004_BCD/template_landmarks_50Lmks.fcsv"
    bcd_task.inputs.houghEyeDetectorMode = 1
    bcd_task.inputs.acLowerBound = 80.000000
    bcd_task.inputs.interpolationMode = "Linear"
    bcd_task.inputs.outputLandmarksInInputSpace = preliminary_workflow3.outputLandmarksInInputSpace.lzout.out
    bcd_task.inputs.outputResampledVolume = preliminary_workflow3.outputResampledVolume.lzout.out
    bcd_task.inputs.outputTransform = preliminary_workflow3.outputTransform.lzout.out
    bcd_task.inputs.outputLandmarksInACPCAlignedSpace = preliminary_workflow3.outputLandmarksInACPCAlignedSpace.lzout.out
    bcd_task.inputs.writeBranded2DImage = preliminary_workflow3.writeBranded2DImage.lzout.out
    preliminary_workflow3.add(bcd_task)

    # Set the filename for the output of the Resample task
    resampledOutputVolume = append_filename(name="resampledOutputVolume",
                                            filename=preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume,
                                            append_str="_resampled", extension=".txt", directory="")
    preliminary_workflow3.add(resampledOutputVolume)

    # Create and fill a task to run a dummy BRAINSResample script that runs appends resample to the inputVolume
    resample_task = BRAINSResample(name="BRAINSResample3",
                                   executable="/mnt/c/2020_Grad_School/Research/BRAINSPydra/BRAINSResample3.sh").get_task()
    resample_task.inputs.inputVolume = preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume
    resample_task.inputs.interpolationMode = "Linear"
    resample_task.inputs.pixelType = "binary"
    resample_task.inputs.referenceVolume = "/mnt/c/2020_Grad_School/Research/BRAINSPydra/resample_refs/t1_average_BRAINSABC.nii.gz"
    resample_task.inputs.warpTransform = preliminary_workflow3.outputTransform.lzout.out
    resample_task.inputs.outputVolume = preliminary_workflow3.resampledOutputVolume.lzout.out
    preliminary_workflow3.add(resample_task)

    # Set the outputs of the processing node and the source node so they are output to the sink node
    preliminary_workflow3.set_output([("outputLandmarksInInputSpace",
                                       preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputLandmarksInInputSpace),
                                      ("outputResampledVolume",
                                       preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputResampledVolume),
                                      ("outputTransform",
                                       preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputTransform),
                                      ("outputLandmarksInACPCAlignedSpace",
                                       preliminary_workflow3.BRAINSConstellationDetector3.lzout.outputLandmarksInACPCAlignedSpace),
                                      ("writeBranded2DImage",
                                       preliminary_workflow3.BRAINSConstellationDetector3.lzout.writeBranded2DImage),
                                      ("outputVolume", preliminary_workflow3.BRAINSResample3.lzout.outputVolume)])

