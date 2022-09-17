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

        try:
            if meta["process"] == "overwrite":
                self.__overwrite(temp_path, meta.get("size", ""), key, dest_ext)
            if meta["process"] == "compress":
                self.__compress(temp_path, meta.get("sizes", "").split(";"), key, dest_ext)
            elif meta["process"] == "resize":
                self.__generate_thumbnails(temp_path, meta.get("sizes", "").split(";"), key, dest_ext)
        finally:
            os.remove(temp_path)
        
        return True

    def __overwrite(self, path, size, key, dest_ext):
        print('[INFO] overwriting image...')
        file_path, filename = key.rsplit("/", 1)

        computed_file_path = ImageProcessor.resize_image(path, filename, size, dest_ext)
        try:
            self.client.upload_file(
                computed_file_path,
                self.bucket,
                key
            )
        finally:
            os.remove(computed_file_path)
        
        print('[INFO] overwrite {} thumbnail.'.format(size))
        print('[INFO] compression over.')

    def __compress(self, path, sizes, key, dest_ext):
        print('[INFO] compressing image...')
        file_path, filename = key.rsplit("/", 1)

        if len(sizes) > 0:
            for size in sizes:
                computed_file_path = ImageProcessor.resize_image(path, filename, size, dest_ext)
                try:
                    self.client.upload_file(
                        computed_file_path,
                        self.bucket,
                        '{}/{}/{}'.format(file_path, size.split("/")[0], filename)
                    )
                finally:
                    os.remove(computed_file_path)
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
                computed_file_path = ImageProcessor.resize_image(path, filename, size, dest_ext)
                try:
                    self.client.upload_file(
                        computed_file_path,
                        self.bucket,
                        '{}/{}/{}'.format(file_path, size.split("/")[0], filename)
                    )
                finally:
                    os.remove(computed_file_path)
                print('[INFO] generate {} thumbnail.'.format(size))

            print('[INFO] thumbnails generation over.')
        else:
            raise Exception("Sizes should be specified in metadata, none found.")

    @staticmethod
    def resize_image(path, filename, size, extension='webp'):
        dest_path = '/tmp/{}-{}'.format(size.split("/")[0], filename)
        with Image.open(path) as image:
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            parsed = ImageProcessor.parse_size(size, image.size)
            
            image.thumbnail([parsed[0], parsed[1]])
            image.save(dest_path, extension, optimize = True, quality = parsed[2])
        return dest_path

    @staticmethod
    def parse_size(size, original_size):
        print('[INFO] parsing {}...'.format(size))
        matched = match(r"(?!autoxauto)(\d+|auto)x(\d+|auto)/?(\d+)?", size)
        if matched:
            wantedWidth = matched[1]
            wantedHeight = matched[2]
            if wantedWidth != "auto" and int(wantedWidth) > original_size[0]:
                wantedWidth = original_size[0]
            if wantedHeight != "auto" and int(wantedHeight) > original_size[1]:
                wantedHeight = original_size[1]

            width = wantedWidth if wantedWidth != "auto" else original_size[0] * (int(wantedHeight) / original_size[1])
            height = wantedHeight if wantedHeight != "auto" else original_size[1] * (int(wantedWidth) / original_size[0])

            quality = matched[3] or 80

            print('[INFO] valid size format.'.format(size))
            return int(width), int(height), int(quality)
        raise Exception('{} is not a valid size format'.format(size))
