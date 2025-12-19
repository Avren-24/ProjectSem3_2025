# 快速开始指南

## 第一步：安装依赖

双击运行 `install_dependencies.bat`，等待安装完成。

## 第二步：配置树莓派连接

编辑 `raspberry_pi_config.txt` 文件：

```
HOSTNAME=192.168.1.100    # 改为你的树莓派IP地址
USERNAME=pi                # 改为你的SSH用户名
PASSWORD=your_password     # 改为你的SSH密码
PORT=22                    # 通常不需要改
```

## 第三步：在PyCharm中运行

1. 打开PyCharm
2. 打开项目文件夹
3. 运行 `sensor_reader.py`
4. 程序会自动连接树莓派并读取10组数据

## 树莓派端准备工作

在树莓派上执行以下命令：

```bash
# 1. 启用I2C
sudo raspi-config
# 选择: Interfacing Options → I2C → Enable

# 2. 安装I2C工具
sudo apt-get update
sudo apt-get install -y i2c-tools python3-pip

# 3. 安装ADS1115库
pip3 install Adafruit-ADS1x15

# 4. 检查ADS1115是否连接（应该看到0x48）
i2cdetect -y 1

# 5. 确保SSH已启用
sudo systemctl enable ssh
sudo systemctl start ssh
```

## 硬件连接

- **ADS1115 → 树莓派**:
  - VDD → 3.3V
  - GND → GND  
  - SCL → GPIO 3 (物理引脚5)
  - SDA → GPIO 2 (物理引脚3)

- **湿度传感器 → ADS1115**:
  - 传感器输出 → A0通道
  - 传感器电源 → 3.3V或5V
  - 传感器地 → GND

## 常见问题

**Q: 连接失败怎么办？**
A: 检查树莓派IP地址、SSH是否启用、防火墙设置

**Q: 检测不到ADS1115？**
A: 运行 `i2cdetect -y 1` 检查，确认I2C已启用

**Q: 读取的数据不对？**
A: 检查传感器连接，可能需要根据实际传感器调整转换公式

