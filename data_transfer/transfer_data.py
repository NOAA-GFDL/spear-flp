import argparse
import subprocess
from pathlib import Path
import polars as pl
import shutil

path_template = [
    'experiment_id',
    'member_id',
    'realm',
    'cell_methods',
    'frequency',
    'chunk_freq'
]

allowed_filters = [
    'realm',
    'variable_id',
    'experiment_id',
    'frequency',
    'chunk_freq'
]

parser = argparse.ArgumentParser(
    prog='SPEAR data mover',
    description='Moves SPEAR data described by an input catalog'
)

parser.add_argument('source_catalog')
parser.add_argument('destination')

# Filters:
for x in allowed_filters:
    parser.add_argument(f'--{x}')

# Options:
parser.add_argument(
    '-n',
    '--dry_run', 
    action='store_true'
)
parser.add_argument(
    '--run_one', 
    action='store_true'
)
parser.add_argument(
    '--tmp_dir',
    default=None
)
parser.add_argument(
    '--log_dir', 
    default=None
)

def transfer_data(
    source_catalog,
    destination,
    filters={},
    tmp_dir=None,
    log_dir=None,
    dry_run=False,
    run_one=False    
):
    if dry_run:
        rsync_flags = '-airnv'
        print(f'-----DRY RUN-----')
    else:
        rsync_flags = '-airv'
    
    baseDir = Path(destination)

    if tmp_dir:
        tmpDir = Path(tmp_dir)
    else:
        tmpDir = baseDir / 'tmp'
    if tmpDir.is_dir():
        shutil.rmtree(tmpDir)
    tmpDir.mkdir(parents=True)
    print(f'Saving tmp files to {str(tmpDir)}')

    if log_dir:
        logDir = Path(log_dir)
    else:
        if dry_run:
            logDir = baseDir / 'logs' / 'dry'
        else:
            logDir = baseDir / 'logs'
    logDir.mkdir(parents=True, exist_ok=True)
    print(f'Saving slurm logs to {str(logDir)}')
    
    cat_df = pl.read_csv(source_catalog)
    print(f'Filtering by {filters}')
    subdf = cat_df.filter(*[pl.col(k).is_in(v) for k,v in filters.items()])
    print(f'Filter result shape is {subdf.shape}')
    
    for grp,df in subdf.group_by(path_template):
        dest_folder = Path(destination) / '/'.join(grp)
        dest_folder.mkdir(parents=True, exist_ok=True)

        dmget_filelist = tmpDir/('.'.join(grp) + '.dmget.csv')
        df.select('path').write_csv(dmget_filelist, include_header=False)

        rsync_filelist = tmpDir/('.'.join(grp) + '.rsync.csv')
        df.select(pl.col('path').str.split(by='/').list.get(-1)).write_csv(
            rsync_filelist, 
            include_header=False
        )

        jobName = 'trnsfr.'+'.'.join(grp)
        logPath = str(logDir / (jobName+'.%j'))

        subprocess.run([
            "sbatch",
            "-J",
            jobName,
            "--output",
            logPath+'.out',
            "--error",
            logPath+'.err',
            "/work/a3r/Documents/code/spear-flp/data_transfer/transfer_data.sh",
            dmget_filelist,
            rsync_filelist,
            rsync_flags,
            Path(df['path'][0]).parent,
            Path(destination) / '/'.join(grp)
        ])

        if run_one:
            print('run_one set to True, breaking loop')
            break

if __name__ == '__main__':
    args = parser.parse_args()
    filter_args = {
        k:v.split(',') for k,v in vars(args).items()
        if k in allowed_filters and v is not None
    }
    transfer_data(
        args.source_catalog,
        args.destination,
        log_dir=args.log_dir,
        dry_run=args.dry_run,
        run_one=args.run_one,
        tmp_dir=args.tmp_dir,
        filters=filter_args
    )
    
