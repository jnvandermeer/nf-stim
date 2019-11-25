#!/bin/bash

source /opt/miniconda3/etc/profile.d/conda.sh

conda activate st

cd /home/johan/nf/nf-stim/src

python FeedbackController.py
