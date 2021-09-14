from PIL import Image
from re import match


class ImageProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key, dest_ext):
        if meta["process"] == "compress":
            self.__compress(path, meta.get("sizes", "").split(";"), key, dest_ext)
        elif meta["process"] == "resize":
            self.__generate_thumbnails(path, meta.get("sizes", "").split(";"), key, dest_ext)

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
                print('- Generate {} thumbnail.'.format(size))

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
                print('- Generate {} thumbnail.'.format(size))

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
            width = match[1] if match[1] != "auto" else original_size[0] * (int(match[2]) / original_size[1])
            height = match[2] if match[2] != "auto" else original_size[1] * (int(match[1]) / original_size[0])

            print('[INFO] valid size format.'.format(size))
            return int(width), int(height)
        raise Exception('{} is not a valid size format'.format(size))
