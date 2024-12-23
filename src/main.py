#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import argparse
import re
import requests
import markdownify
# import multiprocessing
# from lxml import html as lhtml
import html
import math
import natsort

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import warnings
from bs4 import XMLParsedAsHTMLWarning
from datetime import datetime

import concurrent.futures

import networkx as nx
import json
import hashlib

warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

DIR_ARCTICLE = 'article'
DIR_FAVORITES = 'favorites'
DIR_PICTURE = 'picture'
DIR_VIDEO = 'video'
DIR_SINGLES = 'singles'
HABR_TITLE = "https://habr.com"
_HTML_BEGIN_ = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover" />
<meta name=generator content="HabrArticleDownloader" />
<link rel="apple-touch-icon" sizes="180x180" href="js/ico/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="js/ico/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="js/ico/favicon-16x16.png">
<link rel="stylesheet" href="js/habr.css">
<script src="js/habr.js"></script>
<link rel="stylesheet" href="js/highlightjs/stackoverflow-light.min.css">
<script src="js/highlightjs/highlight.min.js"></script>
"""


def callback(el):
    try:
        soup = BeautifulSoup(str(el), features='html.parser')
        return soup.find('code')['class'][0]
    except Exception:
        return None


def imgDownload(url: str, file: str, chdir: str = None):
    """Download single image. file - filename. chdir (optional) - directory for saving file."""
    try:
        img_data = requests.get(url).content
        if chdir:
            filename = os.path.join(chdir, file)
        else:
            filename = file

        with open(filename, 'wb') as handler:
            handler.write(img_data)
    except requests.exceptions.RequestException:
        print("[error]: Ошибка получения картинки: ", url)


def copy_jsdir(dir):
    # скопируем в папку dir файлы js и css если это не было сделано ранее
    ddir = os.path.join(dir, 'js')
    try:
        if not os.path.exists(ddir):
            shutil.copytree(
                os.path.join(os.path.dirname(os.path.realpath(__file__)), 'js'),
                ddir,
                ignore=shutil.ignore_patterns('visjs'),
                dirs_exist_ok=True)
    except OSError:
        print("[error]: Ошибка копирования директории: {}".format(ddir))


def copy_visjs(dir):
    """copy necessary vis.js scripts, css, options, etc."""
    ddir = os.path.join(dir,'js')
    src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'js', 'visjs')
    if not os.path.exists(ddir):
        os.makedirs(ddir)
    try:
        shutil.copytree(src_dir, ddir, dirs_exist_ok=True)
    except shutil.SameFileError:
        pass
    except PermissionError:
        print("[error]: Не хватает прав для копирования библиотеки отображения графов")
    except Exception as e:
        print("[error]: Ошибка копирования библиотеки отображения графов", e)


class HabrArticleDownloader():

    def __init__(self):
        self.dir_author = ''
        self.posts = []
        self.comments = None
        self.dwnl_div = ''
        self._metadata = None

    def dir_cor_name(self, _str):
        for ch in ['#', '%', '&', '{', '}', '\\', '?', '<', '>', '*', '/', '$', '‘', '“', ':', '@', '`', '|']:
            _str = _str.replace(ch, ' ')

        return _str

    def create_dir(self, dir):
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
                if not args.quiet:
                    print("[info]: Директория: {} создана".format(dir))
            except OSError:
                print("[error]: Ошибка создания директории: {}".format(dir))

    def save_md(self, name: str, text: str):
        with open(name + ".md", "w", encoding="UTF-8") as fd:
            fd.write(f'# {name}\n')
            fd.write(text)

    def save_html(self, name: str, text: str):
        orig_title = self._metadata['orig_title'] if 'orig_title' in self._metadata else name
        with open(name + ".html", "w", encoding="UTF-8") as fd:
            fd.write(_HTML_BEGIN_)
            fd.write("<title>" + html.escape(orig_title) + "</title>\n")
            if self._metadata:
                for k, v in self._metadata.items():
                    fd.write('<meta property="hdl_' + html.escape(k) + '" content="' + html.escape(v) + '" />\n')
            fd.write("</head>\n<body>\n\n")
            fd.write(self.dwnl_div + '<div class="tm-page-width">\n<h1 class="tm-title tm-title_h1">' + html.escape(orig_title) + '</h1>')
            fd.write(text)
            fd.write('</div>\n<script>hljs.highlightAll();</script>\n</body></html>')
        copy_jsdir('.')

    def save_comments(self, name: str, text: str):
        lst = text.split('\n')
        lst.reverse()

        with open(name + "_comments.md", "w", encoding="UTF-8") as fd:
            fd.write("\n".join(lst))

    def get_comments(self, url_soup):
        comments = url_soup.findAll('link', {'type': 'application/rss+xml'})

        for c in comments:
            try:
                r = requests.get(c.get('href'))
            except requests.exceptions.RequestException:
                print("[error]: Ошибка получения статьи: ", c.get('href'))
                return

            url_soup = BeautifulSoup(r.text, 'lxml')
            return markdownify.markdownify(str(url_soup), heading_style="ATX", code_language_callback=callback)

    def get_article(self, url, name=None) -> str:
        if not args.quiet and name in (None, 's'):
            print(f"[info]: Скачиваем {url}")
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            print("[error]: Ошибка получения статьи: ", url)
            return

        url_soup = BeautifulSoup(r.text, 'lxml')

        comment = self.get_comments(url_soup) if args.comments else None
        posts = url_soup.findAll('div', {'class': 'tm-article-body'})
        pictures = url_soup.findAll('img')
        video = url_soup.findAll('div', {'class': 'tm-iframe_temp'})

        # одиночное скачивание статьи
        if name is None or 's':
            name = self.dir_cor_name(url_soup.find('h1', 'tm-title tm-title_h1').string)

        text = ''
        self.dwnl_div = ''

        try:
            article_createtime = url_soup.find('span',
                                               {'class': 'tm-article-datetime-published'}).find('time').get('title')
            # article_createtime = article_createtime.replace(",", "", 1)
            article_createtime = article_createtime[:10]
            article_author = url_soup.find('a', {'class': 'tm-user-info__username'}).get('href').split('/')
            self._metadata = {
                'url': url,
                'author': article_author[len(article_author) - 2],
                'author_type': article_author[len(article_author) - 3],
                'author_country_code': article_author[len(article_author) - 4],
                'post_date': article_createtime,
                'article_id': re.search(r'(?:/)(\d+)(?:/?)$', url).group(1)
            }
            meta_cmd = [
            ("orig_title", "url_soup.find('h1', 'tm-title tm-title_h1').string"),
            ("origin_src_url", "url_soup.find('a', 'tm-article-presenter__origin-link').get('href')"),
            ("company_name", "url_soup.find('div', 'tm-company-snippet').find('a', 'tm-company-snippet__title').string"),
            ("company_profile_url", "url_soup.find('div', 'tm-company-snippet').find('a', 'tm-company-snippet__title').get('href')"),
            ("company_site", "url_soup.find('dd', 'tm-description-list__body').find('a', 'tm-company-basic-info__link').text"),
            ("company_site_url", "url_soup.find('dd', 'tm-description-list__body').find('a', 'tm-company-basic-info__link').get('href')"),
            ("company_location", "url_soup.find('dt', 'tm-description-list__title', string='Местоположение').find_next_siblings('dd').string")]
            for meta in meta_cmd:
                try:
                    self._metadata[meta[0]] = eval(meta[1])
                except Exception:
                    pass

            if 'orig_title' not in self._metadata:
                self._metadata['orig_title'] = name
            if 'company_name' in self._metadata:
                self._metadata['is_company_blog'] = '1'
            # self._metadata = {k: v for k, v in self._metadata.items() if v is not None}

            if not args.no_meta_information:
                user_url = HABR_TITLE + '/' + '/'.join([
                    self._metadata['author_country_code'],
                    self._metadata['author_type'],
                    self._metadata['author']
                ]) + '/'
                self.dwnl_div = f"\n<div class='dl-info-cnt'>\
                <div class='dl-info' data-article-id='{self._metadata['article_id']}' data-title-first-c='{name[0]}'><dl>\n\
                <dt>Url</dt><dd><a href='{url}'>{url}</a></dd>\n\
                <dt>Автор</dt><dd><a class='author' href='{user_url}'>{html.escape(self._metadata['author'])}</a></dd>\n\
                <dt>Дата</dt><dd><time datetime='{article_createtime}'>{article_createtime}</time></dd>"
                if 'company_profile_url' in self._metadata and 'company_name' in self._metadata:
                    self.dwnl_div += f'<dt>Компания</dt><dd><a class="company_name" href="{self._metadata["company_profile_url"]}">' + html.escape(self._metadata['company_name']) + '</a></dd>\n'
                elif 'company_name' in self._metadata:
                    self.dwnl_div += '<dt>Компания</dt><dd><span class="company_name">' + html.escape(self._metadata['company_name']) + '</span></dd>\n'
                self.dwnl_div += "</dl></div></div>\n"
        except Exception:
            print("[error]: Ошибка получения метаданных статьи: ", url)

        # заменим абсолютные ссылки на разделы в тексте (#) на относительные
        a_re = re.compile(r'/(#[^/]+)$')
        for post in posts:
            for a in post.findAll('a', href=a_re):
                link = a.get('href')
                a['href'] = a['href'].replace(link, re.search(a_re, link).group(1))

        for post in posts:
            if args.local_pictures:
                pictures_names = post.findAll('img')
                for link in pictures_names:
                    link = link.get('src')
                    filename = 'picture/' + link.split('/')[len(link.split('/')) - 1]
                    post = str(post).replace(str(link), str(filename))

            text += str(post)

        text_md = markdownify.markdownify(text, heading_style="ATX", code_language_callback=callback)
        # text_html = text.replace("<pre><code class=", "<source lang=").replace("</code></pre>", "</source>")
        text_html = f'\
            <div class="tm-article-presenter__origin">Перевод: \
            <a class="tm-article-presenter__origin-link" href="{self._metadata["origin_src_url"]}" target="_blank">оригинал текста</a>\
            </div>\n\n' if 'origin_src_url' in self._metadata else ''
        text_html += text

        # создаем дирректорию под картинки
        self.create_dir(DIR_PICTURE)
        os.chdir(DIR_PICTURE)
        self.save_pictures(pictures)
        os.chdir('../')

        if video != []:
            # создаем дирректорию под видео
            self.create_dir(DIR_VIDEO)
            os.chdir(DIR_VIDEO)
            self.save_video(video, name)
            os.chdir('../')

        self.save_html(name, text_html)
        self.save_md(name, text_md)
        if args.comments:
            self.save_comments(name, str(comment))

        if not args.quiet:
            print(f'[info]: Статья "{name}" сохранена')
        return name

    def save_pictures(self, pictures):
        with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
            mp_tasks = dict()
            for link in pictures:
                # для svg (формулы LaTeX) и др. data-src не проставлен
                link_url = link.get('data-src') or link.get('src')
                if link_url:
                    link_dst = os.path.basename(urlparse(link_url).path)
                    # если картинка уже создана, то второй раз не скачиваем
                    if os.path.exists(link_dst):
                        continue

                    mp_tasks.update({link_dst: executor.submit(imgDownload, link_url, link_dst)})
            while True:
                tsk_status = concurrent.futures.wait(mp_tasks.values(), timeout=2)
                if 0 == len(tsk_status.not_done):
                    break
                print("Ожидание %i изображений  \r" % len(tsk_status.not_done), end='')

    def save_video(self, video, article_name):
        with open('video.txt', 'w+', encoding='UTF-8') as f:
            for link in video:
                if link.get('data-src'):
                    print(link.get('data-src'), ' | ', article_name, file=f)

    def define_numer_of_pages(self, url, type_articles):
        """type_aticles: ['publications', 'bookmarks', 's', 'followers']"""
        r = requests.get(url)
        url_soup = BeautifulSoup(r.text, 'lxml')
        spans = url_soup.find_all("span", {"class": "tm-tabs__tab-item"})
        
        if type_articles == 'publications':
            span = spans[1]
        elif type_articles == 'bookmarks':
            span = spans[3]
        elif type_articles == 's':
            span = spans[1]
        
        span = span.find('span')
        span_value = re.sub(r'[^0-9]', '', span.text) if span else 0
        number_of_pages = math.ceil(int(span_value)/20)
        return number_of_pages

    def getAuthorFullInfo(self, nickname: str):
        """Scan profile and return full info dict with own publications details and favorites details"""
        _baseurl = '/'.join([HABR_TITLE, 'ru', 'users', nickname])
        pub_url = _baseurl + '/publications/articles/'
        fav_url = _baseurl + '/bookmarks/articles/'
        # follow_url = _baseurl + '/followers/'
        _info = {'publications': [], 'bookmarks': []}
        # own publications
        _info['publications'] = self.userProfileArticleSubScan(pub_url, 'publications')
        _info['bookmarks'] = self.userProfileArticleSubScan(fav_url, 'bookmarks')
        return _info

    def userProfileArticleSubScan(self, scan_url: str, page_type: str):
        """helper function to find article snippets on given user profile tab"""
        _ret = []
        num_pages = self.define_numer_of_pages(scan_url, page_type)
        for page in range(1, num_pages + 1):
            page_url = scan_url + ("page" + str(page) if page > 1 else '')
            try:
                r = requests.get(page_url)
            except requests.exceptions.RequestException:
                print(f"[error]: Ошибка получения страницы из списка статей: {page_url}")
                continue
            url_soup = BeautifulSoup(r.text, 'lxml')
            snipppets = url_soup.find('div', {'class': 'tm-articles-list'}).findAll('article', {'class': 'tm-articles-list__item'})
            _ret += self.parseArticleSnippets(snipppets)
        return _ret

    def parseArticleSnippets(self, bs):
        """Parse array of BeautifulSoup <article> elements and return dict with article id, title and author"""
        _ret = []
        for art in bs:
            snip = art
            # если сниппет пустой - мы в рекламной вставке на новость компании. Пропускаем
            if art.find('div', class_='tm-article-snippet') is None:
                continue
            info = {'id': art['id']}
            info.update({
                'author': snip.find('div', class_='tm-article-snippet__meta-container').find('a', class_='tm-user-info__username').text.strip()
            })
            info.update({
                'date': snip.find('div', class_='tm-article-snippet__meta-container').find('time').get('datetime')[:10]
            })
            info.update({
                'url': snip.find('a', class_='tm-title__link').get('href')
            })
            info.update({
                'title': snip.find('a', class_='tm-title__link').find('span').text.strip()
            })
            info.update({
                'titleMD5': hashlib.md5(info['title'].encode("utf-8")).hexdigest()
            })
            info.update({
                'bookmarked_count': int(snip.find('span', class_='bookmarks-button__counter').text)
            })
            if info['url'].startswith('/ru/'):
                info['url'] = HABR_TITLE + info['url']
            # hub_link = snip.findAll('a', class_='tm-publication-hub__link')
            # for ln in hub_link:
            #     if ln.find('span') and ln.find('span').text.startswith('Блог компании '):
            #         info['companyBlog'] = ln.find('span').text[14:]

            _ret += [info]
        return _ret

    def main(self, nickname, dir, type_articles):
        # создаем папку для статей
        self.create_dir(dir)
        os.chdir(dir)

        profile = self.getAuthorFullInfo(nickname)
        if type_articles == 'u':
            pubs = profile['publications']
        else:
            pubs = profile['bookmarks']
        # создаем папку с именем автора, если есть публикации
        if len(pubs):
            self.create_dir(nickname)
            os.chdir(nickname)
            for art_index, art in enumerate(pubs, start=1):
                print(f"[info]: Статья ({art_index}/{len(pubs)}) {art['title']}")
                try:
                    self.get_article(art['url'], art['title'])
                except Exception:
                    print(f"[error]: Ошибка обработки {art['url']}")
            os.chdir('../')

        print("[info]: Построение графа связей")
        _graph_file = os.path.join('graph', 'graph.json')
        try:
            if os.path.exists(_graph_file):
                with open(_graph_file) as json_data:
                    G = nx.node_link_graph(json.load(json_data), edges="edges", source="from", target="to")
            else:
                G = nx.DiGraph()
        except Exception as e:
            print(f"[error]: Ошибка чтения ранее сохраненного графа {_graph_file}")
            print(e)
            G = nx.DiGraph()
        # удаляем закладки на самого себя, чтоб избежать петель в графе
        profile['bookmarks'] = [x for x in profile['bookmarks'] if x['author'] != nickname]
        G.add_nodes_from([(x['author'], {'label':x['author'], 'group': 'author'}) for x in profile['bookmarks']])
        G.add_nodes_from([(x['titleMD5'], {
            'title': x['title'], 'author': x['author'], 'article_id': x['id'],
            'localName': (nickname + '/' + self.dir_cor_name(x['title']) + '.html') if type_articles == 'b' else None,
            'group': 'post', 'shape': 'circle', 'size': 1,
            'url': x['url'], 'bookmarked_count': x['bookmarked_count'],
            'pubdate': x['date']
        }) for x in profile['bookmarks']])
        G.add_node(
            nickname,
            label=nickname, group='author',
            title=f'Публикаций:{len(profile["publications"])}<br/>Закладок:{len(profile["bookmarks"])}')
        # G.add_edges_from( [(nickname,x['author']) for x in profile['bookmarks']] )
        G.add_edges_from([(nickname, x['titleMD5'], {'relation': 'bookmark', 'title': 'закладка'}) for x in profile['bookmarks']])
        G.add_edges_from([(x['titleMD5'], x['author'], {'relation': 'post_author', 'color': {'inherit': True}}) for x in profile['bookmarks']])
        self.create_dir('graph')
        self.create_dir(os.path.join('graph', 'js'))
        # nx.write_adjlist(G, os.path.join('graph', 'test.adjlist'))
        gdata = nx.node_link_data(G, edges="edges", source="from", target="to")
        with open(_graph_file, "w", encoding="UTF-8") as fd:
            fd.write(json.dumps(gdata))
        with open(os.path.join('graph', 'js', 'graph_data.js'), "w", encoding="UTF-8") as fd:
            fd.write('"use strict";\n\n')
            fd.write('var graph_json = ' + json.dumps(gdata))
        with open(os.path.join('graph', 'index.html'), "w", encoding="UTF-8") as fd:
            fd.write("""<!doctype html>
