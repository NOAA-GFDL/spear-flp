import pandas as pd
import polars as pl
import numpy as np
import xarray as xr
import dask
import os,sys
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from stac_utils import convert_timerange
from pathlib import Path

tstr = "%Y-%m-%d"

# output_path_template = ['institution_id','source_id','experiment_id',"table_id","variable_id","grid_label","version_id"]
output_path_template = ['experiment_id', 'realm']
# output_file_template = ["variable_id","table_id",'source_id',"experiment_id","grid_label"]
output_file_template = ['variable_id']
output_path = '.'

class BasicQAPlots:
    def __init__(self,
            catalog_file,
            base_output_path,
            output_path_template,
            output_file_template,
            catalog_filter=None
        ):
        # self.catalog = pd.read_csv(catalog_file).dropna(axis=1, how='all')
        # dfcat = pd.read_csv(catalog_file).dropna(axis=1, how='all')
        # self.catalog = dfcat[(dfcat['variable_id'] == 'pr') & 
        #                      (dfcat['table_id'] == '6hr') & 
        #                      (dfcat['experiment_id'] == 'historical') &
        #                      (dfcat['member_id'] == 'r1i1p1f1')]
        # self.column_filter = ((self.catalog.columns != 'path') & 
        #                       (self.catalog.columns != 'time_range') &
        #                       (self.catalog.columns != 'member_id') &
        #                       (self.catalog.columns != 'pass_qc') &
        #                       (self.catalog.columns != 'who_qc'))
        # self.item_columns = self.catalog.columns[self.column_filter].to_list()

        df1 = pl.read_csv(catalog_file)
        if catalog_filter is not None:
            df = df1.filter(catalog_filter)
        else:
            df = df1
        
        self.catalog = df[
            [s.name for s in df if not (s.null_count() == df.height)]
        ].drop(['pass_qc','who_qc'], strict=False)

        self.item_columns = self.catalog.columns
        for i in ['path', 'time_range', 'member_id']:
            self.item_columns.remove(i)
        
        self.base_output_path = base_output_path
        self.output_path_template = output_path_template
        self.output_file_template = output_file_template
    
    def get_paths(self, group, create=False):
        item_metadata = { c:v for c,v in zip(self.item_columns, group) }
        path = self.base_output_path + '/'.join(
                [item_metadata[o] for o in self.output_path_template]
            ) + '/' 
        if create:
            Path(path).mkdir(parents=True, exist_ok=True)
        fname = '_'.join([item_metadata[o] for o in self.output_file_template])
        csv_fname = path + fname + '.csv'
        avg_fname = path + fname + '_avg.png'
        std_fname = path + fname + '_std.png'
        return csv_fname, avg_fname, std_fname
    
    def calc_vals(self):
        for grp,df in self.catalog.group_by(self.item_columns):
            print(grp)
            file_names = self.get_paths(grp, create=True)

            if os.path.isfile(file_names[1]) & os.path.isfile(file_names[2]):
                continue

            if not os.path.isfile(file_names[0]):
                pd.DataFrame(
                    columns=['member_id', 'min', 'max', 'mean', 'std']
                ).to_csv(
                    file_names[0],
                    index=False
                )

            for m,subdf in df.group_by('member_id'):
                if m in pd.read_csv(file_names[0])['member_id'].to_list():
                    print(f"Skipping {m}")
                    continue
                
                var_id = subdf['variable_id'].unique()[0]
                ds = xr.open_mfdataset(
                    subdf['path'], 
                    parallel=True, 
                    chunks='auto',
                    engine='netcdf4'
                )[var_id]

                weights = np.cos(np.deg2rad(ds.lat))
                weights.name = "weights"
                avgval_lazy = ds.weighted(weights).mean()
                stdval_lazy = ds.weighted(weights).std()

                minval_lazy = ds.min()
                maxval_lazy = ds.max()

                avgval, stdval, minval, maxval = dask.compute(
                    avgval_lazy, 
                    stdval_lazy,
                    minval_lazy,
                    maxval_lazy
                )
                results = {
                    'member_id' : [m],
                    'min' : [float(minval)],
                    'max' : [float(maxval)],
                    'mean' : [float(avgval)], 
                    'std' : [float(stdval)]
                }
                # print(results)
                pd.DataFrame(results).to_csv(
                    file_names[0],
                    mode='a',
                    index=False,
                    header=False
                )
    
    def gen_plots(self):
        for grp,df in self.catalog.groupby(self.item_columns):
            file_names = self.get_paths(grp, create=True)

            if os.path.isfile(file_names[1]) & os.path.isfile(file_names[2]):
                continue

            if not os.path.isfile(file_names[0]):
                pd.DataFrame(columns=['member_id', 'mean', 'std']).to_csv(
                    file_names[0], index=False
                )

            try:
                df = pd.read_csv(file_names[0])
            except FileNotFoundError:
                print(f"Error: '{csv_filename}' not found.")
                print(f"Error: {grp} values not found, skipping.")

def main(catalog_url, member_id):
    qaplots = BasicQAPlots(catalog_url, output_path, output_path_template, 
                output_file_template)
    qaplots.calc_vals()

if __name__=='__main__':
    ens_id = f'pp_ens_{sys.argv[2].zfill(2)}'
    main(sys.argv[1], ens_id)