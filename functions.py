#! python3

import http.cookiejar
import codecs
import uuid
import re
import io
import json
import os
from urllib import request, parse, error
from config import linkme_user, linkme_pass, image_host


def clean_text(text):
    """Функция очистки от некоторых html-мнемоник.
       Вход  : текст для очистки
       Выход : текст без мнемоник"""

    # Заменяются мнемоники &laquo;, &raquo;, &nbsp;
    text = text.replace('&laquo;', '«')
    text = text.replace('&raquo;', '»')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&nbsp', ' ')
    text = text.replace('&mdash;', '—')
    text = text.replace('&ndash;', '–')
    text = text.replace('&amp;', '&')

    return text


def get_edition_notice(html):
    """Функция обрабатывает основную информацию о книге.
       Вход  : html-код страницы с книгой
       Выход : блок основной информации в bb-тегах"""

    # Получаем блок
    result = re.findall(r"<td\swidth=100%>.*?</td>", html, flags=re.DOTALL)

    # Очишаем от атрибутов тегов
    result = re.sub(r'(style|href|itemprop)=[\'"].*?[\'"]', '', result[0])
    result = re.sub(r"size=.*?(>)", r'\1', result)

    # Убираем ненужные теги: <meta>, <td>, <a></a>
    result = re.sub(r'<meta.*?>', '', result)
    result = re.sub(r'</?td.*?>', '', result)
    result = re.sub(r'</?a\s*>', '', result)
    result = re.sub(r'<a\shref=.*?>', '', result)

    # Заменяем оставшиеся теги на bb-код
    result = re.sub(r'<h1\s*>', '\n[size=16]', result)
    result = re.sub(r'</h1>', '[/size]\n', result)
    result = re.sub(r'<font\scolor=gray>(.*?)</font>', r'[color=gray]\1[/color]', result)
    result = re.sub(r'<font\s*>', '\n[size=16]', result)
    result = re.sub(r'</font>', '[/size]\n', result)
    result = re.sub(r'<b\s*>', '[b]', result)
    result = re.sub(r'</b>', '[/b]', result)
    result = result.replace('</span><p>Страниц:', '</span>\n<p>Страниц:')  # fix bug
    result = re.sub(r'<p\s*>', '', result)
    result = re.sub(r'</p>', '\n', result)
    result = re.sub(r'<span\s*>', '[i]', result)
    result = re.sub(r'</span>', '[/i]', result)

    # Немного красоты
    result = re.sub(r'Формат', '\n[b]Формат[/b]', result)
    result = result.replace('Тираж:', '[b]Тираж:[/b]')
    result = result.replace('ISBN', '[b]ISBN[/b]')
    result = result.replace('Страниц:', '[b]Страниц:[/b]')
    result = result.replace('Тип обложки:', '[b]Тип обложки:[/b]')
    result = result.replace('Серия:', '[b]Серия:[/b]')
    result = result.replace('Составитель:', '[b]Составитель:[/b]')
    result = result.replace('Составители:', '[b]Составители:[/b]')
    result = result.replace('Продолжительность:', '[b]Продолжительность:[/b]')

    # Обрабатываем изоюражения
    image_links = re.findall(r"<img src='(.*?)'\s/>", result, flags=re.DOTALL)
    if (image_links):
        for image_link in image_links:
            IH_link = get_image_url(image_link)
            result = re.sub(r"<img\ssrc='" + image_link.replace('.', '\.') +
                            r"'\s/>", '[img]' + IH_link + '[/img]', result)

    # Финальная чистка
    result = re.sub(r'\n(\n\[b\]Формат)', r'\1', result)
    result = clean_text(result)

    return result


