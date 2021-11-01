import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
import os
import random
import numpy as np
from tqdm import tqdm
from code.tools.multi_download import download
import multiprocessing as mp
from code.downloader.gather_info import create_markdown  # AOverview
import glob
from code.configs import proxy, root_path
from code.tools.zip_tools import zip_ya

if not os.path.isdir(root_path): os.makedirs(root_path)


def get_one_page(url):
    response = requests.get(url, proxies=proxy, verify=False)

    while response.status_code == 403:
        time.sleep(500 + random.uniform(0, 500))
        response = requests.get(url)
    if response.status_code == 200:
        return response.text

    return None


def get_paper_list():
    url = 'https://arxiv.org/list/cs/pastweek?show=1000'
    html = get_one_page(url)
    soup = BeautifulSoup(html, features='html.parser')
    all_day = soup.find_all('dl')
    print("last day")
    content = all_day[1]
    list_ids = content.find_all('a', title='Abstract')
    list_title = content.find_all('div', class_='list-title mathjax')
    list_authors = content.find_all('div', class_='list-authors')
    list_subjects = content.find_all('div', class_='list-subjects')
    list_subject_split = []
    for subjects in list_subjects:
        subjects = subjects.text.split(': ', maxsplit=1)[1]
        subjects = subjects.replace('\n\n', '')
        subjects = subjects.replace('\n', '')
        subject_split = subjects.split('; ')
        list_subject_split.append(subject_split)
    items = []
    for i, paper in enumerate(zip(list_ids, list_title, list_authors, list_subjects, list_subject_split)):
        items.append([paper[0].text, paper[1].text, paper[2].text, paper[3].text, paper[4]])

    print("today")
    content = all_day[0]
    list_ids = content.find_all('a', title='Abstract')
    list_title = content.find_all('div', class_='list-title mathjax')
    list_authors = content.find_all('div', class_='list-authors')
    list_subjects = content.find_all('div', class_='list-subjects')
    list_subject_split = []
    for subjects in list_subjects:
        subjects = subjects.text.split(': ', maxsplit=1)[1]
        subjects = subjects.replace('\n\n', '')
        subjects = subjects.replace('\n', '')
        subject_split = subjects.split('; ')
        list_subject_split.append(subject_split)
    for i, paper in enumerate(zip(list_ids, list_title, list_authors, list_subjects, list_subject_split)):
        items.append([paper[0].text, paper[1].text, paper[2].text, paper[3].text, paper[4]])

    name = ['id', 'title', 'authors', 'subjects', 'subject_split']
    paper = pd.DataFrame(columns=name, data=items)

    save_dir = os.path.join(root_path, time.strftime("%Y-%m-%d"))
    if not os.path.isdir(save_dir): os.makedirs(save_dir)
    paper.to_csv(os.path.join(save_dir, time.strftime("%Y-%m-%d") + '.csv'))


def get_abstract(arxiv_id='2101.12159'):
    html = get_one_page("https://arxiv.org/abs/" + arxiv_id)
    soup = BeautifulSoup(html, features='html.parser')
    titles = soup.find_all('h1', class_='title mathjax')
    title = titles[0].text
    abstracts = soup.find_all('blockquote', class_='abstract mathjax')
    abs = abstracts[0].text
    abs = abs.replace('-\n', '')  # 连接换行单词
    abs = abs.replace('\n', " ")  # 删除换行
    return title, abs


def save_markdown(save_dir, title, abs, url):
    detail = {}
    detail['title'] = title
    detail['abs'] = abs
    detail['url'] = url
    np.save(os.path.join(save_dir, "details.npy"), detail)

    # np.savetxt(os.path.join(save_dir, "abs.md"), [ss], "%s")
    print("write abs txt finish")


def list_all_paper():
    dirs = os.listdir(root_path)
    total_paper = []
    for d in dirs:
        path = os.path.join(root_path, d)
        files = os.listdir(path)
        total_paper = total_paper + files

    return total_paper


def check_is_exists(arxiv_id):
    if arxiv_id in exist_papers:
        return True
    else:
        return False


