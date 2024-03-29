#!/usr/bin/env bash
set -ex
export CHG_ROOT_DIR=$(pwd)
source chg/scripts/defaults.sh
mkdir -p ${CHG_RESOURCES}

# Install conda if not available
function install_conda_if_needed() {
    if ! command -v conda &> /dev/null
      then
        curl https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh -L --output miniconda.sh\
            && bash miniconda.sh -b \
            && rm -f miniconda.sh

            export PATH=~/miniconda3/bin/:${PATH}
            source ~/miniconda3/etc/profile.d/conda.sh
    fi
}


# Use conda (easiest to install FAISS)
# for our libs here
install_conda_if_needed
conda create -n ${CHG_CONDA_ENV} python=3.7


source $(dirname ${CONDA_EXE})/../etc/profile.d/conda.sh
conda activate ${CHG_CONDA_ENV}

# install some utilities
pip install tqdm

# using codebert to embed changes and dialogue
# https://github.com/microsoft/CodeBERT
pip install torch
pip install transformers

# install faiss
conda install faiss-cpu -c pytorch

pip install pytest

# install nltk
pip install nltk
# install nltk resources
mkdir -p "${CHG_RESOURCES}/nltk_data"
python -c "import nltk; nltk.download('punkt', download_dir='${CHG_RESOURCES}/nltk_data')"
python -c "import nltk; nltk.download('averaged_perceptron_tagger', download_dir='${CHG_RESOURCES}/nltk_data')"

pip install astunparse
pip install scikit-learn

# install changestructor
pip install -e .

# run tests
pytest

chmod +x bin/chg
chmod +x bin/chg-to-index
chmod +x bin/git-to-chg

export PATH=${PATH}:$(realpath bin/)
