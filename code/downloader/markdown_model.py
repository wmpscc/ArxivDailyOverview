import os


def set_detail(summary, content):
    content = content.strip()
    s = f'''
<details>
  <summary>{summary}</summary>
{content}
</details>
    '''
    return s


def set_img(path_img_dir, is_all_typing):
    files = os.listdir(path_img_dir)
    if len(files) == 0:
        return ''
    s = ''
    if is_all_typing:
        prefix = path_img_dir.split('/')[-2] + '/'
    else:
        prefix = ''
    for f in files:
        s = s + f'<img src="./{prefix}img/{f}" align="middle">\n'
    return set_detail('论文截图', s)


def typing(title_en, abs_en, url, title_cn, abs_cn, img_dir, is_all_typing=False):
    if abs_cn != '':
        cn = set_detail("中文摘要", abs_cn)
    else:
        cn = ''
    img = set_img(img_dir, is_all_typing)
    dsc = f'''
### {title_en}
**{title_cn}**

{abs_en}
{cn}
[download]({url})
{img}

    '''
    return dsc
