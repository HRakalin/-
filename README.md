在Windows操作系统下安装python3.8 
网上搜索任意一个可编程交互式中文语音识别系统进行环境搭建，本人使用的是百度短语音平台提供的语言模型。
硬件准备：电烙铁、焊锡、螺丝刀套装、剪刀、剥线钳、若干跳线/杜邦线、USB转485模块、串口控制继电器模块（5V供电）、USB电风扇（5V供电）
软件准备：
a）在pycharm终端中安装serial, 命令为：pip install serial
b）在pycharm终端中安装pyaudio, 命令为：pip install pyaudio
c）在pycharm终端中安装aip, 命令为：pip install baidu_aip
d）在pycharm终端中安装pyaudio, 命令为：pip install pyaudio
e）在pycharm终端中安装modbus_tk，命令为：pip install modbus_tk
f）在http://www.wch.cn/products/CH340.html 下载 CH340 驱动并安装
6、连接（如下图所示）：
![image](https://github.com/user-attachments/assets/29bafb88-b84a-415d-b29e-0617c977f89d)

之后将USB转485模块连接电脑，在“我的电脑”->“设备管理器”
中找到模块所对应的USB 端口，如下图所示（下图对应COM5）:
![image](https://github.com/user-attachments/assets/97ceecc8-47c4-449d-b0fa-130a89342718)

之后在http://www.windiiot.com/product.html 下载 C2S0301 对应的“上位机配置工具”，并以管理员权限运行，尝试“连接模块”看是否成功。如果“模块版本”和“模块名称”正常显示则表明模块连接成功，如下图所示：
![image](https://github.com/user-attachments/assets/d8ccb95c-a7a2-4b4b-981a-5115938d4045)

之后我们在代码处实现模块的连接和继电器线圈的控制： 
a) 根据http://www.windiiot.com/product.html C2S0301 的“技术参考手册”我们得知，连接模块的原理是读取成功读取模块输入寄存器和保持寄存器，于是我们在python中写如下代码进行模块初始化连接： 

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
b) 之后我们在C2S0301的“技术参考手册”得知写单个线圈指令为0x05,状态常量为0xFF00为请求线圈接通，0x0000则为线圈断开，于是我们写如下代码来控制继电器开合：

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
c) 之后编写录音函数来实现音频数据的存储

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
d) 在之后，使用百度短语言识别的语言模型进行实时的语言识别

    def recognize_audio(audio_data):
        result = client.asr(audio_data, 'pcm', 16000, {'dev_pid': 1537})
        if 'result' in result and len(result['result']) > 0:
            command = result['result'][0]  # 获取语音识别结果
            print("识别结果:", command)
            return command
        else:
            print("未能识别语音")
            return ""
f) 最后，联动语音识别控制代码，我们可以实现语音命令控制风扇开关的功能。


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
实际效果：
![image](https://github.com/user-attachments/assets/4582d5dc-de34-4f62-8fcd-be6a1a6886d1)

