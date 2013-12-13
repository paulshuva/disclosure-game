#!/bin/bash
#PBS -l walltime=12:00:00
#PBS -l nodes=1:ppn=16
#PBS -l pmem=1gb
GAME[1]='-g CarryingInformationGame CaseloadSharingGame -s SharingBayesianPayoffSignaller -r SharingBayesianPayoffResponder'

GAME[2]='-g CarryingInformationGame CaseloadSharingGame -s SharingLexicographicSignaller -r SharingLexicographicResponder'

GAME[3]='-g CarryingInformationGame CaseloadSharingGame -s SharingPayoffProspectSignaller -r SharingPayoffProspectResponder'

cd disclosure-game/python
ulimit -n 512
module load python
#source /home/jg1g12/hpc/bin/activate
python Run.py -R 10 ${GAME[$PBS_ARRAYID]} --pickled-arguments women_proportions.args -f ${PBS_ARRAYID}_women_proportions -i 1000 -d /scratch/jg1g12