import tempfile
import subprocess
import shlex
import os

SIGNED_URL_TIMEOUT = 60


class VideoProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext=None):
        key_path, key_ext = key.rsplit(".", 1)

        s3_source_signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=SIGNED_URL_TIMEOUT
        )

        self.client.upload_file(
            self.__compress(s3_source_signed_url, dest_ext or key_ext),
            self.bucket,
            f'{key_path}.{dest_ext or key_ext}'
        )

        self.client.upload_file(
            self.__generate_thumbnail(path),
            self.bucket,
            f'{key_path}.jpg'
        )

    @staticmethod
    def __compress(self, path, ext):
        print('[INFO] compressing video...')
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + "." + ext

        sp = subprocess.run(
            shlex.split(f"/opt/bin/ffmpeg -i {path} -vf scale=-1:720 -vcodec h264 -acodec aac {out_filename}"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
       
        return out_filename

    @staticmethod
    def __generate_thumbnail(path):
        print('[INFO] generating video thumbnail...')
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + ".jpg"
        
        sp = subprocess.run(
            hlex.split(f'/opt/bin/ffmpeg -i {path} -ss 00:00:02 -vframes 1 -vf scale=-1:720 {out_filename}'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return out_filename
