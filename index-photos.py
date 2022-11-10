
import json
import urllib.parse
import boto3
import requests
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection

print('Loading function')

s3 = boto3.client('s3')
OPEN_SEARCH_URL = "https://search-photos-jo6y5vnguimbbqwuhmud2o3lny.us-east-1.es.amazonaws.com/photos/_doc"
AWS_AUTH_CREDENTIALS = ('Master','Master123@')
HEADERS = { "Content-Type": "application/json" }
# number_of_records_inserted  = 0

PLURAL_TO_SINGULAR_SUFFIX_MAPPING = [
    ('people', 'person'),
    ('men', 'man'),
    ('wives', 'wife'),
    ('menus', 'menu'),
    ('us', 'us'),
    ('ss', 'ss'),
    ('is', 'is'),
    ("'s", "'s"),
    ('ies', 'y'),
    ('ies', 'y'),
    ('es', 'e'),
    ('s', '')
]

def insert_into_open_search(data):

    post_response = requests.post(OPEN_SEARCH_URL,auth=AWS_AUTH_CREDENTIALS,json=data,headers=HEADERS)
    print("post_response",post_response)

def get_singular(word):
    if word is None or word=="":
        return ""
    for suffix,singular_suffix in PLURAL_TO_SINGULAR_SUFFIX_MAPPING:
        if word.endswith(suffix):
            return word[:-len(suffix)] + singular_suffix
    return word
    

def convert_custom_labels_to_singular(customlabels):
    labels = []
    for label in customlabels:
        labels.append(get_singular(label).lower())
    return labels



def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))
    print(event)
    
    # Get the object from the event and show its content type
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        photo_name  = record['s3']['object']['key']
        print(bucket_name,photo_name)
        labels = []
        metadata =[]
        metadata_object = None
        # metadata_object = {"customlabels":"horses,puppies"}
        s3_response = s3.head_object(Bucket=bucket_name, Key=photo_name)
        if "Metadata" in s3_response:
            metadata_object = s3_response["Metadata"]
            
        
        if metadata_object is not None and "customlabels" in metadata_object:
            metadata_labels = metadata_object["customlabels"].split(",")
            labels = convert_custom_labels_to_singular(metadata_labels)
            print("convert_custom_labels_to_singular",labels)
        else:
            print("Unable to find any custom labels for {} image".format(photo_name))

        recognition_client=boto3.client('rekognition')
        recognition_response  = recognition_client.detect_labels(Image={'S3Object':{'Bucket':bucket_name,'Name':photo_name}},
                                MaxLabels=10)
        
        for label in recognition_response['Labels']:
            labels.append(label['Name'].lower())
        
        print("recognition_response",recognition_response)
        print("s3_response",s3_response)
        print('Labels:',labels)

        data_to_be_inserted = {
            'objectKey' : photo_name,
            'bucket':bucket_name,
            'createdTimestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            'labels':labels
        }
        print("Data to be added in open search", data_to_be_inserted)

        insert_into_open_search(data_to_be_inserted)
        # number_of_records_inserted+=1
        return {
        'statusCode': 200,
        'headers':{
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Credentials':True,
            'Access-Control-Request-Headers':'*',
            'Access-Control-Allow-Headers':'*'
            
        },
        # 'body': json.dumps({"no_of_recrods_inserted":number_of_records_inserted})
    }
        
        
