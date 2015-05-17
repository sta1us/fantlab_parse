#! python3

import codecs
import sys
import urllib.request
from config import pattern
from functions import get_edition_notice, get_content,\
                            get_cover_image, get_book_info, get_title


def print_help():
    """Функция вывода справочной информации.
       Вход  : без аргументов
       Выход : текст справочной информации"""

    print("""usage: {0} url1 [url2 [... urlN]][-i filename] [-o filename]
        Parser fantlab.ru to bb-code

        Options:
        -h. -help        print help information and exit
        -o filename      output file
        -i filename      input file
        -v               verbose mode""".format(sys.argv[0]))


def get_html(url):
    """Функция для получения html-кода страницы с книгой.
       Вход  : ссылка на книгу
       Выход : html-код страницы с книгой"""

    response = urllib.request.urlopen(url)

    return response.read().decode('utf-8')


def get_info(html):
    """Функция для извлечения информации из html-кода.
       Вход  : html-код
       Выход : список, состоящий из информации о заголовке, обложке, блок "Описание"
               блок основной информации, блок "Содержание", блок "Примечание".  """

    # Блок основной информации
    book_info = get_edition_notice(html)
    # Блок "Содержание"
    content = get_content(html)
    # Обложка книги
    cover = get_cover_image(html)
    # Заголовок
    title = get_title(html)
    # Блок "Описание" и "Примечание"
    opis, prim = get_book_info(html)

    return title, cover, book_info, opis, content, prim


def main():
    """Основная функция. Запускается при старте программы
       Вход  : без аргументов
       Выход : добавляет информацию о книге(-ах) в текстовой файл."""

    # Запущена без параметров или с параметром -h (-H), -help(-HELP)
    if len(sys.argv) == 1 or sys.argv[1].lower() in {"-h", "--help"}:
        print_help()
        sys.exit()

    # Иначе обрабатываем параметры.
    # По умолчанию выходной файл 'output.txt' и режим verbose отключен
    else:
        urls = []
        output_file = 'output.txt'
        verbose = 0
        i = iter(sys.argv[1:])
        for item in i:
            if 'https://fantlab.ru' in item:
                urls.append(item)
            elif '-i' == item.lower():
                input_file = next(i)
                with codecs.open(input_file, 'r', 'utf-8') as f:
                    for line in f:
                        urls.append(line.rstrip())
            elif '-o' == item.lower():
                output_file = next(i)
            elif '-v' == item.lower():
                verbose = 1
            else:
                print ('Unknow option: {}'.format(item))
                sys.exit()

    # Обрабатывааем все полученные ссылки
    if len(urls) > 0:
        with codecs.open(output_file, 'a', 'utf-8') as f:
            i = iter(urls)
            for item in i:
                if verbose:
                    print("==> {}".format(item))
                f.write(pattern.format(*get_info(get_html(item))))

if __name__ == "__main__":
    main()
