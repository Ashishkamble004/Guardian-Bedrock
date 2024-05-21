import os
import boto3
import random
import string
import base64, re, json


boto3_session = boto3.session.Session()
region = boto3_session.region_name

# create a boto3 bedrock client
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')

# get knowledge base id from environment variable
kb_id = os.environ.get("KNOWLEDGE_BASE_ID")
#print (kb_id)

# declare model id for calling RetrieveAndGenerate API
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
model_arn = f'arn:aws:bedrock:{region}::foundation-model/{model_id}'
bedrock_rt = boto3.client("bedrock-runtime", region_name="us-east-1")

claude_config = {
    'max_tokens': 1000, 
    'temperature': 0, 
    'anthropic_version': '',  
    'top_p': 1, 
    'stop_sequences': ['Human:']
}

def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def post_process_answer(response:str)->str:
    """
    Extracts the answer from the given response string.

    Args:
        response (str): The response string containing the answer.

    Returns:
        str: The extracted answer.
    """
    answer = re.findall(r'<answer>(.*?)</answer>', response, re.DOTALL)
    return answer[0]
    
def generate_vision_answer(bedrock_rt:boto3.client,messages:list, model_id:str, claude_config:dict,system_prompt:str):
    """
    Generates a vision answer using the specified model and configuration.
    
    Parameters:
    - bedrock_rt (boto3.client): The Bedrock runtime client.
    - messages (list): A list of messages.
    - model_id (str): The ID of the model to use.
    - claude_config (dict): The configuration for Claude.
    - system_prompt (str): The system prompt.
    
    Returns:
    - str: The formatted response.
    """
    
    body={'messages': [messages],**claude_config, "system": system_prompt}
    
    response = bedrock_rt.invoke_model(modelId=model_id, body=json.dumps(body))   
    response = json.loads(response['body'].read().decode('utf-8'))
    formated_response= post_process_answer(response['content'][0]['text'])
    
    return formated_response

# Create prompt and system prompt
system_prompt= "You have perfect vision and pay great attention to detail which makes you an expert at answering graph question. Answer question in <question></question> tags. Before answer, think step by step in <thinking> tags and analyze every part of the graph."
#Create a prompt with the question
prompt = f"<question>Suppose the timeframe for the graph is starting from 11 pm in the night, Identify anomalies in the graph, and specify a timefram to where the anomaly would have occured. </question>. Answer must be just the identified anomaly timeframe <answer></answer> tag."

# Create message with the prompt and the base64 encoded image
messages={"role": "user", "content": [
{
        "type": "image",
        "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": image_to_base64("images/OrderImage-main.png"),
        }
},
{"type": "text", "text": prompt}
]}

#Get response from the above prompt

timeframe=generate_vision_answer(bedrock_rt, messages, model_id, claude_config, system_prompt)    


def retrieveAndGenerate(input, kbId, model_arn, sessionId):
    #print(input, kbId, model_arn, sessionId)
    if sessionId != "":
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': f"Summarise the request {input} withing findings for timeframe {timeframe}"
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn
                }
            },
            sessionId=sessionId
        )
    else:
        return bedrock_agent_runtime_client.retrieve_and_generate(
            input={
                'text': f"Summarise the request {input} withing findings for timeframe {timeframe}"
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': model_arn
                }
            }
        )

def lambda_handler(event, context):
    query = event["question"]
    sessionId = event["sessionId"]
    response = retrieveAndGenerate(query, kb_id, model_arn, sessionId)
    generated_text = response['output']['text']
    sessionId = response['sessionId']
    print (generated_text)
    print (sessionId)
    
    return {
        'statusCode': 200,
        'body': {"question": query.strip(), "answer": generated_text.strip(), "sessionId":sessionId}
    }
    
