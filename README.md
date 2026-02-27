conda create -n scenereconstruction python=3.9
conda activate scenereconstruction

Desktop:
CUDA=12.4
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements_desktop.txt

Server:
CUDA=11.8
pip install torch==2.0.0 torchvision==0.15.1 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements_server.txt
python -m pip install server/colmap

sudo apt-get install \
    git \
    cmake \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libopenimageio-dev \
    openimageio-tools \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libgmock-dev \
    libsqlite3-dev \
    libglew-dev \
    qt6-base-dev \
    libqt6opengl6-dev \
    libqt6openglwidgets6 \
    libcgal-dev \
    libceres-dev \
    libsuitesparse-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libmkl-full-dev

sudo apt install -y \
  libopenexr-dev \
  libopenimageio-dev \
  libboost-all-dev \
  libceres-dev \
  libeigen3-dev \
  libflann-dev \
  libfreeimage-dev \
  libgflags-dev \
  libgoogle-glog-dev \
  libsqlite3-dev \
  qtbase5-dev \
  libglew-dev \
  libcgal-dev

sudo mkdir -p /usr/include/opencv4

sudo apt-get install -y \
    nvidia-cuda-toolkit \
    nvidia-cuda-toolkit-gcc

mkdir build
cd build
cmake .. -GNinja -DBLA_VENDOR=Intel10_64lp
ninja
sudo ninja install

uvicorn server.main:app --host 0.0.0.0 --port 8000
将端口8000映射到用户