def get_content(html):
    """Функция обрабатывает блок "Содержание".
       Вход  : html-код страницы с книгой
       Выход : блок "Содержание" в bb-тегах"""

    # Получаем блок
    result = re.findall(r"<div style='padding-left:5px;'>.*?</div>", html,
                        flags=re.DOTALL)

    # Очишаем от атрибутов тегов
    result = re.sub(r'(style|class|data-fantlab_type|data-fantlab_id|href)=[\'"].*?[\'"]', '', result[0])
    result = re.sub(r'class=(agray|abzac)', '', result)

    # Убираем ненужные теги: <div></div>, <a></a>,<br>, <p></p>
    result = re.sub(r'</?div\s*>', '', result)
    result = re.sub(r'</?a.*?>', '', result)
    result = re.sub(r'</?p\s*>', '', result)
    result = re.sub(r'<br>', '', result)

    # Заменяем оставшиеся теги на bb-код
    result = re.sub(r'<ul\s*>', '[list]', result)
    result = re.sub(r'</ul>', '[/list]', result)
    result = re.sub(r'<span\s*>', '[i]', result)
    result = re.sub(r'</span>', '[/i]', result)
    result = re.sub(r'<li\s*>', '[*]', result)
    result = result.replace('<b>', '[b]')
    result = result.replace('</b>', '[/b]')
    result = result.replace('<i>', '[i]')
    result = result.replace('</i>', '[/i]')
    result = result.replace('<font color=gray>', '[color=gray]')
    result = result.replace('</font>', '[/color]')

    # Убираем номера страниц
    result = re.sub(r',\s*(стр|с|cтр|c)?\.?\s?\d{1,3}-?\d{0,3}', '', result)

    # Финальная чистка
    result = clean_text(result)

    # bug fix
    if '[list]' == result[:6] and '[/list]' not in result[-9:]:
        result = result + '[/list]'
    if '[*]' == result[:3]:
        result = '[list]' + result + '[/list]'

    return result


def MultipartFormdataEncoder(image, name):
    """Функция кодирования изображения для отправки multipart/form-data.
       Вход  : ссылку на изображение и имя для Content-Disposition
       Выход : Content-Type и байтовый объект (или что-то такое xD)"""

    # Создадим границу - последовательность байтов,
    # которая не должна встречаться внутри закодированного представления данных части.
    boundary = uuid.uuid4().hex

    # Устанавливаем Content-Type
    content_type = 'multipart/form-data; boundary={}'.format(boundary)

    # Создаем байтовый объект
    item_list = []

    # Дополнительные параметры для фастпик, которые скорее всего и не нужны :)
    if image_host == 'fastpic':
        templist1 = ('jpeg_quality', 'uploading', 'check_thumb', 'thumb_text', 'fp_sid', 'submit', 'nocookie',
                     'check_orig_resize', 'upload_id', 'res_select', 'orig_rotate', 'orig_resize', 'thumb_size',
                     'ajax')
        templist2 = ('75', '1', 'size', 'Увеличить', 'd5b7d6af0297a06cd767c6f262d9f925', 'Загрузить', '1', '1',
                     'h0MCYY19zI', '500', '0', '500', '170', '1')
        for k1, k2 in zip(templist1, templist2):
            item_list.append('--{}\r\n'.format(boundary))
            item_list.append('Content-Disposition: form-data; name="{}"\r\n'.format(k1))
            item_list.append('\r\n')
            item_list.append('{}\r\n'.format(k2))

    item_list.append('--{}\r\n'.format(boundary))
    item_list.append('Content-Disposition: form-data; name="{}"; filename="{}"\r\n'.format(name, image))
    item_list.append('Content-Type: {}\r\n'.format('application/octet-stream'))
    item_list.append('\r\n')

    body = io.BytesIO()
    for chunk in item_list:
        body.write(chunk.encode('utf-8'))
    with open(image, 'rb') as fd:
        buff = fd.read()
        body.write(buff)
    body.write('\r\n'.encode('utf-8'))

    # Снова дополнительные параметры для фастпик, которые скорее всего и не нужны :)
    if image_host == 'fastpic':
        body.write('--{}\r\n'.format(boundary).encode('utf-8'))
        body.write('Content-Disposition: form-data; name="Upload"\r\n'.encode('utf-8'))
        body.write('\r\n'.encode('utf-8'))
        body.write('Submit Query'.encode('utf-8'))

    body.write('--{}--\r\n'.format(boundary).encode('utf-8'))

    return content_type, body.getvalue()


