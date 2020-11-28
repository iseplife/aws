from image_processor import ImageProcessor
from video_processor import VideoProcessor
import package.boto3 as boto3
import uuid

s3_client = boto3.client('s3')


def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            if obj["Metadata"].get("process", 0):
                # Temporary path where we'll save original object
                original_obj_path = '/tmp/{}{}'.format(uuid.uuid4(), key.replace("/", "-"))
                s3_client.download_file(bucket, key, original_obj_path)

                print('Processing object {}...'.format(key))

                # Videos are all stored in 'vid/' folder in S3 so if this part is in the key (pathname) then it is a video
                # otherwise we considered it is a image. Documents are not processed as they don't have the 'process' metadata (yet ?)
                if "vid/" in key:
                    processor = VideoProcessor(s3_client, bucket,)
                else:
                    processor = ImageProcessor(s3_client, bucket)

                processor.process(original_obj_path, obj["Metadata"], key, obj["Metadata"].get("dest_ext", None))
                return {
                    'statusCode': 200,
                    'body': "Process executed successfully"
                }
        except Exception as e:
            print(e)
            print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
            raise e


