#!/usr/bin/env bash
set -ex
export CHG_ROOT_DIR=$(pwd)
source chg/scripts/defaults.sh

if [ ! -z ${CONDA_EXE} ]
then
	source $(dirname ${CONDA_EXE})/../etc/profile.d/conda.sh
	conda env remove -n ${CHG_CONDA_ENV}
fi
rm -rf ${CHG_RESOURCES}
