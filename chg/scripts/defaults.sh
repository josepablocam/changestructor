#!/usr/bin/env
export CHG_CONDA_ENV="changestructor-env"
export CHG_RESOURCES="${CHG_ROOT_DIR}/resources/"

# # per-project paths
export CHG_PROJ_DIR=$(python -m chg.defaults CHG_PROJ_DIR)
export CHG_PROJ_DB_PATH=$(python -m chg.defaults CHG_PROJ_DB_PATH)
