import argparse
import subprocess
from pathlib import Path
import shutil
import polars as pl
import json

parser = argparse.ArgumentParser(
    prog='SPEAR catalog builder',
    description='Creates a catalog for SPEAR data stored on archive'
)
parser.add_argument('output')
parser.add_argument('--config', default=None)

freq_mapping = {
    'day' : 'daily',
    'mon' : 'monthly',
    'yearly' : 'annual',
    '6hr' : '6hr'
}

def main(output, config=None):
    output_dir = Path(output).parent
    tmpdir = output_dir / 'tmp'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir()

    cats_list = []
    
    for input_prefix in [
        '/archive/wfc/SPEAR/SPEAR_c192_o1_Hist_AllForc_IC1921_K50_',
        '/archive/wfc/SPEAR/SPEAR_c192_o1_Scen_SSP585_IC2011_K50_'
    ]:
        for n in range(0,10):
            i1 = str(3*n + 1).zfill(2)
            i2 = str(3*n + 2).zfill(2)
            i3 = str(3*n + 3).zfill(2)

            ens_mapping = {
                f'pp_ens_{i}' : f'pp_ens_{j}' 
                for i,j in zip(['01','02','03'], [i1,i2,i3])
            }

            input_path = input_prefix + f'ens_{i1}_{i3}/'

            tmp_output_path = tmpdir / f'catalog'

            subprocess.run([
                'gen_intake_gfdl',
                input_path,
                tmp_output_path,
                '--config',
                config,
                '--overwrite'
            ])

            catalog = pl.read_csv(str(tmp_output_path) + '.csv')

            cats_list.append(catalog.filter(
                (pl.col('member_id') != 'pp_ensemble') &
                (pl.col('frequency') != 'fx') &
                (pl.col('cell_methods') == 'ts')
            ).with_columns(
                experiment_id=pl.col('experiment_id').str.split(by='_').list.slice(0, 7).list.join('_'),
                member_id=pl.col('member_id').replace(ens_mapping),
                frequency=pl.col('frequency').replace(freq_mapping)
            ))
    
    print(f'Saving catalog file {str(output)+'.csv'}')
    pl.concat(cats_list).write_csv(str(output)+'.csv')

    with open(tmpdir / 'catalog.json') as f:
        catalog_json = json.load(f)
    catalog_json['catalog_file'] = str(output)+'.csv'
    print(f'Saving catalog json file {str(output)+'.json'}')
    with open(str(output)+'.json', 'w') as f:
        json.dump(catalog_json, f, indent=4)
    
    print('Cleaning up temporary files...')
    shutil.rmtree(tmpdir)

if __name__=='__main__':
    args = parser.parse_args()
    main(
        args.output,
        config=args.config
    )
