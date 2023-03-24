from flask import Flask, request, jsonify
import hashlib
import time
import xmltodict
import openai
import os
import requests
import json
import ssl
from chatbotv3 import Chatbot

os.environ['GPT_ENGINE'] = 'gpt-3.5-turbo'
appid = os.environ.get('app_id')
appsecret = os.environ.get('app_secret')
api_key = os.environ.get('API_KEY')
access_token = ''
expire_time = 0
#每人一个gpt实例
bot_list: dict = {
    '': Chatbot(api_key=api_key)
}
#回答列表
a_list: dict = {
    '': list()
}
#问题列表
q_list: dict = {
    '': list()
}


app = Flask(__name__)

@app.route('/')
def index():
    return 'hello world！'


@app.route('/wechat',methods=['GET','POST'])
def wechat():
    if request.method =='GET':
        # 设置token,开发者配置中心使用
        token = 'hsuheinrich003'

        # 获取微信服务器发送过来的参数
        data = request.args
        signature = data.get('signature')
        timestamp = data.get('timestamp')
        nonce = data.get('nonce')
        echostr = data.get('echostr')

        # 对参数进行字典排序，拼接字符串
        temp = [timestamp, nonce, token]
        temp.sort()
        temp = ''.join(temp)

        # 加密
        if (hashlib.sha1(temp.encode('utf8')).hexdigest() == signature):
            return echostr
        else:
            return 'error', 403

    # 根据请求方式进行判断
    if request.method == 'POST':
        # 获取微信服务器post过来的xml数据
        xml = request.data
        try:
            # 把xml格式的数据进行处理，转换成字典进行取值
            req = xmltodict.parse(xml)['xml'] # 云端调试空内容报错解决：no element found
        except:
            return 'no element', 200

        print('req=' + str(req))
        userName = req.get('FromUserName')
        botName = req.get('ToUserName')
        # 判断post过来的数据中数据类型是不是文本
        if 'text' == req.get('MsgType'):
            # 获取用户的信息，开始构造返回数据
            try:
                msg = req.get('Content')
                # 新用户，新建list
                if a_list.get(userName) == None:
                    a_list.setdefault(userName, list())
                    q_list.setdefault(userName, list())
                    bot_list.setdefault(userName, Chatbot(api_key=api_key))
                if msg in ['。', '你好', 'hi']:
                    resp = {
                        'ToUserName':userName,
                        'FromUserName':botName,
                        'CreateTime':int(time.time()),
                        'MsgType':'text',
                        'Content': '我醒了请提问~'
                    }
                    xml = xmltodict.unparse({'xml':resp})
                    return xml
                else:
                    answer = bot_list[userName].ask(msg)
                    # a_list.get(userName).append(answer)
                    # q_list.get(userName).append(msg)
                    # resp = {
                    #     'ToUserName':req.get('FromUserName'),
                    #     'FromUserName':req.get('ToUserName'),
                    #     'CreateTime':int(time.time()),
                    #     'MsgType':'text',
                    #     'Content': answer
                    # }
                    # 把构造的字典转换成xml格式
                    # xml = xmltodict.unparse({'xml':resp})
                    # return xml
                    sendMessageToBot('['+msg+']\n'+answer, userName, botName)
                    return ''
            except Exception as e:
                resp = {
                    'ToUserName':req.get('FromUserName'),
                    'FromUserName':req.get('ToUserName'),
                    'CreateTime':int(time.time()),
                    'MsgType':'text',
                    'Content':'好像发生了点问题\n'+str(e)
                }
                xml = xmltodict.unparse({'xml':resp})
                return xml
        else:
            resp = {
                'ToUserName': req.get('FromUserName', ''),
                'FromUserName': req.get('ToUserName', ''),
                'CreateTime': int(time.time()),
                'MsgType': 'text',
                'Content': '目前仅支持文本消息～'
            }
            xml = xmltodict.unparse({'xml':resp})
            return xml

def GetAccessToken():
    global access_token
    global expire_time
    url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + str(appid) + "&secret=" + str(appsecret)
    res = requests.get(url, verify=False)
    access_token = json.loads(res.text).get('access_token')
    expire_time = time.time() + 7200
    print(access_token, expire_time)

def sendMessageToBot(msg: str, toUserName: str, botName: str):
    global access_token
    global expire_time
    if len(access_token) == 0 or time.time() > expire_time:
        GetAccessToken()
    body = {
            'touser':findOpenid(botName, toUserName),
            'msgtype':'text',
            'text':{
                'content':msg
            }
        }
    requests.post(
        url='https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=' + access_token,
        data=bytes(json.dumps(body, ensure_ascii=False).encode('utf-8')),
        verify=False
    )

def findOpenid(botName: str, fromName: str):
    if botName == 'gh_ae8f15469043':
        return fromName
    dict = {
        # zjc
        'oVkbM52ybms9ag_jyOop64TpT5OM':'odWUz6YvwpkPcTU3NinUd5Cy1jsM',
        # lff
        'oVkbM54D4yjOGMaYSPIh12kcMn1Q':'odWUz6aFvfhRQ3cSsCo1sxPp7pus'
    }
    if dict[fromName]:
        return dict[fromName]
    return ''

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
