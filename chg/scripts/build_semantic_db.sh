#!/usr/bin/env

# Produce a "semantic" version of the changestructor database
# By producing embeddings for question/answers (embedding per question + answer)
# Store in high performance FAISS index
# To enable lookups
set -ex
source ${CHG_ROOT_DIR}/chg/scripts/defaults.sh
export PATH=${PATH}:${CHG_RESOURCES}
source $(dirname ${CONDA_EXE})/../etc/profile.d/conda.sh
conda activate ${CHG_CONDA_ENV}

# make sure we're at the top level of the git dir
CHG_PROJ_DIR="$(python -m chg.defaults 'CHG_PROJ_DIR')"
mkdir -p ${CHG_PROJ_DIR}

# # per-project paths
CHG_PROJ_FAISS="$(python -m chg.defaults 'CHG_PROJ_FAISS')"

# Embed chg's database
python -m chg.embed.basic

# Load embeddings into FAISS for fast search
python -m chg.search.embedded_search

# Build up ranker's model
python -m chg.ranker.model_based_ranking
