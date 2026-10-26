# CMOR Checker

Compares two output CSV files from the `get_ens_stats.py` tool. Assumes the first input file has its members labelled by `r*i1p1f1` (in the CMIP style) and the second input file has its members labelled by `pp_ens_*` (in the GFDL style). By default, this adds a column to the first input file called `match` that stores a boolean value that reports whether the values matched for each row. This can also be saved to a separate file by using the `--output_file` option.

```
$ python check_cmor.py --help
usage: check_cmor.py [-h] [-o OUTPUT_FILE] [--mappings MAPPINGS]
                     [--member_column MEMBER_COLUMN]
                     cmorized_stats original_stats

Verifies FRE CMOR output summary statistics by comparing two CSV files. CSV files are
assumed to be created using the get_ens_stats tool from this repository. Output is a
copy of the cmorized_stats file with a new column called match that stores boolean
values.

positional arguments:
  cmorized_stats        Path to file containing stats calculated from CMORized
                        datasets.
  original_stats        Path to file containing stats calculated from pre-CMORized
                        datasets.

options:
  -h, --help            show this help message and exit
  -o, --output_file OUTPUT_FILE
                        Path to write output to. By default this script will save over
                        the cmorized_stats file.
  --mappings MAPPINGS   Path to mappings file. See documentation for how to format
                        this.
  --member_column MEMBER_COLUMN
                        Name of member id column in the CMORized CSV. This defaults to
                        member_id, though CMORized data could often also use
                        variant_label.
```

The mappings JSON file tells this script how to translate between columns in the CMORized CSV and columns in the GFDL format CSV. The format looks something like
```json
{
    <cmor_column> : {
        "map_from" : <column or list of columns in CMORized, optional>,
        "map_to" : <column name in GFDL, optional>,
        "mappings" : {
            <value in CMIP> : <value in GFDL>
        }
    }
}
```
For each CMOR column, this will map values from the `map_from` column to the `map_to` column. `map_from` can be a list, in which case the `mappings` will be a nested dictionary, with an extra level for each additional item in `map_from`. If `map_from` or `map_to` are not specified, the `cmor_column` will be used in each case. See also the example mappings file `spear_mappings.json`.