<HTML>
<HEAD>
  <meta charset="utf-8" />
  <TITLE>Граф связей</TITLE>
  <script type="text/javascript" src="js/vis.min.js"></script>
  <script type="text/javascript" src="js/graph_data.js"></script>
  <script type="text/javascript" src="js/graph.js"></script>
  <link rel="stylesheet" type="text/css" href="js/vis.min.css">
  <link rel="stylesheet" type="text/css" href="js/graph.css">
  <style type="text/css">
    #mynetwork {width: 100%; height: 600px; border: 2px solid lightgray; background: #fff;}
    </style>
</HEAD>
<BODY>
<div id="mynetwork-cnt" class="mynetwork_cnt">
  <div id="netprogress" class="progressbar_cnt"><div class="progressbar"></div></div>
  <div id="mynetwork"></div>
</div>

<div class="network-info-cnt">

    <div class="ni-pane srch-pane">
      <div class="index_srch_cnt">
        <input type="text" placeholder="Найти автора.." pattern="s+" id="srch-author" >
      </div>
      <div class="srch-results-cnt ni-bump-pane"><div id="author-srch-res" class="srch-results"></div></div>
    </div>
    <div class="ni-pane sel-info-pane">
      <div id="graph-stngs" class="graph-stngs-cnt ni-bump-pane"></div>
      <div id="selnodeinfo" class="ni-bump-pane"></div>
    </div>

