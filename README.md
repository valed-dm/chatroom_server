# chatroom_server
API chat room handler.

To get SSL certificate (certificate.crt) and a private key (private.key) to enable wss://

```commandline
openssl req -new -x509 -days 365 -nodes -out certificate.crt -keyout private.key
```

Swagger: Создание и просмотр чатов. Попытка интегрировать Websocket endpoints.

[<img src="docs/images/img_01.png" width="600"/>]()

Создание чата:

[<img src="docs/images/img_02.png" width="600"/>]()
[<img src="docs/images/img_03.png" width="600"/>]()

Просмотр чатов:

[<img src="docs/images/img_04.png" width="600"/>]()

Установка Websocket соединения:

[<img src="docs/images/img_05.png" width="600"/>]()

Пользователи чата:

[<img src="docs/images/img_06.png" width="600"/>]()

Сообщения о присоединении:

[<img src="docs/images/img_07.png" width="600"/>]()

Пользователь покинул чат. Сообщение:

[<img src="docs/images/img_08.png" width="600"/>]()
[<img src="docs/images/img_09.png" width="600"/>]()

Сообщение для участников чата:

[<img src="docs/images/img_10.png" width="600"/>]()
[<img src="docs/images/img_11.png" width="600"/>]()

Изменение количества участников:

[<img src="docs/images/img_12.png" width="600"/>]()

Остановка сервера с причиной остановки:

[<img src="docs/images/img_13.png" width="600"/>]()

Логи:

[<img src="docs/images/img_14.png" width="600"/>]()
[<img src="docs/images/img_15.png" width="600"/>]()

Первые тесты:

[<img src="docs/images/img_16.png" width="600"/>]()


