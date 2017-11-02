import boto
from boto.s3.key import Key
import os
import urllib
import requests
import json
import time
from flask import Flask, request

#S3 bucket info including an optional subdirectory for your file upload
bucket_name = "<your_S3_bucket>"
upload_path = '/<your_upload_path>/'
bucket_region = "<your_S3_region>"

#Flowroute API endpoint and reply SMS to be sent
fr_api_url = "https://api.flowroute.com/v2.1/messages"
reply_message = 'Thanks for the picture!'

app = Flask(__name__)
app.debug = True

@app.route('/inboundmms', methods=['POST'])
def inboundmms():
    
    bucket = gets3bucket(bucket_name, bucket_region)

    #extract attributes from POSTed JSON of inbound MMS
    json_content = request.json
    reply_to = json_content['data']['attributes']['from']
    reply_from = json_content['data']['attributes']['to']
    media_url = json_content['included'][0]['attributes']['url']

    #add a timestamp to prevent overwriting files
    rcv_time = str(int(time.time()))
    filename = rcv_time + "_" + reply_to

    #temporarily download the media to your local file system
    tmpfile = '/tmp/' + filename
    urllib.urlretrieve(media_url, tmpfile)
 
    #upload the media to your specified S3 bucket
    uploadtos3(bucket, tmpfile, filename)

    #remove file from local file system
    os.remove(tmpfile)

    #send a reply SMS from your Flowroute number
    sendreply(reply_to, reply_from)

    return '0'

#create S3 connection
def gets3bucket(bucket_name, bucket_region):

    AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
    AWS_SECRET_KEY = os.environ['AWS_SECRET_KEY']

    conn = boto.s3.connect_to_region(bucket_region,
           aws_access_key_id=AWS_ACCESS_KEY,
           aws_secret_access_key=AWS_SECRET_KEY
           )
    bucket = conn.get_bucket(bucket_name, validate=False)

    return bucket

#upload file to S3
def uploadtos3(bucket, path, key):

    k = Key(bucket)
    k.key = upload_path + key
    k.set_contents_from_filename(path)

    return None

#send a reply SMS using your Flowroute credentials 
def sendreply(reply_to, reply_from):

    FR_ACCESS_KEY = os.environ['FR_ACCESS_KEY']
    FR_SECRET_KEY = os.environ['FR_SECRET_KEY']

    auth = (FR_ACCESS_KEY, FR_SECRET_KEY)

    replyheaders = {'Content-Type': 'application/vnd.api+json'}
    replydata = { 'from': reply_from, 'to': reply_to, 'body': reply_message }
    r = requests.post(fr_api_url, auth=auth, json=replydata, headers=replyheaders)
    print r.status_code
    return None

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8080")
    )
