# chatroom_server
API chat room handler.

To get SSL certificate (certificate.crt) and a private key (private.key) to enable wss://

```commandline
openssl req -new -x509 -days 365 -nodes -out certificate.crt -keyout private.key
```
