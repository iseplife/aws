from PIL import Image
from re import match
from uuid import uuid4


class ImageProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext):
        # Temporary path where we'll save original object
        temp_path = '/tmp/{}{}'.format(uuid4(), key.replace("/", "-"))
        self.client.download_file(self.bucket, key, temp_path)

        if meta["process"] == "compress":
            self.__compress(temp_path, meta.get("sizes", "").split(";"), key, dest_ext)
        elif meta["process"] == "resize":
            self.__generate_thumbnails(temp_path, meta.get("sizes", "").split(";"), key, dest_ext)

    def __compress(self, path, sizes, key, dest_ext):
        print('[INFO] compressing image...')
        file_path, filename = key.rsplit("/", 1)

        if len(sizes) > 0:
            for size in sizes:
                self.client.upload_file(
                    ImageProcessor.resize_image(path, filename, size, dest_ext),
                    self.bucket,
                    '{}/{}/{}'.format(file_path, size, filename)
                )
                print('[INFO] generate {} thumbnail.'.format(size))

            self.client.delete_object(Bucket=self.bucket, Key=key)
            print('[INFO] compression over.')
        else:
            raise Exception("Sizes should be specified in metadata, none found.")

    def __generate_thumbnails(self, path, sizes, key, dest_ext):
        print('[INFO] generating thumbnails ({})...'.format(",".join(sizes)))
        file_path, filename = key.rsplit("/", 1)

        if len(sizes) > 0:
            for size in sizes:
                self.client.upload_file(
                    ImageProcessor.resize_image(path, filename, size, dest_ext),
                    self.bucket,
                    '{}/{}/{}'.format(file_path, size, filename)
                )
                print('[INFO] generate {} thumbnail.'.format(size))

            print('[INFO] thumbnails generation over.')
        else:
            raise Exception("Sizes should be specified in metadata, none found.")

    @staticmethod
    def resize_image(path, filename, size, ext=None):
        dest_path = '/tmp/{}-{}'.format(size, filename)
        with Image.open(path) as image:
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.thumbnail(ImageProcessor.parse_size(size, image.size))
            image.save(dest_path, ext)
        return dest_path

    @staticmethod
    def parse_size(size, original_size):
        print('[INFO] parsing {}...'.format(size))
        matched = match(r"(?!autoxauto)(\d+|auto)x(\d+|auto)", size)
        if matched:
            width = matched[1] if matched[1] != "auto" else original_size[0] * (int(matched[2]) / original_size[1])
            height = matched[2] if matched[2] != "auto" else original_size[1] * (int(matched[1]) / original_size[0])

            print('[INFO] valid size format.'.format(size))
            return int(width), int(height)
        raise Exception('{} is not a valid size format'.format(size))
