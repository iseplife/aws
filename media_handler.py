from image_processor import ImageProcessor
from video_processor import VideoProcessor
import package.boto3 as boto3
import package.psycopg2 as psycopg2
import uuid
import os

s3_client = boto3.client('s3')
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD']
)


def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            if obj["Metadata"].get("process", 0):
                # Mark media as being processed
                cur = conn.cursor()
                cur.execute("UPDATE media (status) VALUES ('PROCESSING') WHERE name=%s", key)
                conn.commit()

                # Temporary path where we'll save original object
                original_obj_path = '/tmp/{}{}'.format(uuid.uuid4(), key.replace("/", "-"))
                s3_client.download_file(bucket, key, original_obj_path)

                print('Processing object {}...'.format(key))

                # Videos are all stored in 'vid/' folder in S3 so if this part is in the key (pathname) then it is a video
                # otherwise we considered it is a image. Documents are not processed as they don't have the 'process' metadata (yet ?)
                if "vid/" in key:
                    processor = VideoProcessor(s3_client, bucket)
                else:
                    processor = ImageProcessor(s3_client, bucket)

                processor.process(original_obj_path, obj["Metadata"], key, obj["Metadata"].get("dest_ext", None))

                try:
                    # Mark media as ready after processing
                    cur = conn.cursor()
                    cur.execute("UPDATE media (status) VALUES ('READY') WHERE name=%s", key)
                    conn.commit()
                except Exception as e:
                    print("Error updating media status in database (name: {})".format(key))
                    print(e)
                    raise e
                finally:
                    # Close communication with database
                    cur.close()
                    conn.close()

                return {
                    'statusCode': 200,
                    'body': "Process executed successfully"
                }
        except Exception as e:
            print(e)
            print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
            raise e


