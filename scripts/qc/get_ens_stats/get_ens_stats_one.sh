#!/bin/bash 
# note this is for running on analysis nodes at GFDL

#SBATCH --partition=analysis
#SBATCH --time=72:00:00
#SBATCH --nodes=1

#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=128GB
#SBATCH --constraint=avx2

module load miniforge
conda activate aria
python ./get_ens_stats.py $1 $2