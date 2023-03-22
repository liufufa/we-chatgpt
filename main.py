from flask import Flask, request, jsonify
import hashlib
import time
import xmltodict
import openai
import os
from chatbotv3 import Chatbot

os.environ['GPT_ENGINE'] = 'gpt-3.5-turbo'
api_key = os.environ.get('API_KEY')
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
                    if len(a_list.get(userName)) == 0:
                        resp = {
                            'ToUserName':req.get('FromUserName'),
                            'FromUserName':req.get('ToUserName'),
                            'CreateTime':int(time.time()),
                            'MsgType':'text',
                            'Content': '请提问，或回复中文句号查询上一次结果...'
                        }
                    else:
                        resp = {
                            'ToUserName':req.get('FromUserName'),
                            'FromUserName':req.get('ToUserName'),
                            'CreateTime':int(time.time()),
                            'MsgType':'text',
                            'Content': '['+str(q_list.get(userName).pop())+']\n'+str(a_list.get(userName).pop())
                        }
                    xml = xmltodict.unparse({'xml':resp})
                    return xml
                else:
                    answer = bot_list[userName].ask(msg)
                    a_list.get(userName).append(answer)
                    q_list.get(userName).append(msg)
                    resp = {
                        'ToUserName':req.get('FromUserName'),
                        'FromUserName':req.get('ToUserName'),
                        'CreateTime':int(time.time()),
                        'MsgType':'text',
                        'Content': answer
                    }
                    # 把构造的字典转换成xml格式
                    xml = xmltodict.unparse({'xml':resp})
                    return xml
            except Exception as e:
                resp = {
                    'ToUserName':req.get('FromUserName'),
                    'FromUserName':req.get('ToUserName'),
                    'CreateTime':int(time.time()),
                    'MsgType':'text',
                    'Content':'好像发生了点问题，请稍后再重新提问:'+str(e)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
