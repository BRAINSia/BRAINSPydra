# BRAINSPydra

### Generating Pipeline Jobs
#### Example
```

python3.8 extract_input_data.py \
/Shared/sinapse/CHASE_ALEX_TEMPCOPY/PREDICTHD_BIDS_DEFACE \
/Shared/sinapse/CHASE_ALEX_TEMPCOPY/PREDICTHD_BIDS_DEFACE/phenotype \
/bids_best_image_table.tsv \
/Shared/sinapse/pydra-cjohnson/BRAINSPydra/input_data_dictionaries \
/Shared/sinapse/pydra-cjohnson/BRAINSPydra/preliminary_pipeline6.py \
/Shared/sinapse/pydra-cjohnson/BRAINSPydra/config_experimental_argon.json \
/Shared/sinapse/pydra-cjohnson/BRAINSPydra/config_environment_argon.json \
--output_job_path pipeline_10.job \
--max_sessions_per_file 150 \
--original_sessions_list_file \
/Shared/sinapse/pydra-cjohnson/BRAINSPydra/orig_sessions.list \
--session_count 10

```

### Running the Pipeline

### Parameters
```
usage: preliminary_pipeline6.py [-h] config_experimental config_environment input_data_dictionary

Move echo numbers in fmap BIDS data to JSON sidecars

positional arguments:
  config_experimental   Path to the json file for configuring task parameters
  config_environment    Path to the json file for setting environment config parameters
  input_data_dictionary
                        Path to the json file for input data

optional arguments:
  -h, --help            show this help message and exit
```

#### Example
```

qsub -o /Shared/sinapse/pydra-cjohnson/log_10 \
-e /Shared/sinapse/pydra-cjohnson/error_10 \
-M charles-e-johnson@uiowa.edu \
-pe smp 1 -q HJ -m be \
-t 1-1 pipeline_10.job

```
