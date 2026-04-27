sudo apt update
sudo apt install python3-venv python3-pip -y

python3 -m venv pythonEnv
source pythonEnv/bin/activate
pip install -r requirements.txt
