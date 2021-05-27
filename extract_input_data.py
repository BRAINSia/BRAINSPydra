import argparse
from pathlib import Path
import pprint
import csv
from BIDSFilename import *
import json

parser = argparse.ArgumentParser(
    description="Get MRI data to be processed by BRAINSPydraAutoWorkup"
)
parser.add_argument(
    "bids_path", type=str, help="The path to the top level of the bids dataset"
)
parser.add_argument(
    "best_image_table",
    type=str,
    help="Path to the tsv file containing information on the best series for each session",
)
parser.add_argument(
    "data_dictionary_dir",
    type=str,
    help="Path the the directory to store the generated input_data_dictionary__.json files",
)
parser.add_argument(
    "pipeline_script",
    type=str,
    help="Path to the python pipeline script to run BAW using pydra",
)
parser.add_argument(
    "experimental_config",
    type=str,
    help="Path to the experimental configuration json file defining settings for each of the BRAINSTools applications",
)
parser.add_argument(
    "environmental_config",
    type=str,
    help="Path to the environmental configuration json file defining overall settings for the system being used",
)
parser.add_argument(
    "--output_job_path",
    type=str,
    default="pipeline.job",
    help="Output path to the job file that will be run to execute the pipeline on all the input data dictionary files",
)
parser.add_argument(
    "--max_sessions_per_file",
    type=int,
    help="The number of sessions to be recorded per json file (-1 for all sessions in one file)",
    default=500,
    required=False,
)
parser.add_argument(
    "--session_count",
    type=int,
    help="The number of sessions from which to have data extracted",
    default=-1,
    required=False,
)
parser.add_argument(
    "--original_sessions_list_file",
    type=str,
    help="The path to the list file where each line is a session processed in the original BAW predicthd run",
    default="",
    required=False,
)
args = parser.parse_args()

pp = pprint.PrettyPrinter(depth=6)

# Read the tsv file identifying the best t1 image in each session
best_t1_by_session = {}
with open(args.best_image_table) as fd:
    rd = csv.reader(fd, delimiter="\t")
    header = next(rd)
    for row in rd:
        session_id = f"sub-{row[header.index('participant_id')]}_ses-{row[header.index('session_id')]}"
        best_t1_series = row[header.index("bestt1_series_number")].zfill(3)
        best_t1_by_session[session_id] = best_t1_series

if args.original_sessions_list_file != "":
    with open(args.original_sessions_list_file) as fd:
        sessions_to_record = fd.read().splitlines()


sessions_regex = "*sub-*/ses-*/"

sessions_dict = {"sessions_with_T2": [], "sessions_without_T2": []}

p = Path(args.bids_path)
if args.session_count == -1:
    total_sessions = len(list(p.glob(sessions_regex)))
else:
    total_sessions = args.session_count
if args.max_sessions_per_file == -1:
    args.max_sessions_per_file = total_sessions

files_created = []
saved_sessions_count = 0
sessions = p.glob(sessions_regex)
counter = 1
for session in sessions:
    print(f"{counter} / {total_sessions} Reading data from {str(session)}")
    counter += 1
    if Path(session).name in sessions_to_record:
        session_id = f"{session.parent.name}_{session.name}"
        if (
            counter > args.session_count and args.session_count != -1
        ):  # Only read args.session_count sessions unless it is -1, then read all sessions
            break
        # if args.session_count == -1:
        # else:
        # print(f"{counter} / {args.session_count} Reading data from {str(session)}")


        inputVolumes = []
        inputVolumeTypes = []
        inputLandmarksEMSP = None

        nifty_files = session.glob("*.nii.gz")
        for inputVolume in nifty_files:
            if "BAD" not in inputVolume.name:
                bids_filename_obj = BIDSFilename(inputVolume)
                inputVolumeType = None

                if session_id in best_t1_by_session:
                    # Put the best T1 image at the beginning of the inputVolumes list and set its landmark file
                    if (
                        bids_filename_obj.attribute_dict["run"]
                        == best_t1_by_session[session_id]
                    ):
                        if "T1w.nii.gz" in inputVolume.name:
                            if inputVolume.with_suffix("").with_suffix(".fcsv").exists():
                                inputLandmarksEMSP = str(
                                    inputVolume.with_suffix("").with_suffix(".fcsv")
                                )
                            else:
                                inputLandmarksEMSP = None
                            inputVolumes.insert(0, str(inputVolume))
                            inputVolumeTypes.insert(0, "T1")

                    # If the current inputVolume is not the best for the session,
                    # add its information to the end of the input_data lists
                    else:
                        if "T1w.nii.gz" in inputVolume.name:
                            inputVolumeType = "T1"

                        elif "T2w.nii.gz" in inputVolume.name:
                            inputVolumeType = "T2"
                        elif "PD.nii.gz" in inputVolume.name:
                            inputVolumeType = "PD"
                        elif "FL.nii.gz" in inputVolume.name:
                            inputVolumeType = "FL"

                        if inputVolumeType is not None:
                            inputVolumes.append(str(inputVolume))
                            inputVolumeTypes.append(inputVolumeType)
                else:
                    print(f"Skipping {session_id}")

        if "T1" in inputVolumeTypes:
            saved_sessions_count += 1
            if "T2" in inputVolumeTypes:
                sessions_dict["sessions_with_T2"].append(
                    {
                        "session": session_id,
                        "inputVolumes": inputVolumes,
                        "inputVolumeTypes": inputVolumeTypes,
                        "inputLandmarksEMSP": None,
                    }
                )
            else:
                sessions_dict["sessions_without_T2"].append(
                    {
                        "session": session_id,
                        "inputVolumes": inputVolumes,
                        "inputVolumeTypes": inputVolumeTypes,
                        "inputLandmarksEMSP": None,
                    }
                )
            if (
                len(sessions_dict["sessions_without_T2"])
                + len(sessions_dict["sessions_with_T2"])
                == args.max_sessions_per_file
            ):
                output_file_name = Path(args.data_dictionary_dir) / Path(
                    f"input_data_dictionary_{saved_sessions_count+1-args.max_sessions_per_file}_{saved_sessions_count}.json"
                )
                with open(output_file_name, "w") as out_file:
                    json.dump(sessions_dict, out_file, indent=4)
                print(
                    f"Wrote data from {args.max_sessions_per_file} sessions to {output_file_name}"
                )
                sessions_dict = {"sessions_with_T2": [], "sessions_without_T2": []}
                files_created.append(output_file_name)

output_file_name = Path(args.data_dictionary_dir) / Path(
    f"input_data_dictionary_{saved_sessions_count+1-(saved_sessions_count%args.max_sessions_per_file)}_{saved_sessions_count}.json"
)
if (
    len(sessions_dict["sessions_with_T2"]) > 0
    or len(sessions_dict["sessions_without_T2"]) > 0
):
    with open(output_file_name, "w") as out_file:
        json.dump(sessions_dict, out_file, indent=4)
    files_created.append(output_file_name)
    print(
        f"Wrote data from {saved_sessions_count % args.max_sessions_per_file} sessions to {output_file_name}"
    )

job_string = """#!/bin/sh
case $SGE_TASK_ID in"""

for index, input_data_dictionary_file in enumerate(files_created):
    job_string += f"\n\t{index+1}) python {args.pipeline_script} {args.experimental_config} {args.environmental_config} {input_data_dictionary_file};;"
job_string += "\nesac"

with open(args.output_job_path, "w") as out_file:
    out_file.write(job_string)
print(f"Wrote job to {args.output_job_path}")
