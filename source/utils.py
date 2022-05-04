import itertools
from loguru import logger
from typing import (
    Optional,
    Tuple
)

import numpy as np
from PIL import Image


def resize_image(image: Image.Image, width: int = 256, height: int = 256) -> Optional[Image.Image]:
    # resize image keeping aspect ratio
    image.thumbnail((width, height), Image.ANTIALIAS)
    
    # calculate offset to make image in the center
    w, h = image.size
    if w < width:
        offset = ((width - w) // 2, 0)
    elif h < height:
        offset = (0, (height - h) // 2)
    else:
        offset = (0, 0)

    # add padding
    new_img = Image.new(image.mode, (width, height))
    new_img.paste(image, offset)
    return new_img


def byte2img(filepath: str, width: int = 256, height: int = 256) -> Optional[Image.Image]:
    """
        Convert from bytes to PNG

        @filepath: bytes filepath
    """
    try:
        with open(filepath, 'r') as f:
            arr = []
            for line in f:
                vals = line.split()
                del vals[0]
                arr.append(vals)
            
            max_len = max([len(vals) for vals in arr])
            
            new_arr = []
            for vals in arr:
                new_arr.append([val.replace('?', '0') for val in vals])
            
            for vals in new_arr:
                if '?' in vals:
                    print(vals)
            
            hexstring = ''.join(list(itertools.chain.from_iterable(new_arr)))
            
            byte_arr = bytearray.fromhex(hexstring)
            rem = len(byte_arr) % width
            byte_arr_len = len(byte_arr) - rem
            byte_arr = byte_arr[:byte_arr_len]
            byte_arr = np.asarray(byte_arr)
            np_arr = np.reshape(byte_arr, (len(byte_arr)//width, width))
            np_arr = np.uint8(np_arr)
            img = Image.fromarray(np_arr)

            if width and height:
                img = resize_image(img, width, height)

            return img
    except Exception as error:
        logger.error(f"Cant convert bytes to image: {error}")


if __name__ == "__main__":
    filepath = "file_in"
    img = byte2img(filepath)
    img.save("file_out")