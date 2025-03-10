import requests
import random
from hashlib import md5
from config import BAIDU_APPID, BAIDU_APPKEY, FROM_LANG, TO_LANG

# 百度翻译API端点
ENDPOINT = 'http://api.fanyi.baidu.com'
PATH = '/api/trans/vip/translate'
URL = ENDPOINT + PATH

def translate_text(text):
    """
    使用百度翻译API翻译文本
    
    Args:
        text: 要翻译的文本
        
    Returns:
        dict: 包含翻译结果的字典，格式如下：
            成功: {'success': True, 'translation': '翻译结果'}
            失败: {'success': False, 'error': '错误信息'}
    """
    try:
        # 生成salt和sign
        salt = random.randint(32768, 65536)
        sign = make_md5(BAIDU_APPID + text + str(salt) + BAIDU_APPKEY)
        
        # 构建请求
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'appid': BAIDU_APPID, 
            'q': text, 
            'from': FROM_LANG, 
            'to': TO_LANG, 
            'salt': salt, 
            'sign': sign
        }
        
        # 发送请求
        response = requests.post(URL, params=payload, headers=headers)
        result = response.json()
        
        # 检查是否有错误
        if 'error_code' in result:
            return {
                'success': False,
                'error': f"错误代码: {result['error_code']}, 错误信息: {result.get('error_msg', '未知错误')}"
            }
        
        # 提取翻译结果
        if 'trans_result' in result and len(result['trans_result']) > 0:
            translation = result['trans_result'][0]['dst']
            return {
                'success': True,
                'translation': translation
            }
        else:
            return {
                'success': False,
                'error': '翻译结果为空'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'翻译过程中发生错误: {str(e)}'
        }

def make_md5(s, encoding='utf-8'):
    """
    生成MD5签名
    """
    return md5(s.encode(encoding)).hexdigest()