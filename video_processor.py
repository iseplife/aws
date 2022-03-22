import tempfile
import subprocess
import shlex
import os


class VideoProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext=None):
        key_path, key_ext = key.rsplit(".", 1)

        self.client.upload_file(
            self.__compress(path, dest_ext or key_ext),
            self.bucket,
            f'{key_path}.{dest_ext or key_ext}'
        )

        self.client.upload_file(
            self.__generate_thumbnail(path),
            self.bucket,
            f'{key_path}.jpg'
        )

    @staticmethod
    def __compress(path, ext):
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
            shlex.split(f'/opt/bin/ffmpeg -i {path} -ss 00:00:02 -vframes 1 -vf scale=-1:720 {out_filename}'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return out_filename
