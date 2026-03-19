from dotenv import load_dotenv
from imagekitio import ImageKit
import os

load_dotenv()

imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    # password=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    # base_url=os.getenv("IMAGEKIT_URL"),
)

