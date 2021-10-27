import os
import requests
import zipfile

def parse_pdf(filename, path_zip='./tmp/img.zip', path_extract='./tmp/img'):
    '''
    对pdf文件进行分析和裁剪
    :param filename: pdf完整路径
    :param path_zip: 下载的zip文件保存目录
    :param path_extract: zip解压目录
    :return: 包含裁剪后的图片的zip后缀压缩包
    '''
    url = 'http://127.0.0.1:9529/parse'
    files = {'file': open(filename, 'rb')}
    response = requests.post(url, files=files)
    try:
        with open(path_zip, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(path_extract):
            os.makedirs(path_extract)
        with zipfile.ZipFile(path_zip) as zf:
            zf.extractall(path_extract)
    except:
        print("解析异常", filename)
    #print("success", filename)

if __name__ == '__main__':
    parse_pdf(r'C:\Users\harvey\Documents\paper\2103.03230.pdf')



