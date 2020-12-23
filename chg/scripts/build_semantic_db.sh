#!/usr/bin/env

# Produce a "semantic" version of the changestructor database
# By producing embeddings for question/answers (embedding per question + answer)
# Store in high performance FAISS index
# To enable lookups

source ${CHG_ROOT_DIR}/chg/scripts/defaults.sh
export PATH=${PATH}:${CHG_RESOURCES}
source $(dirname ${CONDA_EXE})/../etc/profile.d/conda.sh
conda activate ${CHG_CONDA_ENV}


export CHG_PROJ_DB_TEXT="${CHG_PROJ_DIR}/db.txt"
export CHG_PROJ_DB_VECTORS="${CHG_PROJ_DIR}/db.vec"
export CHG_PROJ_EMBEDDING_MODEL="${CHG_PROJ_DIR}/embeddings"
export CHG_PROJ_FAISS="${CHG_PROJ_DIR}/faiss.db"
NDIM=150

# Chg database to "text"
python -m chg.search.embedded_search text > ${CHG_PROJ_DB_TEXT}


# Create embeddings
fasttext cbow \
  -input ${CHG_PROJ_DB_TEXT} \
  -output ${CHG_PROJ_EMBEDDING_MODEL} \
  -dim ${NDIM}


# Embed chg's database
fasttext print-sentence-vectors "${CHG_PROJ_EMBEDDING_MODEL}.bin" \
  < ${CHG_PROJ_DB_TEXT} \
  > ${CHG_PROJ_DB_VECTORS}


# store the class vectors in FAISS
# so we can perform fast searches
python -m chg.search.embedded_search build \
  --vectors ${CHG_PROJ_DB_VECTORS} \
  --index ${CHG_PROJ_FAISS}
