from opensearchpy import OpenSearch, RequestsHttpConnection

import boto3
import json
import re
import requests
import random
import string


OPEN_SEARCH_URL = "https://search-photos-jo6y5vnguimbbqwuhmud2o3lny.us-east-1.es.amazonaws.com/photos/_search?q=labels:{}"

HEADERS = { "Content-Type": "application/json" }

AWS_AUTH_CREDENTIALS = ('Master','Master123@')




def get_images_from_keywords(keywords):
    query_results = {}
    for label in keywords:
        response = requests.get(OPEN_SEARCH_URL.format(label.lower()), auth=AWS_AUTH_CREDENTIALS, headers=HEADERS)
        response = response.json()
        print("Label",label,"Response:",response)
        if len(response['hits']['hits']) == 0:
            print("No photographs found matching the query: {}".format(q))
            continue
        for sample in response['hits']['hits']:
            image_name =sample['_source']['objectKey']
            if image_name not in query_results:
                query_results[image_name] = sample['_source']['labels']
    
    return query_results

# def get_image_names(open_search_results):
#     name_labels_dict = {}
#     for result in open_search_results:
#         for hit in result['hits']['hits']:
#             image_name = hit['_source']['objectKey']
#             labels = hit['_source']['labels']
#             if image_name not in name_labels_dict.keys():
#                 name_labels_dict[image_name] = labels
#     return name_labels_dict


SINGULAR_SUFFIX = [
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

def singularize(noun):
    for suffix, singular_suffix in SINGULAR_SUFFIX:
        if noun.endswith(suffix):
            return noun[:-len(suffix)] + singular_suffix
    return noun

def get_open_search_supported_keywords(keywords):
    modified_keywords = []
    for keyword in keywords:
        if keyword is not None:
            modified_keywords.append(singularize(keyword).capitalize())
    return modified_keywords
    
def lambda_handler(event, context):
    try:
        print("event:{}".format(event))
        print("context:{}".format(context))
        if "q" not in event:
            return {
            'code': 400,
            'message': "Query parameter not present in request"
        }
        
        print("creating lex client")
        lex_bot_client = boto3.client('lexv2-runtime')
        print("lex client created")
        print(lex_bot_client)
        
  
    
        
        user_input = event["q"]
        
        print("User Input:{}".format(user_input))
        
        
        
        response = lex_bot_client.recognize_text(
                botAliasId="FOPVRKUGGG",  
                botId="TUBZIHIWQI",
                localeId= "en_US",
                text = user_input,
                sessionId= ''.join(random.choices(string.ascii_lowercase, k=10))
            )
        
        print("*******************Lex bot response:{}".format(response))
        
        keywords = []
        interpretations = response.get('interpretations', None)
        if interpretations is None:
            print("No interpreattaion found")
            return None
        slots = interpretations[0]['intent']['slots']
        print("Slots ",slots)
        keywords= []
        if "keyword1" in slots and slots["keyword1"] is not None:
            keywords.append(slots["keyword1"]['value']['originalValue'])
        if "keyword2" in slots and slots["keyword2"] is not None:
            keywords.append(slots["keyword2"]['value']['originalValue'])
        
        
        modified_keywords = get_open_search_supported_keywords(keywords)
        
        print("Keywords are:{}".format(keywords))
        print("Modified keywords are:{}".format(modified_keywords))
        image_names_labels = get_images_from_keywords(modified_keywords)
        print(image_names_labels)
        
        
        base_url = "https://bucket-for-photos-b2.s3.amazonaws.com/"
        results = []
        for image in image_names_labels.keys():
            image_info_json = {}
            image_info_json["url"] = base_url+image
            image_info_json["labels"] = image_names_labels[image]
            results.append(image_info_json)
        
        print("The result images are:{}".format(results))
        return {
        'statusCode': 200,
        'headers':{
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Credentials':True
            # 'Access-Control-Request-Headers':'*',
            # 'Access-Control-Allow-Headers':'*'
        },
        'body': {"results":results}
    }
        
    except Exception as e:
        return {
            'code': 0,
            'message': str(e)
        }