import tempfile
import subprocess
import shlex
import os

SIGNED_URL_TIMEOUT = 60

class VideoBundler:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, meta, key, dest_ext=None):
        compressed, max, key_id, folder = meta["vidpart"].split(",")

        temp_video = self.bundle(meta["vidpart"].split(","))

        print(f"[INFO] Bundling "+meta["vidpart"])
        self.client.upload_file(
            temp_video,
            self.bucket,
            key_id,
        )

    def bundle(self,vidpart):
        compressed, max, key_id, folder = vidpart

        segmentFile = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + ".txt"
        files = ""
        files_keys = []
        for i in range(int(max)):
            if len(files) != 0:
                files = files + "\n"

            key = f"{folder}/{i}.mp4"
            files_keys.append(key)
            s3_source_signed_url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=SIGNED_URL_TIMEOUT
            )

            files = f"{files}file '{s3_source_signed_url}'"

        print(f"[INFO] Files list : {files}")
        with open(segmentFile, "w+") as f:
            f.write(files)
        print('[INFO] Bundling video...')
        out_filename = tempfile._get_default_tempdir() + os.path.sep + next(tempfile._get_candidate_names()) + ".mp4"

        sp = subprocess.run(
            shlex.split(f"/opt/bin/ffmpeg -f concat -safe 0 -protocol_whitelist file,https,tcp,tls,crypto -i {segmentFile} -c copy {out_filename}"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True
        )
        print("[INFO] Bundling finished. Logs :")
        print("..."+sp.stdout.decode("utf-8").split("libpostproc")[1])

        print("[INFO] Deleting temporary files from S3...")
        delete_keys = {'Objects' : [{'Key' : k} for k in files_keys]}
        self.client.delete_objects(Bucket=self.bucket, Delete=delete_keys)
        deleted = '\n'.join(files_keys)
        print(f"[INFO] Deleted : {deleted}")

        return out_filename