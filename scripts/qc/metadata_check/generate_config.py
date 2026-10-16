# Generates a config from a single input netCDF file
# Useful when you have mutlitple files that should have all-matching metadata
# or to create a template to edit.

import argparse
from pathlib import Path
from netCDF4 import Dataset
import yaml

parser = argparse.ArgumentParser(
    description="Generates a config for metadata_checker.py from a single input netCDF file"
)

parser.add_argument(
    'input_file',
    help="Input netCDF file."
)

parser.add_argument(
    'output_file',
    help='Path to yaml to create as output.'
)

parser.add_argument(
    '--skip_attrs',
    default=[],
    help='List of attributes to skip, separate by commas. (e.g., "variant_label,parent_variant_label,realization_index")'
)

def parse_skip_attrs(skip_attrs: str) -> list:
    return skip_attrs.split(',')

def main(input_file,output_file,skip_attrs=[]):
    with Dataset(input_file, 'r') as ds:
        global_attrs = {}
        for attr in ds.ncattrs():
            if attr not in skip_attrs:
                global_attrs[attr] = str(ds.getncattr(attr))

        checked_vars = []
        dim_vars = []
        for v in ds.variables:
            if 'bnds' not in v:
                checked_vars.append(v)
                dim_vars.extend(ds[v].dimensions)
        dim_vars = list(set(dim_vars))

        dim_var_sizes = {}
        for d in dim_vars:
            dim_var_sizes[d] = ds[d].shape[0]
        
        checked_var_attrs = {}
        data_vars = []
        for v in checked_vars:
            if v not in dim_vars:
                data_vars.append(v)
            var_attrs = {}
            for attr in ds[v].ncattrs():
                if attr not in skip_attrs:
                    var_attrs[attr] = str(ds[v].getncattr(attr))
            checked_var_attrs[v] = var_attrs
    
        if len(data_vars) > 1:
            print(f"More than one data variable found: {data_vars}")
        
    config_dict = {}
    config_dict['variable_name'] = data_vars[0]
    config_dict['input_directory'] = str(Path(input_file).parent.resolve())
    config_dict['output_directory'] = "."
    config_dict['output_filename'] = f"failed_{data_vars[0]}_metadata.csv"
    config_dict['log_file'] = f"{data_vars[0]}_metadata.log"

    config_dict['expected_metadata'] = {}
    config_dict['expected_metadata']['globals'] = global_attrs
    config_dict['expected_metadata']['dimensions'] = dim_var_sizes
    config_dict['expected_metadata']['variables'] = checked_var_attrs

    with open(output_file, 'w') as f:
        yaml.dump(config_dict, f)

if __name__=='__main__':
    args = parser.parse_args()
    main(
        args.input_file,
        args.output_file,
        skip_attrs=args.skip_attrs
    )