def get_cover_image(html):
    """Функция получения обложки книги.
       Вход  : html-код страницы с книгой
       Выход : ссылку на изображение обложки книги на выбраном хостинге изображений"""

    # Получаем нужный блок
    result = re.findall(r"<div\sstyle='margin-bottom:5px;\swhite-space:nowrap;'>.*?</div>", html, flags=re.DOTALL)[0]

    # Проверяем, есть ли большое изображение.
    if 'href' in result:
        image_url = re.findall("href='(.*?)'", result)[0]
        try:
            if image_url[:2] == '//':
                image_url = 'https:' + image_url
            request.urlopen(image_url)
        except error.HTTPError as err:
            if err.code == 404:
                image_url = re.findall("src='(.*?)'", result)[-1]
            else:
                raise
    else:
        image_url = re.findall("src='(.*?)'", result)[-1]

    # Заливаем на хостинг
    image_url = get_image_url(image_url)

    return image_url


def get_image_url(url):
    """Функция-обертка для изображений. Сохраняет изображение и выбирает нужный хостинг
       Вход  : ссылка на изображение
       Выход : ссылку на изображение на выбраном хостинге изображений"""

    # Получаем полную ссылку
    if url[:2] == '//':
        url = 'https:' + url

    # Временно сохраняем изображение
    image = url.split('/')[-1]
    response = request.urlopen(url)
    out = open(image, 'wb')
    out.write(response.read())
    out.close()

    # Выбираем хостинг и возвращаем ссылку. Нужный хостинг задается в config.py.
    if image_host == 'linkme':
        return IH_linkme_ufanet(image)
    elif image_host == 'fastpic':
        return IH_fastpic(image)


def IH_linkme_ufanet(url):
    """Функция для заливки изображений на локальный хостинг - linkme.ufanet.ru.
       Вход  : ссылка на изображение
       Выход : ссылку на изображение на выбраном хостинге изображений"""

    # Включим печеньки
    cookie = http.cookiejar.CookieJar()
    request.install_opener(request.build_opener(request.HTTPCookieProcessor(cookie)))

    # Добавим заголовки
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0'}

    # Установка логина-пароля. Логин-пароль задаются в config.py
    params = parse.urlencode({'user': linkme_user, 'pass': linkme_pass})
    bin_params = params.encode('utf-8')

    # Запрос для получения печенег
    linkme_url = 'http://passport.ufanet.ru/enter/?a=a%3A2%3A%7Bs%3A6%3A%22backto%22%3Bs%3A29%3A%22http%3A%2F%2Flinkme.ufanet.ru%2Fenter%22%3Bs%3A3%3A%22xml%22%3Bb%3A1%3B%7D'
    req = request.Request(linkme_url, bin_params, headers)
    request.urlopen(req)

    # Получим Content-Type и байтовый объект
    content_type, body = MultipartFormdataEncoder(url, 'Filedata')

    # Добавим заголовки
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0',
               'Content-Type': content_type}

    # Заливка изображения на хостинг
    req = request.Request('http://linkme.ufanet.ru/image/upload/0', body, headers)
    f3 = request.urlopen(req)

    # Сервер возвращает ответ в формате json.
    json_dict = json.loads(f3.read().decode('utf-8'))

    # Удвление ненужного изображения
    os.remove(url)

    return json_dict['fullLink'].replace('/images/', '/box/400x500/')


