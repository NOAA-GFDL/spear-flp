#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --partition=analysis

DMGET_FILELIST=$1
RSYNC_FILELIST=$2
FLAGS=$3
SOURCE=$4
DEST=$5

if [[ $FLAGS != *"n"* ]]; then
    echo "Running dmget..."
    dmget $(cat $DMGET_FILELIST)
fi

rsync $FLAGS --files-from=$RSYNC_FILELIST $SOURCE $DEST

rm $DMGET_FILELIST
rm $RSYNC_FILELIST
