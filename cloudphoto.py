import os

import boto3
from os import listdir
from os.path import isfile, join, expanduser
import logging
import argparse
import yaml

key = None
secret = None
bucket = None
path = None
command = None
album = None
path = None
config_path = expanduser("~") + '/.osf/config.yaml'


# Чтение секретов из файла конфигурации
def read_config():
    global key
    global secret
    global bucket

    with open(config_path) as file:
        parameter_list = yaml.load(file, Loader=yaml.FullLoader)
        key = parameter_list['osf_access_key_id']
        secret = parameter_list['osf_secret_access_key']
        bucket = parameter_list['osf_bucket']


# отправка фотографий из каталога в альбом
def upload_file(path, album=""):
    if not os.path.isdir(path):
        logging.error(path + " : directory is not exist")
        return

    if album != "":
        album = album + '/'

    s3 = boto3.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=key, aws_secret_access_key=secret)
    files = [f for f in listdir(path) if (isfile(join(path, f)) and f.endswith(('.jpg', 'jpeg')))]
    for f in files:
        filePath = path + '/' + f
        distance = album + f
        s3.upload_file(filePath, bucket, distance)
        print('Uploaded: ' + filePath + " -> " + distance)
    print("Success")


# Проверка сущетвования альбома
def album_exists(s3, bucket, path) -> bool:
    path = path.rstrip('/')
    resp = s3.list_objects(Bucket=bucket, Prefix=path, Delimiter='/')
    return 'CommonPrefixes' in resp


# Загрузка фотографий из альбома в каталог
def download_files(path, album):
    if not os.path.isdir(path):
        logging.error(path + " : directory is not exist")
        return

    s3 = boto3.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=key, aws_secret_access_key=secret)

    if not album_exists(s3, bucket, album):
        logging.error("Album: " + album + " : is not exist")
        return

    album += '/'
    result = s3.list_objects(Bucket=bucket, Prefix=album, Delimiter='/')
    for o in result.get('Contents'):
        get_object_response = s3.get_object(Bucket=bucket, Key=o.get('Key'))
        data = get_object_response['Body'].read()
        distance = path + "/" + o.get('Key').split('/')[1]
        f = open(distance, "wb")
        f.write(data)
        f.close()
        print('Downloaded: ' + o.get('Key') + " -> " + distance)

    print("Success")


# Список фотографий в альбоме
def image_list_in_album(album):
    if album is None:
        logging.error("Need album value")
        return

    s3 = boto3.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=key, aws_secret_access_key=secret)

    if not album_exists(s3, bucket, album):
        logging.error("Album: " + album + " : is not exist")
        return
    album += '/'
    result = s3.list_objects(Bucket=bucket, Prefix=album, Delimiter='/')
    for o in result.get('Contents'):
        print("File:", o.get('Key').split('/')[1], "Size:", o.get('Size'))


# Список всех альбомов
def album_list():
    s3 = boto3.client(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                      aws_access_key_id=key, aws_secret_access_key=secret)
    result = s3.list_objects(Bucket=bucket, Delimiter='/')
    if result.get('CommonPrefixes'):
        for o in result.get('CommonPrefixes'):
            print(o.get('Prefix').split('/')[0])
    else:
        print("No one album is not exist")


# Вызовы методов
def run():
    if command == 'upload':
        upload_file(path, album)
    elif command == 'download':
        download_files(path, album)
    elif command == 'list' and album is not None:
        image_list_in_album(album)
    elif command == 'list' and album is None:
        album_list()
    else:
        logging.error(command + " is not correct")


# Парсинг метода и флагов
parser = argparse.ArgumentParser()
parser.add_argument("command", help="Command")
parser.add_argument("-p", help="Path")
parser.add_argument("-a", help="Album")
args = parser.parse_args()
read_config()
command = args.command
path = args.p
album = args.a
run()
