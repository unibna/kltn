import itertools
from loguru import logger
import numpy as np
from PIL import Image
import math
import codecs
from collections import defaultdict  

def resize_image(image: Image.Image, width: int = 256, height: int = 256):
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


def byte2img(filepath: str, width: int = 256, height: int = 256):
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

            # if width and height:
            #     img = resize_image(img, width, height)

            return img
    except Exception as error:
        logger.error(f"Cant convert bytes to image: {error}")
        
def get_binary_dimension(filepath: str):
    """
        Get optimal width and height of binary

    Args:
        filepath (str): _description_
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
            
            raw_width = math.floor(math.sqrt(len(byte_arr)))
            
            raw_height = len(byte_arr) // raw_width
            
            return (raw_width, raw_height)
        
    except Exception as error:
        logger.error(f"Cant convert bytes to numpy array: {error}")
        
def byte2np(filepath: str):
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
            byte_arr = np.asarray(byte_arr)
            return byte_arr
        
    except Exception as error:
        logger.error(f"Cant convert bytes to numpy array: {error}")
        
def byte2np_square(filepath: str):
    """
        Convert from bytes to Numpy array

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
            
            raw_width = math.floor(math.sqrt(len(byte_arr)))
            
            rem = len(byte_arr) % raw_width
            byte_arr_len = len(byte_arr) - rem
            byte_arr = byte_arr[:byte_arr_len]
            byte_arr = np.asarray(byte_arr)
            np_arr = np.reshape(byte_arr, (len(byte_arr)// raw_width, raw_width))
            np_arr = np.uint8(np_arr)
            
            return np_arr
        
    except Exception as error:
        logger.error(f"Cant convert bytes to numpy array: {error}")
        
def byte2img_square(filepath, width=None, height=None):
    try: 
        img = Image.fromarray(byte2np_square(filepath))

        if width and height:
            img = resize_image(img, width, height)
            
        return img
    except Exception as error:
        logger.error(f"Cant convert bytes to numpy array: {error}")
    
# Take asm as input and parse the "align" location in binary
# Return a list of (sectionname, injectable address, length)    
def get_inject_locations(filepath):
    with codecs.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        results = []
        idx = 0
        numlines = len(lines)
        while idx < numlines:
            if lines[idx].find('align ') != -1:
                # print("Processing line", idx, lines[idx])
                section, address = (lines[idx].replace('\t', ' ').split(' ')[0]).split(':')
                # print(section, address)
                
                found = False
                while not found:
                    if idx + 1 < numlines:
                        nextline = lines[idx+1]
                        _, next_address = nextline.replace('\t', ' ').split(' ')[0].split(':')
                        if address != next_address:
                            found = True
                            length = int(next_address, 16) - int(address, 16)
                            results.append((section, int(address, 16), length))
                        idx += 1
                    else:
                        found = True
            idx += 1
            
        return results
    
def group_locations(locations):
    locations = sorted(locations, key=lambda x: x[2], reverse=True)
    d = defaultdict(list)
    
    for name, *v in locations:
        d[name].append(v)    
        
    return d
    

if __name__ == "__main__":
    bytepath = "./dataSample/0A32eTdBKayjCWhZqDOQ.bytes"
    asmpath = "./dataSample/0A32eTdBKayjCWhZqDOQ.asm"
    
    bytepath1 = "./dataSample/0ACDbR5M3ZhBJajygTuf.bytes"
    asmpath1 = "./dataSample/0ACDbR5M3ZhBJajygTuf.asm"
    
    testpath = "D:\\Big2015\\dataset-10-8-2\\8-2-0.0\\8.2.0.0-asm\\train-asm\\5\\GbTUXFYkMoafQSe1zN94.asm"
    # print(byte2np_square(testpath).shape)
    
    # img = byte2img_square(bytepath, 256, 256)
    # img.save(bytepath + "_resize.png")
    # img = byte2img_square(filepath)
    # img.save(filepath + ".png")
    locations = get_inject_locations(testpath)
    locations = group_locations(locations)
    
    print(locations)