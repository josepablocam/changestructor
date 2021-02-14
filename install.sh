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

# install fasttext
# we'll use this to create embeddings for our classes
wget https://github.com/facebookresearch/fastText/archive/v0.9.2.zip
unzip v0.9.2.zip
mv fastText-0.9.2 "${CHG_RESOURCES}/fasttext-install"
rm v0.9.2.zip
pushd "${CHG_RESOURCES}/fasttext-install"
make
pip install .
popd
ln -s "${CHG_RESOURCES}/fasttext-install/fasttext" "${CHG_RESOURCES}/fasttext"
export PATH=${PATH}:"${CHG_RESOURCES}"


# install faiss
conda install faiss-cpu -c pytorch

pip install pytest

# install nltk
pip install nltk

# install changestructor
pip install -e .

# run tests
pytest

chmod +x bin/chg
chmod +x bin/chg-to-index
chmod +x bin/git-to-chg

export PATH=${PATH}:$(realpath bin/)
