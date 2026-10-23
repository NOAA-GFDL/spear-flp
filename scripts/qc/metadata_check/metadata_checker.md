# Metadata Checker

Checks that the metadata within a set of netCDF files (stored in `input_directory/<member_search_pattern>/.../*.nc`) matches the values in `expected_metadata`.

The main script is `metadata_checker.py`, authored by Soelem Aafnan Bhuiyan.

This script parses a config yaml to inform the checks that it performs. Check `example_metadata.yaml` for an example configuration for minimum daily surface temperature, `t_ref_min`, at GFDL. The configuration file takes the following options:

- `variable_name` : the ID of the variable to check. E.g., for precipitation this could be `pr`
- `input_directory` : where to look for netCDF datasets
- `output_directory` : where to save results to, defaults to `outputs`
- `output_filename` : results filename, defaults to `failed_metadata.csv`
- `log_file` : where to save logs
- `member_search_pattern` : how to search for ensemble members or realizations, defaults to `pp_ens_*`
- `file_search_pattern` : pattern to search for datasets, defaults to `f"*{variable_name}*.nc"`
- `expected_metadata` : defines the expected metadata
  - `globals` : list of dataset attributes to look for along with their expected values
  - `dimensions` : list of coordinates to verify, along with their expected sizes
  - `variables` : list of variables, then list the expected attributes of those variables