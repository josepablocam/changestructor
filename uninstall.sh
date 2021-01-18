#!/usr/bin/env bash
set -eux
export CHG_ROOT_DIR=$(pwd)
source chg/scripts/defaults.sh

source $(dirname ${CONDA_EXE})/../etc/profile.d/conda.sh
conda env remove -n ${CHG_CONDA_ENV}
rm -rf ${CHG_RESOURCES}
