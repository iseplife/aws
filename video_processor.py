import tempfile
import os
from package import ffmpeg


class VideoProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext=None):
        key_path, key_ext = key.rsplit(".", 1)

        self.client.upload_file(
            self.__compress(path, dest_ext or key_ext),
            self.bucket,
            "{}.{}".format(key_path, dest_ext or key_ext)
        )

        self.client.upload_file(
            self.__generate_thumbnail(path),
            self.bucket,
            key_path+".jpg"
        )

    @staticmethod
    def __compress(self, path, ext):
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + "." + ext

        media = ffmpeg.input(path)
        audio = media.audio
        video = media.video.filter("scale", -1, 720)

        ffmpeg.output(video, audio, out_filename, vcodec='h264', acodec='aac').run()

        return tempfile._get_default_tempdir() + os.path.sep + out_filename

    @staticmethod
    def __generate_thumbnail(path):
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + ".jpg"
        (
            ffmpeg
                .input(path, ss=2)
                .filter('scale', -1, 720)
                .output(out_filename, vframes=1)
                .run()
        )
        return out_filename
