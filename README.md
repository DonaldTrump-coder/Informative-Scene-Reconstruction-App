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

uvicorn server:app --host 0.0.0.0 --port 8000
