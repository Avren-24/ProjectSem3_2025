# 湿度传感器数据采集系统

通过SSH连接树莓派，读取ADS1115 ADC模块和湿度传感器的真实数据。

## 系统要求

- Windows 10/11
- Python 3.7+
- PyCharm（推荐）
- 树莓派（已启用SSH）
- ADS1115 ADC模块
- 湿度传感器

## 硬件连接

1. **ADS1115连接到树莓派**：
   - VDD → 3.3V
   - GND → GND
   - SCL → GPIO 3 (SCL)
   - SDA → GPIO 2 (SDA)

2. **湿度传感器连接到ADS1115**：
   - 传感器输出 → ADS1115 A0通道
   - 传感器电源 → 3.3V或5V（根据传感器规格）
   - 传感器地 → GND

3. **树莓派配置**：
   ```bash
   # 启用I2C
   sudo raspi-config
   # 选择 Interfacing Options → I2C → Enable
   
   # 安装I2C工具
   sudo apt-get update
   sudo apt-get install -y i2c-tools
   
   # 检查ADS1115是否连接（应该看到0x48）
   i2cdetect -y 1
   ```

## 安装步骤

### 方法1：一键安装（推荐）

1. 双击运行 `install_dependencies.bat`
2. 等待安装完成

### 方法2：手动安装

```bash
pip install -r requirements.txt
```

## 配置

1. 编辑 `raspberry_pi_config.txt` 文件，填入你的树莓派连接信息：
   ```
   HOSTNAME=192.168.1.100  # 你的树莓派IP地址
   USERNAME=pi             # SSH用户名
   PASSWORD=your_password  # SSH密码
   PORT=22                 # SSH端口
   ```

2. 或者设置环境变量：
   - `PI_HOSTNAME`: 树莓派IP或主机名
   - `PI_USERNAME`: SSH用户名
   - `PI_PASSWORD`: SSH密码
   - `PI_PORT`: SSH端口

## 使用方法

1. 在PyCharm中打开项目
2. 运行 `sensor_reader.py`
3. 程序会自动：
   - 连接到树莓派
   - 检查硬件连接
   - 上传读取脚本
   - 每秒读取一次湿度数据，共读取10次

## 输出说明

程序会输出：
- 系统连接状态
- 硬件检测结果
- 10组湿度数据（每秒一组）
- 数据采集完成状态

## 故障排除

1. **连接失败**：
   - 检查树莓派SSH是否启用
   - 检查IP地址和端口是否正确
   - 检查防火墙设置

2. **硬件未检测到**：
   - 运行 `i2cdetect -y 1` 检查ADS1115是否连接
   - 检查I2C是否在raspi-config中启用
   - 检查接线是否正确

3. **读取失败**：
   - 检查传感器是否正确连接到ADS1115的A0通道
   - 检查传感器电源连接
   - 根据实际传感器规格调整转换公式

## 注意事项

- 确保树莓派和Windows电脑在同一网络中
- 首次连接可能需要确认SSH主机密钥
- 湿度转换公式需要根据实际传感器规格调整
- 建议使用固定IP地址的树莓派

