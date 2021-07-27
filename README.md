# BRAINSPydra

### Using BRAINSPydra

Using BRAINSPydra to run AutoWorkup using the Pydra dataflow engine requires the following steps:
1) Define config_environment to set parameters for individual steps in AutoWorkup and config_experimental to set parameters for the computing environment (examples: config_environment_argon.json and config_experimental_argon.json)
2) Generate an array job of AutoWorkup pipelines to avoid the Pydra overhead of submitting many sessions through the same pipeline script (session_count recommended to be 10). Further instruction is given in `Generating Pipeline Jobs`.
3) Submit the array job of pipelines to the Sun Grid Engine. Further instruction is given in `Running the Pipeline`.

### Generating Pipeline Jobs

#### Parameters
```
positional arguments:
  bids_path             The path to the top level of the bids dataset
  best_image_table      Path to the tsv file containing information on the best series for each
                        session
  data_dictionary_dir   Path the the directory to store the generated input_data_dictionary__.json
                        files
  pipeline_script       Path to the python pipeline script to run BAW using pydra
  experimental_config   Path to the experimental configuration json file defining settings for each of
                        the BRAINSTools applications
  environmental_config  Path to the environmental configuration json file defining overall settings
                        for the system being used

optional arguments:
  -h, --help            show this help message and exit
  --output_job_path OUTPUT_JOB_PATH
                        Output path to the job file that will be run to execute the pipeline on all
                        the input data dictionary files
  --max_sessions_per_file MAX_SESSIONS_PER_FILE
                        The number of sessions to be recorded per json file (-1 for all sessions in
                        one file)
  --session_count SESSION_COUNT
                        The number of sessions from which to have data extracted
  --original_sessions_list_file ORIGINAL_SESSIONS_LIST_FILE
                        The path to a list file where each line is a session (sess-#####) processed in
                        the original BAW predicthd run
  --bad_sessions_list BAD_SESSIONS_LIST
                        The path to a list file where each line is a session (sess-####) that should
                        not be processed
```

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

#### Parameters
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

### Other Notes

#### Rerunning the Pipeline
If all array job entries in pipeline_10.job complete, but not all sessions are fully processed, rerun the pipeline. Before rerunning, run the command `rm *.lock` in the cache_dir given in the `config_experimental` JSON file. Then, run the same command used to run the pipeline, as in `Running the Pipeline/Example`
