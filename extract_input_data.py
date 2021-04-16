import argparse
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Get MRI data to be processed by BRAINSPydraAutoWorkup"
)
parser.add_argument(
    "bids_path", type=str, help="The path to the top level of the bids dataset"
)
parser.add_argument(
    "--session_count",
    type=int,
    help="The number of sessions from which to have data extracted",
    default=-1,
    required=False,
)


args = parser.parse_args()
print(args.bids_path)
sessions_regex = "*sub-*/ses-*/"


p = Path(args.bids_path)
all_jsons = p.glob(sessions_regex)
counter = 0
for json_path in all_jsons:
    if counter > args.session_count and args.session_count is not -1:
        break
    print(json_path)
    counter += 1
