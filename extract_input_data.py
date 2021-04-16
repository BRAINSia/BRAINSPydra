import argparse
from pathlib import Path
import pprint
import csv
from BIDSFilename import *

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
    "--session_count",
    type=int,
    help="The number of sessions from which to have data extracted",
    default=-1,
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


sessions_regex = "*sub-*/ses-*/"

input_dict = {"sessions_with_T2": [], "sessions_without_T2": []}

p = Path(args.bids_path)
sessions = p.glob(sessions_regex)
counter = 0
for session in sessions:
    session_id = f"{session.parent.name}_{session.name}"
    if counter > args.session_count and args.session_count is not -1:
        break
    counter += 1

    inputVolumes = []
    inputVolumeTypes = []
    inputLandmarksEMSP = None

    nifty_files = session.glob("*.nii.gz")
    for inputVolume in nifty_files:
        bids_filename_obj = BIDSFilename(inputVolume)
        inputVolumeType = None

        # Put the best T1 image at the beginning of the inputVolumes list and set its landmark file
        if bids_filename_obj.attribute_dict["run"] == best_t1_by_session[session_id]:
            if "T1w.nii.gz" in inputVolume.name:
                inputLandmarksEMSP = str(
                    inputVolume.with_suffix("").with_suffix(".fcsv")
                )
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

    if "T2" in inputVolumeTypes:
        input_dict["sessions_with_T2"].append(
            {
                "session": session_id,
                "inputVolumes": inputVolumes,
                "inputVolumeTypes": inputVolumeTypes,
                "inputLandmarksEMSP": inputLandmarksEMSP,
            }
        )
    else:
        input_dict["sessions_without_T2"].append(
            {
                "session": session_id,
                "inputVolumes": inputVolumes,
                "inputVolumeTypes": inputVolumeTypes,
                "inputLandmarksEMSP": inputLandmarksEMSP,
            }
        )


pp.pprint(input_dict)