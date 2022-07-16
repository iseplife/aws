import psycopg2
from psycopg2 import OperationalError
from boto3 import client
from os import environ as env


from image_processor import ImageProcessor
from video_processor import VideoProcessor

SIGNED_URL_TIMEOUT = 60
s3_client = client('s3')

def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        try:
            print("[INFO] getting object...")
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            if obj["Metadata"].get("process", 0):
                conn = psycopg2.connect(
                    host=env['DB_HOST'],
                    port=env['DB_PORT'],
                    database=env['DB_NAME'],
                    user=env['DB_USER'],
                    password=env['DB_PASSWORD']
                )
                try:
                    # Mark media as being processed
                    cur = conn.cursor()
                    cur.execute("UPDATE media SET status ='PROCESSING' WHERE name=%s", (key,))
                    conn.commit()

                    try:
                        s3_source_signed_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket, 'Key': key},
                            ExpiresIn=SIGNED_URL_TIMEOUT
                        )

                        # Videos are all stored in 'vid/' folder in S3 so if this part is in the key (pathname) then it is a video
                        # otherwise we considered it is a image. Documents are not processed as they don't have the 'process' metadata (yet ?)
                        if "vid/" in key:
                            processor = VideoProcessor(s3_client, bucket)
                        else:
                            processor = ImageProcessor(s3_client, bucket)

                        print('[INFO] processing object {}...'.format(key))
                        processor.process(
                            s3_source_signed_url,
                            obj["Metadata"],
                            key,
                            obj["Metadata"].get("dest_ext", None)
                        )
                    
                        # Mark media as ready after processing
                        cur = conn.cursor()
                        cur.execute("UPDATE media SET status = 'READY' WHERE name=%s", (key,))
                        conn.commit()
                    except Exception as e:
                        print('Error raised when trying to process object {} from bucket {}.'.format(key, bucket))
                        cur.execute("UPDATE media SET status = 'ERROR' WHERE name=%s", (key,))
                        conn.commit()
                        print(e)
                        raise e
                except OperationalError as e:
                    print("OperationalError with psycopg when updating media status in database (name: {})".format(key))
                    print(e)
                    raise e
                finally:
                    # We do not close connection to database as the same container can be reused for a following object
                    # as the conn variable is not defined in the function, its value is "frozen"
                    cur.close()

                return {
                    'statusCode': 200,
                    'body': "Process executed successfully"
                }
            else:
                print(f"[INFO] object {key} skipped (no process metadata)")
        except Exception as e:
            print('Error raised when trying to process object {} from bucket {}.'.format(key, bucket))
            cur.execute("UPDATE media SET status = 'ERROR' WHERE name=%s", (key,))
            conn.commit()
            print(e)
            raise e


