import json
import boto3
import io
from PIL import Image
import os
import requests


def handler(event, context):
    print(event)
    data = event['messages'][0]

    S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
    S3_SECRET_KEY = os.environ['S3_SECRET_KEY']

    SQS_ACCESS_KEY = os.environ['SQS_ACCESS_KEY']
    SQS_SECRET_KEY = os.environ['SQS_SECRET_KEY']
    SQS_QUEUE = os.environ['SQS_QUEUE']

    if data['event_metadata']['event_type'] == 'yandex.cloud.events.storage.ObjectCreate':
        
        bucket_id = data['details']['bucket_id']
        object_id = data['details']['object_id']
        
        if len(object_id.split('/')) != 2:
            return {
                'statusCode': 200,
            }
        
        s3 = boto3.resource(service_name='s3', endpoint_url='https://storage.yandexcloud.net',
                            aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)

        b = downloadFileLikeObject(s3, bucket_id, object_id)
        faceList = findFaces(b)

        i = 0
        directory = object_id.rsplit('.', 1)[0]
        extension = object_id.split('.')[-1]
        new_object_id_list = []

        for face in faceList:
            new_object_id = directory + "/" + str(i) + "." + extension
            uploadObjectLikeFile(s3, bucket_id, new_object_id, face)
            new_object_id_list.append(new_object_id)
            i+=1

        sqs = boto3.resource(service_name='sqs', endpoint_url='https://message-queue.api.cloud.yandex.net', region_name='ru-central1',
                            aws_access_key_id=SQS_ACCESS_KEY, aws_secret_access_key=SQS_SECRET_KEY)
        send_message_to_queue(sqs, SQS_QUEUE, json.dumps(new_object_id_list))

    return {
        'statusCode': 200,
        'body': 'Hello World!',
    }


def downloadFileLikeObject(s3, bucketId, objectId):
    response = s3.Object(bucketId, objectId).get()
    return response['Body'].read()


def uploadObjectLikeFile(s3, bucketId, objectId, fileBody):
    newFile = s3.Object(bucketId, objectId)
    newFile.put(Body=fileBody)

def findFaces(bytes):
    FACE_ACCESS_KEY = os.environ['FACE_ACCESS_KEY']
    FACE_SECRET_KEY = os.environ['FACE_SECRET_KEY']
    face_detect_url ="https://api-us.faceplusplus.com/facepp/v3/detect"
    files= {"image_file": bytes}
    params = {
        'api_key': FACE_ACCESS_KEY,
        'api_secret' : FACE_SECRET_KEY,
        'return_attributes': 'headpose'
    }
    r = requests.post(face_detect_url, params, files=files)
    response = json.loads(r.text)
    
    result = []
    for a in response['faces']:
        result.append(cropImage(bytes, a['face_rectangle']))
    
    return result


def cropImage(bytes, face_rectangle):

    image = Image.open(io.BytesIO(bytes))
    area = (face_rectangle['left'], face_rectangle['top'], face_rectangle['width'] + face_rectangle['left'], face_rectangle['height'] + face_rectangle['top'])
    new_img = image.crop(area)
    return image_to_byte_array(new_img)


def image_to_byte_array(image: Image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format='JPEG')
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr

def send_message_to_queue(sqs, queue_name, json_message):
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    response = queue.send_message(MessageBody=json_message) 
