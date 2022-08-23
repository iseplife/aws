import tempfile
import subprocess
import shlex
import os


class VideoSplitter:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext=None):
        key_path, key_ext = key.rsplit(".", 1)

        seg_folder = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + os.path.sep + "segments"

        os.makedirs(seg_folder)

        print("[INFO] Splitting video...")
        sp = subprocess.run(
            shlex.split(f"/opt/bin/ffmpeg -i {path} -c copy -map 0 -segment_time 00:00:20 -reset_timestamps 1 -f segment {seg_folder}/%d.mp4"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True
        )
        print("[INFO] Splitting finished. Logs :")
        print("..."+sp.stdout.decode("utf-8").split("libpostproc")[1])

        print("[INFO] Sending files to compression :")
        files = os.listdir(seg_folder)
        filesLength = len(files)
        for file in files:
            print(f"[INFO] File detected : {file}, sending.")
            self.client.upload_file(
                f"{seg_folder}{os.path.sep}{file}",
                self.bucket,
                f'tmp/{key_path}/{file}',
                ExtraArgs={
                    'Metadata': {
                        'vidpart': f"uncompressed,{filesLength},{key},tmp/{key_path}"
                    }
                }
            )
        print("[INFO] Deleting original...")
        self.client.delete_object(Bucket=self.bucket, Key=key)
        print("[INFO] Job done.")
        return False