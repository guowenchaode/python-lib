########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:\__cache\plan")

from py_lib.func import (
    log,
    log_error,
    sleep,
    dt,
    read_file,
    write_file,
    format_json,
    loop_dir,
)

########################################

import argparse
import os
import time
import traceback
from datetime import datetime

############### SAMPLE ################
# time.sleep(1)


########################################
def build_arg_parser():
    parser = argparse.ArgumentParser(description="Action")
    parser.add_argument("--action", dest="action", required=False, help="action")
    parser.add_argument("--text", dest="text", required=False, help="text")
    args, left = parser.parse_known_args()
    return args


def test(txt):
    log(txt)


########################################
# BODY #
########################################
"""
INPUT YOUR SCRIPT HERE
"""


# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#   合成小语种需要传输小语种文本、使用小语种发音人vcn、tte=unicode以及修改文本编码方式
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
import pyaudio
import wave

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

# pcm_dir = r"W:\Downloads"
pcm_dir = r"D:\__cache\plan"


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {
            "aue": "raw",
            "auf": "audio/L16;rate=16000",
            "vcn": "xiaoyan",
            "tte": "utf8",
        }
        self.Data = {
            "status": 2,
            "text": str(base64.b64encode(self.Text.encode("utf-8")), "UTF8"),
        }
        # 使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
        # self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

    # 生成url
    def create_url(self):
        url = "wss://tts-api.xfyun.cn/v2/tts"
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = (
            'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
            % (self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )
        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        # 拼接鉴权参数，生成url
        url = url + "?" + urlencode(v)
        # log("date: ",date)
        # log("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # log('websocket url :', url)
        return url


class tts_speaker:
    def __init__(self, text, pac_name="text", on_speak=None):
        self.wsParam = Ws_Param(
            APPID="5c38b07d",
            APISecret="6538336f03a7b4f896dad4af884f98f7",
            APIKey="9205fab03853da6d587883bcbd011004",
            Text=text,
        )
        self.text = text
        websocket.enableTrace(False)
        dts = dt()
        self.pcm_file = f"{pcm_dir}/{pac_name}.{dts}.pcm"
        self.on_speak = on_speak

    def on_message(self, ws, message):
        try:
            message = json.loads(message)
            code = message["code"]
            sid = message["sid"]
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            if code != 0:
                errMsg = message["message"]
                log("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:
                with open(self.pcm_file, "ab") as f:
                    f.write(audio)

            if status == 2:
                play_pcm(self.pcm_file)
                if self.on_speak is not None:
                    self.on_speak()

                log("ws is closed")
                ws.close()
        except Exception as e:
            log("receive msg,but parse exception:", e)

    # 收到websocket错误的处理
    def on_error(self, ws, error):
        log("### error:", error)

    # 收到websocket关闭的处理
    def on_close(self, ws):
        log("### closed ###")

    # 收到websocket连接建立的处理
    def on_open(self, ws):
        def run(*args):
            d = {
                "common": self.wsParam.CommonArgs,
                "business": self.wsParam.BusinessArgs,
                "data": self.wsParam.Data,
            }
            d = json.dumps(d)
            log(f"------>开始发送文本数据{d}")
            ws.send(d)
            if os.path.exists(self.pcm_file):
                os.remove(self.pcm_file)

        thread.start_new_thread(run, ())

    def speak(self):
        log(f"speak [{self.text}]")
        wsUrl = self.wsParam.create_url()
        ws = websocket.WebSocketApp(
            wsUrl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        ws.on_open = self.on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


def speak(text, pac_name="tts", on_speak=None):
    tts = tts_speaker(text, pac_name, on_speak)
    tts.speak()


def pcm2wav(pcm_file, wav_file="", channels=1, bits=16, sample_rate=16000):
    if wav_file == "":
        wav_file = f"{pcm_file}.wav"

    # 打开 PCM 文件
    pcmf = open(pcm_file, "rb")
    pcmdata = pcmf.read()
    pcmf.close()

    # 打开将要写入的 WAVE 文件
    wavfile = wave.open(wav_file, "wb")
    # 设置声道数
    wavfile.setnchannels(channels)
    # 设置采样位宽
    wavfile.setsampwidth(bits // 8)
    # 设置采样率
    wavfile.setframerate(sample_rate)
    # 写入 data 部分
    wavfile.writeframes(pcmdata)
    wavfile.close()


def play_wav(wav_path):
    # 初始化播放器
    p = pyaudio.PyAudio()
    stream = p.open(
        format=p.get_format_from_width(2), channels=1, rate=16000, output=True
    )

    # 将 pcm 数据直接写入 PyAudio 的数据流
    with open(wav_path, "rb") as f:
        stream.write(f.read())

    stream.stop_stream()
    stream.close()
    p.terminate()


def play_pcm(pcm_path):
    wav_path = f"{pcm_path}.wav"
    log(f"play pcm: {pcm_path}")
    pcm2wav(pcm_path, wav_path)
    log(f"play wav: {wav_path}")
    play_wav(wav_path)


# pcm2wave("f1.pcm", "f2.wav")

########################################
########################################

# BOTTOM #
########################################
if __name__ == "__main__":
    try:
        start = datetime.now()
        args = build_arg_parser()
        log(f"__dir__: {__file__}")
        log(f"### [start-try]: action=[{args.action}]")
        ###########################################
        if args.action == "test":
            test(args.text)
        else:
            text = "你好"
            speak(text)
        ###########################################
        end = datetime.now()
        inter = end - start
        log(f"### [end-try]: [{inter}]")
    except:
        traceback.print_exc()
    finally:
        fine = datetime.now()
        inter = fine - start
        log(f"### [finally]: [{inter}]")
