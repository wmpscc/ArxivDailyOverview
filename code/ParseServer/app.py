import sys

sys.path.append('./code')
import time
from flask import *
import os
from flask_cors import CORS
from model_control import std_parse_doc as spd
import zipfile

app = Flask(__name__)
cors = CORS(app)


def zip_ya(start_dir):
    start_dir = start_dir  # 要压缩的文件夹路径
    file_news = start_dir + '.zip'  # 压缩后文件夹的名字

    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(start_dir):
        f_path = dir_path.replace(start_dir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
        f_path = f_path and f_path + os.sep or ''  # 实现当前文件夹以及包含的所有文件的压缩
        for filename in file_names:
            z.write(os.path.join(dir_path, filename), f_path + filename)
    z.close()
    return file_news


@app.route('/parse', methods=['GET', 'POST'])
def get_crop_file():
    if request.method == 'POST':
        f = request.files.get('file')
        path = os.path.join('./tmp/upload', f.filename)
        f.save(path)
        tmp_save_dir = os.path.join('./tmp/download', str(int(time.time())))
        pil_images = spd.convert_pdf2img(path)
        for page_num, img in enumerate(pil_images):
            if page_num > 20:  # 只要前20页
                break
            spd.parse_page(img, page_num, save_dir=tmp_save_dir)

        path_zip = zip_ya(os.path.abspath(tmp_save_dir))

    return send_file(path_zip, as_attachment=True)


@app.route('/online', methods=['GET', 'POST'])
def check_online():
    return 'ok'


if __name__ == '__main__':
    files = [
        './tmp/upload',
        './tmp/download',
    ]
    for ff in files:
        if not os.path.exists(ff):
            os.makedirs(ff)
    app.run(debug=False, host='0.0.0.0', port=9529)
