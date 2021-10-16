
Чтобы запустить приложение, нужно создать конфигурационный файл ~/.osf/config.yaml, содержащий:

```yaml
osf_access_key_id: key
osf_secret_access_key: secret
osf_bucket: bucket
```

Команды запуска cloudphoto.py:
- python cloudphoto.py upload -p path -a album
- python cloudphoto.py download -p path -a album
- python cloudphoto.py list
- python cloudphoto.py list -a album

Требуемый зависимости:
- os
- boto3
- logging
- argparse
- yaml