from package.PIL import Image
import re


class ImageProcessor:
    def __init__(self, client, bucket):
        self.bucket = bucket
        self.client = client

    def process(self, path, meta, key):
        if meta["process"] == "compress":
            self.__compress(path, meta["size"], key)
        elif meta["process"] == "resize":
            self.__generate_thumbnails(path, meta.get("sizes", "").split(";"), key)

    def __compress(self, path, size, key):
        print('Compressing image...')
        try:
            self.client.upload_file(
                ImageProcessor.resize_image(path, key, size),
                self.bucket,
                '{}/{}/{}'.format(path, size, key)
            )
            print('Compression over.')
        except Exception as e:
            print(e)
            raise e

    def __generate_thumbnails(self, path, sizes, key):
        print('Generating thumbnails ({})...'.format(",".join(sizes)))
        path_frags = key.rsplit("/", 1)
        file_path = path_frags[0]
        filename, ext = path_frags[1].split(".")

        if len(sizes) > 0:
            for size in sizes:
                self.client.upload_file(
                    ImageProcessor.resize_image(path, filename, size, ext),
                    self.bucket,
                    '{}/{}/{}.jpg'.format(file_path, size, filename)
                )
                print('- Generate {} thumbnail.'.format(size))

            print('Thumbnails generation over.')
        else:
            raise Exception("Sizes should be specified in metadata, none found.")

    @staticmethod
    def resize_image(path, filename, size, ext=None):
        dest_path = '/tmp/{}-{}'.format(size, filename)
        with Image.open(path) as image:
            #if image.mode in ("RGBA", "P"):
            #    image = image.convert("RGB")
            image.thumbnail(ImageProcessor.parse_size(size, image.size))
            image.save(dest_path, ext)
        return dest_path

    @staticmethod
    def parse_size(size, original_size):
        print('parsing {}...'.format(size))
        match = re.match(r"(?!autoxauto)(\d+|auto)x(\d+|auto)", size)
        if match:
            width = match[1] if match[1] != "auto" else original_size[0]*(int(match[2])/original_size[1])
            height = match[2] if match[2] != "auto" else original_size[1]*(int(match[1])/original_size[0])

            print('valid size format.'.format(size))
            return int(width), int(height)
        raise Exception('{} is not a valid size format'.format(size))
