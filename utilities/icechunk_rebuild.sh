#!/bin/bash
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --partition=analysis
#SBATCH --constraint=avx2

module load miniforge
conda activate aria
python /work/a3r/Documents/code/spear-flp/utilities/icechunk_rebuild.py