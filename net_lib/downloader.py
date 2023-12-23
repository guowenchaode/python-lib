import flash
from flash.core.data.utils import download_data
from flash.image import ImageClassificationData, ImageClassifier


# 1. Download the data

pytorch_dir = f"D:\Git\github\pytorch\data"


def download_pytorch_data(
    url="https://pl-flash-data.s3.amazonaws.com/hymenoptera_data.zip",
):
    download_data(url, pytorch_dir)


if __name__ == "__main__":
    download_pytorch_data()