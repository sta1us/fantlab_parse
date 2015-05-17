# fantlab_parse
Парсер Fantlab.ru в bb-код

### Установка
```
git clone https://github.com/sta1us/fantlab_parse.git
```

или скачать [zip-архив](https://github.com/sta1us/fantlab_parse/archive/master.zip).
### Запуск
Для запуска необходим Python >= 3.0. 

```python fantlab_parse.py url1 [url2 [... urlN]][-i filename] [-o filename] [-v]
```

 где:
 
- **url1...urlN** - ссылки на книги
- **-i filename** - имя входного файла с ссылками. Необязательный параметр
- **-o filename** - имя выходного файла. Необязательный параметр, по умолчанию имя выходного файла "output.txt"
- **-v** - "болтливый" режим. Будет выводиться текущая обрабатываемая ссылка. Необязательный параметр

Параметры **urlN** и **-i filename** взаимодополняемы. Обязательным является как минимум один, но можно задать оба.

##### Дополнительно:

- **-h** или **-help** - вывод справочной информации. 

##### Примеры

```python fantlab_parse.py -h
```

```python fantlab_parse.py https://fantlab.ru/edition146046
```

```python fantlab_parse.py -i links.txt
```

```python fantlab_parse.py https://fantlab.ru/edition146046 -o code.txt
```

```python fantlab_parse.py https://fantlab.ru/edition146046 -i links.txt -o code.txt -v
```
##### Примечание:
В выходном файле используется перевод строк в unix-стиле. Для корректного отображения в операционной системе Windows желательно использовать сторонний текстовый редактор вместо встроенного "Блокнота". Например, [Notepad++](https://notepad-plus-plus.org/). 

### Настройки
В файле **config.py** можно задать:

- **image_host** - хостинг для изображений.
 Вариантов два:  **fastpic** - http://fastpic.ru/ (вариант по умолчанию) и **linkme** - http://linkme.ufanet.ru/ (локальный хостинг, для загрузки изображений нужны логин/пароль)
- **linkme_user/pass** - задает логин/пароль для локального хостинга изображений.
- **pattern** - задает шаблон для оформления одной книги. Параметры: {0} - заголовок, {1} - обложка книги, {2} - основная информация, {3} - блок "Описание", {4} - блок "Содержание", {5} - блок "Примечание"

### Благодарности
Спасибо сайту **[FantLab.ru](https://fantlab.ru)** за то, что вы есть :)