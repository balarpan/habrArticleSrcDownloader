# habrArticleSrcDownloader

Данный скрипт для скачивания исходников статей с [habr](https://habr.com/) основан на проекте
[dvjdjvu / habrArticleSrcDownloader](https://github.com/dvjdjvu/habrArticleSrcDownloader).

По сравнению с оригинальным проектом в этом репозитории:

- устранена ошибка наименования файла при скачивании одиночной статьи;
- все статьи сохраняются в один каталог с общей папкой для скачанных изображений;
- добавлена возможность указать через запятую несколько статей для скачивания;
- уже скачанный ранее файл изображения не скачивается повторно при работе со следующей заметкой;
- изображения из статьи скачиваются в многопоточном режиме, текст заметки - в однопоточном;
- многопоточный режим теперь доступен и на Windows;
- при создании перечня ссылок на видео в заметке файл не перезаписывается, а новые записи добавляются в конец файла;
- файл с перечнем ссылок на видео теперь через символ '|' содержит заголовок статьи, к которой относится ссылка;
- исправлен баг с несохранением картинок с формулами в SVG-изображениях и некоторых других;
- **добавлен новый параметр** запуска, контролирующий создание файла с комментариями к статье;
- убран излишний вывод предупреждений о парсинге XML-документа как HTML-документа;
- абсолютные ссылки на разделы в документе (https://...../#bla-bla) заменены на относительные;
- в сохраняемой HTML-версии статьи:
  - добавлена HTML-разметка для соответствия минимальным требованиям к законченному HTML-документу;
  - добавлены HTML-элементы для корректной работы стилей отображения документа;
  - добавлена подсветка синтаксиса через [highlight.js](https://highlightjs.org/) для наиболее популярных языков программирования;
  - для корректной работы подсветки синтаксиса убрана из оригинального скрипта замена тега **CODE** на тег **SOURCE**;
  - добавлено для постов компании сохранение метаданных компании;
  - восстановлено ближе к оригинальному оформление страницы, загружаемой с диска (оформление текста, заголовков разделов,  отступы, таблицы, изображения в тексте и др.);
  - добавлен в начало HTML-страницы блок мета-информации со ссылкой на оригинал статьи, автора и дату публикации;
  - для статьи-перевода добавлена ссылка на оригинал в начале статьи;
  - добавлены минимальные необходимые скрипты для корректной работы спойлеров в момент открытия созданного файла;
  - в каталоге одиночных статей создаётся файл index.html со сслыками на все найденные в папке HTML-файлы с указанием автора и даты публикации;
  - в каталогах статей автора и favorites index.html с перечнем авторов и названием его компании, а также фильтрация по имени автора;
  - в index.html включены все файлы в папке, в том числе не скачанные этим скриптом (автор будет указан как "неизв.");
  - статьи-переводы в перечне статей помечены отдельным символом;
  - для скачиваемых статей пользователя или закладок пользователя создается граф связей между закладкой на статью, статьей и автором, открываемый в новом окне по ссылке "Открыть граф связей".

Внимание: Полное тестирование проводилось только на ОС Windows и Python 3.11 .


## Как использовать:

### Установка:

#### Linux
```bash
apt-get install python3-lxml
pip3 install -r requirements.txt
```

#### macOS
```bash
brew install python-lxml
pip3 install -r requirements.txt
```

#### Windows
При установленном в системе Python 3.11 или более поздней версии:
```bash
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```


### Использование:
```
usage: main.py [-h] [-q] [-l] [-i] (-u USER_NAME_FOR_ARTICLES | -f USER_NAME_FOR_FAVORITES | -s ARTICLE_ID)

Скрипт для скачивания статей с https://habr.com/

options:
  -h, --help            show this help message and exit
  -q, --quiet           Quiet mode
  -c, --comments        Создать файл с коментариями к статье
  -l, --local-pictures  Cкачать все картинки локально и использовать абсолютный путь к изображениям
  --no-meta-information
                        Не добавить мета-информацию о статье на экран
  --no-index            Не создавать файл index.html
  -u USER_NAME_FOR_ARTICLES, --user-publications USER_NAME_FOR_ARTICLES
                        Скачать статьи пользователя
  -b USER_NAME_FOR_BOOKMARKS, --user-bookmarks USER_NAME_FOR_BOOKMARKS
                        Скачать закладки пользователя
  -s ARTICLE_ID         Скачать одиночные статьи (список ID через запятую)
```

Например:

```bash
./src/main.py -u jessy_james
```
```bash
./src/main.py -b jessy_james
```
```bash
./src/main.py -s 665254,809021
```

Взять имя пользователя можно из ссылки профиля

<img src="https://habrastorage.org/webt/4e/ur/ml/4eurmlni9b4f15fuqpuz4wrolmq.png" />


Если все было сделано успешно, то Вы увидите примерно следующее:
```bash
./src/main.py -u jessy_james
[info]: Будет загружено: 22 статей.
[info]: Скачивается: Шахматы. От начала до читов
[info]: Статья: Шахматы. От начала до читов сохранена
[info]: Скачивается: C/C++ из Python (Kivy, ctypes) на iOS
[info]: Статья: C C++ из Python (Kivy, ctypes) на iOS сохранена
[info]: Скачивается: Резервное копирование репозиториев с github, gitlab
[info]: Статья: Резервное копирование репозиториев с github, gitlab сохранена
[info]: Скачивается: Android. Starting Kivy App and Service on bootup
[info]: Статья: Android. Starting Kivy App and Service on bootup сохранена

...

[info]: Скачивается: Python из C (C API)
[info]: Статья: Python из C (C API) сохранена
[info]: Скачивается: Игрушка ГАЗ-66 на пульте управления. Часть 3
[info]: Статья: Игрушка ГАЗ-66 на пульте управления. Часть 3 сохранена
[info]: Скачивается: Игрушка ГАЗ-66 на пульте управления. Часть 2
[info]: Статья: Игрушка ГАЗ-66 на пульте управления. Часть 2 сохранена
[info]: Скачивается: Игрушка ГАЗ-66 на пульте управления. Часть 1
[info]: Статья: Игрушка ГАЗ-66 на пульте управления. Часть 1 сохранена

```


#### Docker

Сборка образа:

```
docker build -t habrsaver .
```

Запуск контейнера:

```
docker run --rm --name habrsaver  \
            -v $(pwd)/article:/app/article \
            -v $(pwd)/favorites:/app/favorites \
            -v $(pwd)/singles:/app/singles \
            habrsaver -s 665254
```
