# FREMOR output checker

This script checks that four numerical values (min, max, mean, std dev) match between the input datasets pre-processed datasets and the output CMORized datasets. This assumes that you've run `get_ens_stats.py` for all the pre-processed datasets and will take the base output directory given to that script as an input to look for the already-computed stats.

The main script is `check_cmor_spear.py`. The `--help` option provides a summary of how to use it:
```
$ python check_cmor_spear.py --help
usage: check_cmor_spear.py [-h] [--table_id TABLE_ID] [--variable_id VARIABLE_ID]
                           [--experiment_id EXPERIMENT_ID] [--mappings MAPPINGS]
                           catalog_path stats_dir

Verifies FRE CMOR output of SPEAR data using catalogs to search for datasets

positional arguments:
  catalog_path          Path to input csv catalog that describes the CMORized data. This could be
                        the CSV of an intake-esm catalog, output by CatalogBuilder.
  stats_dir             Same as the base_path in get_ens_stats.py, tells this script where to look
                        for the precomputed pre-CMORization stats.

options:
  -h, --help            show this help message and exit
  --table_id TABLE_ID   Allows to filter the catalog by a specific table_id.
  --variable_id VARIABLE_ID
                        Allows to filter the catalog by a specific variable_id.
  --experiment_id EXPERIMENT_ID
                        Allows to filter the catalog by a specific experiment_id.
  --mappings MAPPINGS   Describes how to map the experiment_id, table_id, and variable_id to the
                        precomputed stats directory structure. See the default file
                        spear_mappings.json for an example of how to format this.
```

The script `check_cmor_spear_one.sh` is an example of how to submit a single job to slurm. This will work running on analysis nodes at GFDL.

The file `submit_check_cmor.py` will submit fremor checker as slurm jobs, running a separate job for each experiment_id, table_id, and variable_id set.
```
$ python submit_check_cmor.py --help
usage: submit_check_cmor.py [-h] [--mappings MAPPINGS] catalog_path stats_dir

Submits fremor checker as slurm jobs, running a separate job for each experiment_id, table_id, and variable_id set. Check docs for necessary edits to the slurm script.

positional arguments:
  catalog_path         Path to input csv catalog that describes the CMORized data. This could be
                       the CSV of an intake-esm catalog, output by CatalogBuilder.
  stats_dir            Same as the base_path in get_ens_stats.py, tells this script where to look
                       for the precomputed pre-CMORization stats.

options:
  -h, --help           show this help message and exit
  --mappings MAPPINGS  Describes how to map the experiment_id, table_id, and variable_id to the
                       precomputed stats directory structure. See the default file
                       spear_mappings.json for an example of how to format this.
```