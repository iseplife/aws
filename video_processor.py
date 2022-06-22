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

        temp_video = self.__compress(path, dest_ext or key_ext)
        self.client.upload_file(
            temp_video,
            self.bucket,
            f'{key_path}.{dest_ext or key_ext}'
        )

    @staticmethod
    def __compress(path, ext):
        print('[INFO] compressing video...')
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + "." + ext

        sp = subprocess.run(
            shlex.split(f"/opt/bin/ffmpeg -i {path} -vcodec h264 -crf 28 -preset faster -c:a aac -b:a 96k -movflags +faststart -vf scale=-2:720 -profile:v baseline -preset veryfast -fpsmax 50 -ar 44100 {out_filename}"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


        return out_filename