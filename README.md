# nacan

# 确认版本
python3 --version

# 添加apt-get模块
sudo apt-get install python3-apt --reinstall

# 载入本脚本
wget -c https://github.com/xhjvpn/nacan/releases/download/1.0/nc.tar.gz -O - | tar -xz
cd nc

# 安装依赖
pip install --upgrade pip
# 安装依赖
apt install python3-pip
# 安装依赖
pip3 install -r requirements.txt
# 运行
python3 main.py
