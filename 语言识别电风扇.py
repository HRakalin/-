import pyaudio ##音频处理库，它提供了一种与音频设备进行输入和输出交互的方式。
import wave
from aip import AipSpeech
import threading
import serial
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu

# 设置百度语音识别的APPID, API KEY 和 SECRET KEY
APP_ID = '70954175'
API_KEY = 'W4aBaXQ6fogPvOsD2I68Kd7A'
SECRET_KEY = 'CZ2yEZyOMCcsCF5fotw55tf2GWMJA8Sq'

# 创建百度语音识别对象
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

# 配置音频流
FORMAT = pyaudio.paInt16 ##音频的格式
CHANNELS = 1  ##音频通道
RATE = 16000  ##采样率
CHUNK = 1024   ##每次读取或写入的音频数据块的大小
RECORD_SECONDS = 5  # 每次录音的时长，单位：秒

# 串口继电器配置
RELAY_PORT = 'COM5'  # 串口端口，需要手动填写
RELAY_RESPONSE_TIMEOUT = 5.0  # 串口响应超时时间，单位：秒

# 连接串口继电器
def ConnectRelay(port):
    try:
        # 创建串口继电器对象
        master = modbus_rtu.RtuMaster(serial.Serial(port=port, baudrate=9600, bytesize=8, parity='E', stopbits=1))
        master.set_timeout(RELAY_RESPONSE_TIMEOUT)
        master.set_verbose(True)

        # 读取输入寄存器
        master.execute(2, cst.READ_INPUT_REGISTERS, 0, 2)

        # 读取保持寄存器
        master.execute(2, cst.READ_HOLDING_REGISTERS, 0, 1)

        # 连接成功
        return 1, master
    except Exception as exc:
        print(str(exc))
        # 连接超时或出错
        return -1, None

# 控制继电器开关
def Switch(master, action):
    try:
        if "on" in action.lower():
            # 继电器闭合，开启风扇
            master.execute(2, cst.WRITE_SINGLE_COIL, 0, output_value=1)## output_value=1 表示将线圈值设置为 1，即闭合继电器
        else:
            # 继电器断开，关闭风扇
            master.execute(2, cst.WRITE_SINGLE_COIL, 0, output_value=0)## output_value=1 表示将线圈值设置为 0，即断开继电器。

        # 操作成功
        return 1
    except Exception as exc:
        print(str(exc))
        # 操作失败
        return -1

# 录音函数
def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("开始录音，请说话...")

    frames = []##存储每次读取的音频数据帧
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("录音结束")

    stream.stop_stream()
    stream.close()##释放 stream 资源
    p.terminate()##释放 p 资源

    audio_data = b''.join(frames)
    return audio_data

# 实时识别函数
def recognize_audio(audio_data):
    result = client.asr(audio_data, 'pcm', 16000, {'dev_pid': 1537})
    if 'result' in result and len(result['result']) > 0:
        command = result['result'][0]  # 获取语音识别结果
        print("识别结果:", command)
        return command
    else:
        print("未能识别语音")
        return ""

# 录音并实时识别函数
def recognize_realtime():
    # 连接串口继电器
    response_code, relay_master = ConnectRelay(RELAY_PORT)##连接到串口继电器
    if response_code < 0:
        print("无法连接串口继电器，程序退出")
        return

    while True:
        audio_data = record_audio()  # 录音
        command = recognize_audio(audio_data)  # 实时语音识别
        if command:
                if "打开" in command:
                    Switch(relay_master, "ON")
                elif "关闭" in command:
                    Switch(relay_master, "OFF")
                else:
                    print("未识别的命令")

# 测试实时识别函数
recognize_realtime()
