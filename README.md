conda create -n scenereconstruction python=3.9
conda activate scenereconstruction

Desktop:
pip install -r requirements_desktop.txt

CUDA=12.4
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124

Server:
pip install -r requirements_server.txt