def IH_fastpic(url):
    """Функция для заливки изображений на локальный хостинг - linkme.ufanet.ru.
       Вход  : ссылка на изображение
       Выход : ссылку на изображение на выбраном хостинге изображений"""

    # Включим печеньки
    cookie = http.cookiejar.CookieJar()
    request.install_opener(request.build_opener(request.HTTPCookieProcessor(cookie)))

    # Добавим заголовки
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0'}

    # Запрос для получения печенег
    req = request.Request('http://fastpic.ru/', headers=headers)
    request.urlopen(req)

    # Получим Content-Type и байтовый объект
    content_type, body = MultipartFormdataEncoder(url, 'file1')

    # Добавим заголовки
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0',
               'Content-Type': content_type}

    # Заливка изображения на хостинг
    req = request.Request('http://fastpic.ru/upload', body, headers)
    f3 = request.urlopen(req)

    # Удвление ненужного изображения
    os.remove(url)

    return re.findall(r'value="(.*?)"', f3.read().decode('utf-8').replace('\\', ''))[0]


def get_book_info(html):
    """Функция обрабатывает блок "Описание" и "Примечание".
       Вход  : html-код страницы с книгой
       Выход : блок "Описание" и "Примечание" в bb-тегах"""

    # Получаем блок    "Описание"
    result = re.findall(r"Описание:</b>.*?<p\sstyle='margin-top:10px'>", html, flags=re.DOTALL)

    # А есть ли блок?
    if result == []:
        opis = ''
    else:

        # Очищаем от ненужных тегов и заменяем bb-тегами
        opis = re.sub(r'(style|class|data-fantlab_type|data-fantlab_id|href)=[\'"].*?[\'"]', '', result[0])
        opis = re.sub(r'<span.*?>', '[i]', opis)
        opis = opis.replace('</span>', '[/i]')
        opis = re.sub(r'<a.*?>(.*?)</a>', r'\1', opis)
        opis = opis.replace('Описание:</b></p>', '[b]Описание:[/b]\n')
        opis = opis.replace('</p>', '\n')
        opis = re.sub(r'<p.*?>', '', opis)
        opis = re.sub(r'<ul\s*>', '[list]', opis)
        opis = re.sub(r'</ul>', '[/list]', opis)
        opis = re.sub(r'<span\s*>', '[i]', opis)
        opis = re.sub(r'</span>', '[/i]', opis)
        opis = re.sub(r'<li\s*>', '[*]', opis)
        opis = opis.replace('<br>', '')
        opis = opis.replace('<u>', '[b]')
        opis = opis.replace('</u>', '[/b]')
        opis = clean_text(opis)

    # Получаем блок    "Примечание"
    result = re.findall(r"Примечание:</b>.*?<div>", html, flags=re.DOTALL)

    # А есть ли блок?
    if result == []:
        prim = ''
    else:

        # Очищаем от ненужных тегов и заменяем bb-тегами
        prim = re.sub(r'<font.*', '', result[0], flags=re.DOTALL)
        prim = re.sub(r'(style|class|data-fantlab_type|data-fantlab_id|href)=[\'"].*?[\'"]', '', prim)
        prim = re.sub(r'<a.*?>(.*?)</a>', r'\1', prim)
        prim = prim.replace('Примечание:</b></p>', '[b]Примечание:[/b]\n')
        prim = prim.replace('</p>', '\n')
        prim = prim.replace('<div>', '')
        prim = re.sub(r'<p.*?>', '', prim)
        prim = prim.replace('<br><br>', '')
        prim = re.sub(r'<ul\s*>', '[list]', prim)
        prim = re.sub(r'</ul>', '[/list]', prim)
        prim = re.sub(r'<span\s*>', '[i]', prim)
        prim = re.sub(r'</span>', '[/i]', prim)
        prim = re.sub(r'<li\s*>', '[*]', prim)
        prim = prim.replace('<br>', '')
        prim = prim.replace('<u>', '[b]')
        prim = prim.replace('</u>', '[/b]')
        prim = clean_text(prim)

    return opis, prim


def get_title(html):
    """Функция для получения заголовка.
       Вход  : html-код страницы с книгой
       Выход : заголовок книги"""

    return re.findall(r'<font\scolor="white"><b>(.*?)</b></font>', html)[0]
