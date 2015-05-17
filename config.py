# Основной конфигурационный файл

# Задает хостинг для изображений. Вариантоы два:
#   fastpic - http://fastpic.ru/ [вариант по умолчанию]
#   linkme - http://linkme.ufanet.ru/ [локальный хостинг, для загрузки изображений нужны логин/пароль]
image_host = 'fastpic'

# Логин и пароль для хостинга linkme.ufanet.ru
linkme_user = ''
linkme_pass = ''

# Шаблон для оформления одной книги. Парметры:
#   {0} - заголовок
#   {1} - обложка книги
#   {2} - основная информация
#   {3} - блок "Описание"
#   {4} - блок "Содержание"
#   {5} - юлок "Примечание"
pattern="""[spoiler="{0}"]
[img=right]{1}[/img]
{2}[b]Формат:[/b] FB2 / RTF
[b]Качество: [/b]eBook (изначально компьютерное)

{3}
[b]Содержание:[/b]
{4}

{5}

[/spoiler]
"""