</div>
</BODY>
</HTML>""")
        copy_visjs(os.path.join('.', 'graph'))


class IndexBuilder():

    def __init__(self):
        self._articles = []

    def fileMetadata(self, file):
        """Return article metadata dict from HTML file <meta> tags"""
        soup = BeautifulSoup(open(file, encoding="utf8"), 'lxml')
        metadata = [
            (x, soup.find('meta', {'property': str('hdl_' + x)}))
            for x in ['author', 'url', 'post_date', 'author_country_code', 'author_type', 'orig_title', 'origin_src_url',
                'company_name', 'company_profile_url', 'company_site', 'company_site_url', 'is_company_blog']]
        metadata = [(x, v.attrs['content']) for x, v in metadata if v]
        metadata = metadata + [('file', os.path.basename(file)), ('title', soup.find('title').string)]
        metadata = dict(metadata)
        if 'orig_title' not in metadata or not metadata['orig_title']:
            metadata['orig_title'] = os.path.basename(file)[:-5]
        if 'author' not in metadata or not metadata['author']:
            metadata['author'] = 'неизв.'
        return metadata

    def authorsInDir(self, dirpath='.'):
        a_list = [
            os.path.join(dirpath,f) for f in natsort.os_sorted(os.listdir(dirpath))
                if os.path.isdir(os.path.join(dirpath, f)) and f != 'js' and f != 'graph'
        ]
        return [os.path.basename(p) for p in a_list]

    def articlesInDir(self, dirpath='.'):
        """List of article HTML-files in dirpath. Return's array of 'dirpath/file.html'"""
        return [
            os.path.join(dirpath,f) for f in natsort.os_sorted(os.listdir(dirpath))
                if os.path.isfile(os.path.join(dirpath,f)) and f.endswith('.html') and f.lower() != 'index.html'
        ]

    def articlesMetaInDir(self, dirpath='.'):
        """Scan folder and return array of dictionary of metadata for each HTML file"""
        src_articles = self.articlesInDir(dirpath)
        _articles = []
        for file in src_articles:
            _articles.append(self.fileMetadata(file))
        return _articles

    def make_index(self, dirpath='.', with_authors_list=True):
        self._articles = self.articlesMetaInDir(dirpath)
        with open(os.path.join(dirpath, "index.html"), "w", encoding="UTF-8") as fd:
            fd.write(_HTML_BEGIN_)
            fd.write('</head><body>\n\n')
            fd.write('<div class="art_index_cnt"><p class="art_index_h1">Перечень статей:</p>\n')

            if with_authors_list:
                fd.write('<div class="index_spoiler index_spoiler_open" role="button" tabindex="0"><span class="index_spoiler_title">По алфавиту:</span>\n<div class="index_spoiler_txt">\n')
            self._ul_article(fd, self._articles)
            if with_authors_list:
                fd.write('</div></div>\n')

            # список авторов статей
            authors = natsort.natsorted(set(x['author'] for x in self._articles))
            if with_authors_list and len(authors) > 1:
                fd.write('<p class="art_index_h1">Перечень авторов:</p>')
                fd.write('<div>')
                fd.write('<div class="index_author_srch_cnt"></div>\n')
                fd.write('<ul class="author_list">\n')
                for a in authors:
                    arts = [x for x in self._articles if x['author'] == a]
                    fd.write('<li><div class="index_spoiler" role="button" tabindex="0">\
                        <span class="index_spoiler_title"><span class="author">' + html.escape(a) + '</span>' +
                        ('&nbsp;<span class="company_name">' + html.escape(arts[0]['company_name']) + '</span>' if 'company_name' in arts[0] else '')+
                        '</span><div class="index_spoiler_txt">')
                    self._ul_article(fd, arts)
                    fd.write('</div></div></li>\n')
                fd.write('</ul>\n')
                fd.write('</div>')

            fd.write('</div>\n<div class="art_index_end"></div>\n</body></html>')

    def _ul_article(self, fd, articles, dirpath_prefix='.', add_search_box=True):
        """Write into file descriptor fd <ul>...</ul> block for provided list of articles"""
        _articles = articles
        _path_prefix = dirpath_prefix
        if _path_prefix not in ['.', '', None]:
            if os.name == 'nt':
                _path_prefix = _path_prefix.replace('\\', '/')
            _path_prefix = _path_prefix + '/' if _path_prefix[-1] != '/' else _path_prefix
        else:
            _path_prefix = ''
        if add_search_box and len(_articles) > 10:
            fd.write('<div class="index_article_srch_cnt"></div>\n')
        fd.write('\n<div class="art_index_ul_cnt"><div class="art_index_ul_before"></div><ul class="art_index">')
        for art in _articles:
            isTrans = 'origin_src_url' in art
            fd.write(f"\n <li><span class='{('art_translation' if isTrans else '')}'>")
            fd.write(f"<a class='article_link' href='{_path_prefix + art['file']}'" + (" title='Статья-перевод'" if isTrans else "") + ">")
            fd.write(html.escape(art['orig_title']) + "</a></span>")
            a = ['&nbsp;<span class="' + x + '">' + html.escape(art[x]) + 
                '</span>' if x in art else '&nbsp;<span class="missing ' + x + '">&mdash;</span>'
                for x in ['author', 'post_date'] ]
            for tg in a:
                fd.write(tg)
            fd.write('\n </li>')
        fd.write('\n</ul><div class="art_index_ul_after"></div></div>\n')

    def indexAuthor(self, dirpath):
        self.make_index(dirpath=dirpath, with_authors_list=False)

    def indexSingles(self, dirpath='.'):
        self.make_index(dirpath=dirpath, with_authors_list=True)

    def indexCatalogue(self, dirpath='.'):
        """Top-level index.html for -u and -b run args"""
        a_list = natsort.natsorted(self.authorsInDir(dirpath))
        print("[info]: Построение индексов для %i каталогов авторов" % len(a_list))
        a_meta = {}
        for author in a_list:
            a_file = self.articlesInDir(dirpath=os.path.join(dirpath, author))
            if a_file and len(a_file):
                a_meta.update({author: self.fileMetadata(a_file[0])})
                a_meta[author]['article_count'] = len(a_file)
            self.make_index(dirpath=author, with_authors_list=False)
        with open(os.path.join(dirpath, "index.html"), "w", encoding="UTF-8") as fd:
            fd.write(_HTML_BEGIN_)
            fd.write('</head><body>\n\n')
            if os.path.exists(os.path.join('graph', 'index.html')):
                fd.write('<div class="graph_link"><a href="graph/index.html" target="_blank">Открыть граф связей</a></div>\n')
            fd.write('<div class="art_index_cnt authorsCatalogue"><p class="art_index_h1">Перечень авторов и количества статей:</p>\n')

            fd.write('<div class="index_author_srch_cnt"></div>\n')
            fd.write('<ul class="author_list authorsCatalogue">\n')
            for a in a_list:
                if a in a_meta and 'company_name' in a_meta[a]:
                    company_name = '<span class="company_name">' + html.escape(a_meta[a]['company_name']) + '</span>'
                    art_count = "(" + str(a_meta[a]['article_count']) + ")" 
                else:
                    company_name = ''
                    art_count = "(" + str(a_meta[a]['article_count']) + ")" 
                fd.write(f'  <li><a class="author" href="{a}/index.html">{html.escape(a)}</a>{art_count}&nbsp;{company_name}</li>\n')
            fd.write('</ul>\n')

            fd.write('</div>\n<div class="art_index_end"></div>\n</body></html>')
            copy_jsdir('.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Скрипт для скачивания статей с https://habr.com/")
    parser.add_argument('-q', '--quiet', help="Quiet mode", action='store_true')
    parser.add_argument('-c', '--comments', help="Создать файл с коментариями к статье", action='store_true')
    parser.add_argument('-l', '--local-pictures',
                        help="Cкачать все картинки локально и использовать абсолютный путь к изображениям", action='store_true')
    parser.add_argument('--no-meta-information', help="Не добавить мета-информацию о статье на экран", action='store_true')
    parser.add_argument('--no-index', help="Не создавать файл index.html", action='store_true')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--user-publications', help="Скачать статьи пользователя", type=str, dest='user_name_for_articles')
    group.add_argument('-b', '--user-bookmarks', help="Скачать закладки пользователя", type=str, dest='user_name_for_bookmarks')
    group.add_argument('-s', help="Скачать одиночные статьи (список ID через запятую)", type=str, dest='article_id')

    args = parser.parse_args()

    type_articles = None

    if args.user_name_for_articles:
        nickname = args.user_name_for_articles
        output = DIR_ARCTICLE
        type_articles = 'u'
    elif args.user_name_for_bookmarks:
        nickname = args.user_name_for_bookmarks
        output = DIR_FAVORITES
        type_articles = 'b'
    else:
        type_articles = 's'
        output = DIR_SINGLES

    habrSD = HabrArticleDownloader()
    start_time = datetime.now()
    try:
        if not args.article_id:
            habrSD.main(nickname, output, type_articles)
            if not args.no_index:
                index = IndexBuilder()
                # index.indexAuthor(args.user_name_for_articles)
                index.indexCatalogue()
        else:
            if not os.path.exists(DIR_SINGLES):
                try:
                    os.makedirs(DIR_SINGLES)
                    if not args.quiet:
                        print("[info]: Директория: {} создана".format(DIR_SINGLES))
                except OSError:
                    print("[error]: Ошибка создания директории: {}".format(DIR_SINGLES))
                    raise SystemExit
            os.chdir(DIR_SINGLES)
            for ar_id in args.article_id.split(','):
                habrSD.get_article("https://habr.com/ru/post/" + ar_id, type_articles)
            try:
                if not args.no_index:
                    index = IndexBuilder()
                    # index.make_index()
                    index.indexSingles()
            except Exception as ex:
                print("[error]: Ошибка создания файла index.html")
                print(ex)
    except Exception:
        import traceback
        print("[error]: Ошибка получения данных")
        print(traceback.format_exc())
    end_time = datetime.now()
    print('Затраченное время: {}'.format(end_time - start_time))