def download_paper(arxiv_id='2101.12159', paper_title=''):
    # if check_is_exists(arxiv_id): # 过去曾经下载
    #     return None
    selected_paper_id = arxiv_id.replace(".", "_")
    pdfname = paper_title.replace("/", "_")  # pdf名中不能出现/和：
    pdfname = pdfname.replace("?", "_")
    pdfname = pdfname.replace("\"", "_")
    pdfname = pdfname.replace("*", "_")
    pdfname = pdfname.replace(":", "_")
    pdfname = pdfname.replace("\n", "")
    pdfname = pdfname.replace("\r", "")
    pdfname = pdfname.replace("\\", "")
    pdfname = pdfname.replace("  ", " ")
    # print(time.strftime("%Y-%m-%d") + '/%s %s.pdf' % (selected_paper_id, paper_title))
    if len(pdfname) > 130:
        pdfname = pdfname[:100]
    save_dir = os.path.join(root_path, time.strftime("%Y-%m-%d"), arxiv_id)
    if not os.path.isdir(save_dir): os.makedirs(save_dir)
    save_path = os.path.join(save_dir, arxiv_id + "_" + pdfname + ".pdf")
    if os.path.exists(save_path):  # 存在则跳过
        return save_path
    try:
        download('https://arxiv.org/pdf/' + arxiv_id + ".pdf", save_path)
    except:
        os.removedirs(save_dir)
        raise RuntimeWarning('download error!')
    # 处理文本
    title, abs = get_abstract(arxiv_id)
    print(arxiv_id)
    save_markdown(save_dir, title, abs, 'https://arxiv.org/pdf/' + arxiv_id)
    print("finish download")
    return save_path


def get_daily_paper(key_words, subject_words, files):
    if not (len(key_words) > 0 and len(subject_words) > 0):
        print('请输入关键词')
        return None
    global exist_papers
    exist_papers = list_all_paper()
    path_daily_paper = os.path.join(root_path, time.strftime("%Y-%m-%d"), time.strftime("%Y-%m-%d") + '.csv')
    if not os.path.exists(path_daily_paper):
        print('update paper list begining')
        get_paper_list()
        print('update paper list finish')
    paper = pd.read_csv(path_daily_paper)
    selected_papers = paper[paper['title'].str.contains(key_words[0], case=False)]
    for key_word in key_words[1:]:
        selected_paper1 = paper[paper['title'].str.contains(key_word, case=False)]
        selected_papers = pd.concat([selected_papers, selected_paper1], axis=0)
    selected_papers.drop_duplicates(inplace=True)
    selected_subject_papers = selected_papers[
        selected_papers['subject_split'].str.contains(subject_words[0], case=False)]
    for key_word in subject_words[1:]:
        selected_paper1 = selected_papers[selected_papers['subject_split'].str.contains(key_word, case=False)]
        selected_subject_papers = pd.concat([selected_subject_papers, selected_paper1], axis=0)
    selected_subject_papers.drop_duplicates()

    for i, t in zip(selected_subject_papers['id'], tqdm(selected_subject_papers['title'])):
        id = i.split(':', maxsplit=1)[1]
        title = t.split(':', maxsplit=1)[1]
        print("process  ", id)
        try:
            save_path = download_paper(id, title)
            files.put(save_path)
            print('finish   ', id)
        except:
            print('cannot download', id)
    files.put("finish")
    print("put finish")


def finish(needPDF, needZip):
    if not needPDF:
        pdf = glob.glob(os.path.join(root_path, '*', '*', '*.pdf'))
        for p in pdf:
            print(p)
            os.remove(p)
    if needZip:
        zip_ya(root_path)


def process_context(files, share_dict, needPDF, needZip):
    while True:
        if not files.empty():
            path_pdf = files.get()
            if path_pdf is not None:
                if path_pdf == 'finish':
                    np.savetxt(os.path.join(root_path, time.strftime("%Y-%m-%d"), "README.md"), [share_dict['all_md']],
                               "%s", encoding='utf-8')
                    finish(needPDF, needZip)
                    break
                try:
                    all_md = create_markdown(path_pdf, share_dict['all_md'])
                    share_dict['all_md'] = all_md
                except:
                    print("except =====>>>>>", path_pdf)
                    files.put(path_pdf)
                    time.sleep(1)

        else:
            time.sleep(1)
    share_dict['break'] = 'true'


def start_parse(key_words, subject_words, needPDF=True, needZip=True):
    with mp.Manager() as mg:
        files = mp.Queue(30)
        share_dict = mp.Manager().dict()
        share_dict['all_md'] = ''
        share_dict['break'] = 'false'

        p1 = mp.Process(target=process_context, args=(files, share_dict, needPDF, needZip))
        p1.start()
        get_daily_paper(key_words, subject_words, files)

    while True:
        if not share_dict['break'] == 'true':
            time.sleep(10)
