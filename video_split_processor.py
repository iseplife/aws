import boto3
import json

class VideoSplitProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client
        
    def process(self, path, meta, key, dest_ext=None):
        lambda_client = boto3.client('lambda')
        with open('video_splitter.py') as f:
            lines = f.readlines()
            lambda_payload = json.dumps({"path":path, "meta": meta, "key": key, "videosplitter_code": "\n".join(lines), "bucket": self.bucket})
            lambda_client.invoke(FunctionName='arn:aws:lambda:eu-west-3:982399186209:function:PROD-iseplifeVideoSplitting', 
                                InvocationType='Event',
                                Payload=lambda_payload)
        return False