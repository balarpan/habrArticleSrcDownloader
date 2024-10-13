#!/usr/bin/python3
#-*- coding: utf-8 -*-

import os
import shutil
import argparse
import re
import pymp
import requests
import markdownify
import multiprocessing
# from lxml import html as lhtml
import html
import math
import natsort

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

DIR_ARCTICLE = 'article'
DIR_FAVORITES = 'favorites'
DIR_PICTURE = 'picture'
DIR_VIDEO = 'video'
DIR_SINGLES = 'singles'
HABR_TITLE = "https://habr.com"


def callback(el):
    try:
        soup = BeautifulSoup(str(el), features='html.parser')
        return soup.find('code')['class'][0]
    except:
        return None

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

    def copy_jsdir(self, dir):
        # скопируем в папку dir файлы js и css если это не было сделано ранее
        ddir = os.path.join(dir,'js')
        try:
            if not os.path.exists(ddir):
                shutil.copytree(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'js'),
                    ddir,
                    dirs_exist_ok=True)
        except OSError:
            print("[error]: Ошибка копирования директории: {}".format(ddir))

    def save_md(self, name: str, text: str):
        with open(name + ".md", "w", encoding="UTF-8") as fd:
            fd.write(f'# {name}\n')
            fd.write(text)

    def save_html(self, name: str, text: str):
        orig_title = self._metadata['orig_title']
        with open(name + ".html", "w", encoding="UTF-8") as fd:
            fd.write("<!DOCTYPE html><html><head>\n<title>" + 
                html.escape(orig_title) + "</title>\n")
            fd.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
            fd.write('<meta charset="UTF-8" />\n<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover" />\n')
            fd.write('<meta name=generator content="HabrArticleDownloader" />\n')
            if self._metadata:
                for k,v in self._metadata.items():
                    fd.write('<meta property="hdl_' + html.escape(k) + '" content="' + html.escape(v) + '" />\n')
            fd.write('<link rel="stylesheet" href="js/habr.css">\n')
            fd.write('<script src="js/habr.js"></script>\n')
            fd.write('<link rel="stylesheet" href="js/highlightjs/stackoverflow-light.min.css">\n')
            fd.write('<script src="js/highlightjs/highlight.min.js"></script>\n</head>\n<body>\n\n')
            fd.write(self.dwnl_div + '<div class="tm-page-width">\n<h1 class="tm-title tm-title_h1">' + html.escape(orig_title) +'</h1>')
            fd.write(text)
            fd.write('</div>\n<script>hljs.highlightAll();</script>\n</body></html>')
        self.copy_jsdir('.')

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
        if not args.quiet:
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
                                               {'class': 'tm-article-datetime-published'}).find('time').get('title') or ''
            # article_createtime = article_createtime.replace(",", "", 1)
            article_createtime = article_createtime[:10]
            article_author = url_soup.find('a', {'class': 'tm-user-info__username'}).get('href').split('/') or []
            self._metadata = {
                'url': url,
                'author': article_author[len(article_author) - 2],
                'author_type': article_author[len(article_author) - 3],
                'author_country_code': article_author[len(article_author) - 4],
                'post_date': article_createtime,
                'orig_title': url_soup.find('h1', 'tm-title tm-title_h1').string or name,
                'origin_src_url': url_soup.find('a', 'tm-article-presenter__origin-link').get('href') if url_soup.find('a', 'tm-article-presenter__origin-link') else None
                }
            self._metadata = {k: v for k, v in self._metadata.items() if v is not None}
            if not args.no_meta_information:
                user_url = 'https://habr.com/' + '/'.join([
                    self._metadata['author_country_code'],
                    self._metadata['author_type'],
                    self._metadata['author']
                    ]) + '/'
                self.dwnl_div = f"\n<div class='dl-info'><dl>\
                <dt>Url</dt><dd><a href='{url}'>{url}</a></dd>\n\
                <dt>Автор</dt><dd><a class='author' href='{user_url}'>{self._metadata['author']}</a></dd>\n\
                <dt>Дата</dt><dd><time datetime='{article_createtime}'>{article_createtime}</time><//dd>\n\
                </dl></div>\n"
        except:
            print("[error]: Ошибка получения метаданных статьи: ", url)

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
            print(f"[info]: Статья: {name} сохранена")
        return name

    def save_pictures(self, pictures):
        for link in pictures:
            # для svg (формулы LaTeX) и др. data-src не проставлен
            link_url = link.get('data-src') or link.get('src')
            if link_url:
                link_dst = os.path.basename(urlparse(link_url).path)
                # если картинка уже создана, то второй раз не скачиваем
                if os.path.exists(link_dst):
                    continue
                try:
                    img_data = requests.get(link_url).content
                    with open(link_dst, 'wb') as handler:
                        handler.write(img_data)
                except requests.exceptions.RequestException:
                    print("[error]: Ошибка получения картинки: ", link_url)

    def save_video(self, video, article_name):
        with open('video.txt', 'w+', encoding='UTF-8') as f:
            for link in video:
                if link.get('data-src'):
                    print(link.get('data-src'), ' | ', article_name, file=f)

    def define_numer_of_pages(self, url, type_articles):
        r = requests.get(url)
        url_soup = BeautifulSoup(r.text, 'lxml')
        #spans = url_soup.find_all("span", {"class": "tm-tabs__tab-counter"})
        spans = url_soup.find_all("span", {"class": "tm-tabs__tab-item"})
        
        if type_articles == 'u':
            span = spans[1]
        elif type_articles == 'f':
            span = spans[3]
        elif type_articles == 's':
            span = spans[1]
        
        span = span.find('span')
        span_value = re.sub(r'[^0-9]', '', span.text)
        number_of_pages = math.ceil(int(span_value)/20)
        return number_of_pages


    def get_articles(self, url, type_articles):
        number_of_pages = self.define_numer_of_pages(url, type_articles)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            print("[error]: Ошибка получения статей: ", url)
            return

        url_soup = BeautifulSoup(r.text, 'lxml')
        posts = url_soup.findAll('a', {'class': 'tm-title__link'})
        self.posts += posts
        if number_of_pages > 1: 
            for page in range(2, number_of_pages + 1):
                try:
                    r = requests.get(url + "page" + str(page))
                except requests.exceptions.RequestException:
                    print("[error]: Ошибка получения последующих страниц из списка статей: ", url)
                    return

                url_soup = BeautifulSoup(r.text, 'lxml')
                posts = url_soup.findAll('a', {'class': 'tm-title__link'})
                self.posts += posts


    def parse_articles(self, type_articles):
        print(f"[info]: Будет загружено: {len(self.posts)} статей.")

        with pymp.Parallel(multiprocessing.cpu_count()) as pmp:
            #for p in self.posts :
            for i in pmp.range(0, len(self.posts)):
                p = self.posts[i]
                if not args.quiet:
                    print("[info]: Скачивается:", p.text)

                name = self.dir_cor_name(p.text)

                dir_path = '{:03}'.format(len(self.posts) - i) + " " + name

                # создаем директории с названиями статей
                self.create_dir(dir_path)
                # заходим в директорию статьи
                os.chdir(dir_path)

                self.get_article(HABR_TITLE + p.get('href'), name)

                # выходим из директории статьи
                os.chdir('../')

    def main(self, url, dir, type_articles):
        # создаем папку для статей
        self.create_dir(dir)
        os.chdir(dir)

        # создаем папку с именем автора
        self.dir_author = url.split('/')[5]
        self.create_dir(self.dir_author)
        os.chdir(self.dir_author)

        self.get_articles(url, type_articles)

        self.parse_articles(type_articles)

        os.chdir('../')


