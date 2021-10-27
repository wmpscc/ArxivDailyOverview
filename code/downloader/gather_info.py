import os
import time
import numpy as np
from code.downloader.Composing import parse_pdf
from code.downloader.markdown_model import typing
from code.configs import root_path


def load_detail(path_dir):
    d = np.load(os.path.join(path_dir, 'details.npy'), allow_pickle=True).item()
    title = d['title']
    abs = d['abs']
    url = d['url']
    return title, abs, url


def create_markdown(path_pdf, all_md='', root_dir=None):
    d = path_pdf.split('/')[-2]

    if root_dir is None:
        root_dir = os.path.join(root_path, time.strftime("%Y-%m-%d"))  # today

    if not os.path.isdir(os.path.join(root_dir, d)):
        return
    title, abs, url = load_detail(os.path.join(root_dir, d))
    title_cn = ''
    abs_cn = ''
    if os.path.exists(os.path.join(root_dir, d, "abs.md")):
        md = typing(title, abs, url, title_cn, abs_cn, os.path.join(root_dir, d, 'img'), is_all_typing=True)
        all_md = all_md + md
        return all_md

    parse_pdf(path_pdf, path_zip=os.path.join('./tmp', str(int(time.time())) + '.zip'),
              path_extract=os.path.join(root_dir, d, 'img'))
    md = typing(title, abs, url, title_cn, abs_cn, os.path.join(root_dir, d, 'img'))
    np.savetxt(os.path.join(root_dir, d, "abs.md"), [md], "%s", encoding='utf-8')
    md = typing(title, abs, url, title_cn, abs_cn, os.path.join(root_dir, d, 'img'), is_all_typing=True)
    all_md = all_md + md
    return all_md


if __name__ == '__main__':
    create_markdown()