class IndexBuilder():

    def __init__(self):
        self._articles = []

    def make_index(self):
        src_articles = [f for f in natsort.os_sorted(os.listdir('.')) if f.endswith('.html') and f.lower() != 'index.html']
        for file in src_articles:
            soup = BeautifulSoup(open(file, encoding="utf8"), 'lxml')
            metadata = [
                (x, soup.find('meta', {'property': str('hdl_' + x)}))
                for x in ['author', 'url','post_date','author_country_code','author_type', 'orig_title']]
            metadata = [(x,v.attrs['content']) for x,v in metadata if v]
            metadata = metadata + [('file', file), ('title', soup.find('title').string)]
            metadata = dict(metadata)
            if 'orig_title' not in metadata or not metadata['orig_title']:
                metadata['orig_title'] = file[:-5]
            if 'author' not in metadata or not metadata['author']:
                metadata['author'] = 'неизв.'
            self._articles.append(metadata)
        with open("index.html", "w", encoding="UTF-8") as fd:
            fd.write('<!DOCTYPE html>\n<html><head>\n')
            fd.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
            fd.write('<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover">\n')
            fd.write('<link rel="stylesheet" href="js/habr.css">\n')
            fd.write('<script src="js/habr.js"></script>\n</head><body>\n\n')
            fd.write('<div class="art_index_cnt"><p class="art_index_h1">Перечень статей:</p>\n')

            fd.write('<div class="index_spoiler index_spoiler_open" role="button" tabindex="0"><span class="index_spoiler_title">По алфавиту:</span>\n<div class="index_spoiler_txt">\n')
            self._ul_article(fd, self._articles)
            fd.write('</div></div>\n')

            authors = natsort.natsorted(set(x['author'] for x in self._articles))
            if len(authors) > 1:
                fd.write('<p class="art_index_h1">Перечень авторов:</p>')
                fd.write('<ul class="author_list">\n')
                for a in authors:
                    arts = [x for x in self._articles if x['author'] == a]
                    fd.write('<li><div class="index_spoiler" role="button" tabindex="0">\
                        <span class="index_spoiler_title"><span class="author">' + html.escape(a) + '</span></span><div class="index_spoiler_txt">')
                    self._ul_article(fd, arts)
                    fd.write('</div></div></li>\n')
                fd.write('</ul>\n')

            fd.write('</div>\n<div class="art_index_end"></div></body></html>')

    def _ul_article(self, fd, articles):
        """Write into file <ul>...</ul> block for provided list of articles"""
        _articles = articles
        fd.write('\n<ul class="art_index">')
        for art in _articles:
            fd.write(f"\n <li><span><a href='{art['file']}'>")
            fd.write(html.escape(art['orig_title']) + "</a></span>")
            a = ['&nbsp;<span class="' + x + '">' + html.escape(art[x]) + 
                '</span>' if x in art else '&nbsp;<span class="missing ' + x + '">&mdash;</span>'
                for x in ['author', 'post_date'] ]
            for tg in a:
                fd.write(tg)
            fd.write('\n </li>')
        fd.write('\n</ul>\n')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Скрипт для скачивания статей с https://habr.com/")
    parser.add_argument('-q', '--quiet', help="Quiet mode", action='store_true')
    parser.add_argument('-c', '--comments', help="Создать файл с коментариями к статье", action='store_true')
    parser.add_argument('-l', '--local-pictures',
                        help="Cкачать все картинки локально и использовать абсолютный путь к изображениям", action='store_true')
    parser.add_argument('--no-meta-information', help="Не добавить мета-информацию о статье на экран", action='store_true')
    parser.add_argument('--no-index', help="Не создавать файл index.html", action='store_true')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', help="Скачать статьи пользователя", type=str, dest='user_name_for_articles')
    group.add_argument('-f', help="Скачать закладки пользователя", type=str, dest='user_name_for_favorites')
    group.add_argument('-s', help="Скачать одиночные статьи (список ID через запятую)", type=str, dest='article_id')

    args = parser.parse_args()

    type_articles = None

    if args.user_name_for_articles:
        output_name = args.user_name_for_articles + "/publications/articles/"
        output = DIR_ARCTICLE
        type_articles = 'u'
    elif args.user_name_for_favorites:
        output_name = args.user_name_for_favorites + "/bookmarks/articles/"
        output = DIR_FAVORITES
        type_articles = 'f'
    else:
        output_name = args.article_id
        type_articles = 's'
        output = DIR_SINGLES

    habrSD = HabrArticleDownloader()
    try:
        if not args.article_id:
            habrSD.main("https://habr.com/ru/users/" + output_name, output, type_articles)
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
            art_list = []
            for ar_id in args.article_id.split(','):
                art_list.append(habrSD.get_article("https://habr.com/ru/post/" + ar_id, type_articles))
    except Exception as ex:
        print("[error]: Ошибка получения данных от :", output_name)
        print(ex)
    try:
        if not args.no_index:
            index = IndexBuilder()
            index.make_index()
    except Exception as ex:
        print("[error]: Ошибка создания файла index.html")
        print(ex)

# apt install libomp-dev
