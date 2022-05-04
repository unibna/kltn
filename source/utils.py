import itertools
import random
from loguru import logger
from typing import (
    Optional,
    Tuple,
    Dict,
    List
)
import os
import shutil
import math
import numpy as np
from PIL import Image
from configs import *


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
            print(type(hexstring))
            
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


def byte2img_square(filepath: str, width: int = 256, height: int = 256):
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
            
            raw_width = math.floor(math.sqrt(len(byte_arr)))
            
            rem = len(byte_arr) % raw_width
            byte_arr_len = len(byte_arr) - rem
            byte_arr = byte_arr[:byte_arr_len]
            byte_arr = np.asarray(byte_arr)
            np_arr = np.reshape(byte_arr, (len(byte_arr)// raw_width, raw_width))
            np_arr = np.uint8(np_arr)
            img = Image.fromarray(np_arr)

            if width and height:
                img = resize_image(img, width, height)

            return img
    except Exception as error:
        logger.error(f"Cant convert bytes to image: {error}")


def generate_folder_out_name(
        root_folder: str,
        splited_percent: SplitedPercent,
        folder_out_list: Dict[str, FolderOutMetadata] = folder_out_list,
) -> Dict[str, FolderOutMetadata]:
    # create root folder out
    folder_out = f"{root_folder}/{splited_percent.train}-{splited_percent.valid}-{splited_percent.test}"
    if not os.path.isdir(folder_out):
        os.mkdir(folder_out)

    # create folder out name
    for key in folder_out_list.keys():
        folder_out_list[key].filepath = f"{folder_out}/{key}"
        if not os.path.isdir(folder_out_list[key].filepath):
            os.mkdir(folder_out_list[key].filepath)

        for family in families:
            family_folder = f"""{folder_out_list[key].filepath}/{family}"""
            if not os.path.isdir(family_folder):
                os.mkdir(family_folder)

    return folder_out_list


def split_files(
        folder_in: str,
        splited_percent: SplitedPercent,
        folder_out_list: Dict[str, FolderOutMetadata],
        width: int = 256,
        height: int = 256,
) -> None:

    if not splited_percent.verify():
        logger.error(f"Invalid splited percentage")
        return

    for family in families:
        family_folder = f"{folder_in}/{family}"
        if not os.path.isdir(family_folder):
            logger.error(f"There is no folder {family_folder}")
            return
        
        # list files and get total file
        family_files = os.listdir(family_folder)
        random.shuffle(family_files)
        total_files = len(family_files)

        if splited_percent.train:
            no_train_files = int(total_files * splited_percent.train // 100)
        else:
            no_train_files = 0
        if splited_percent.valid and no_train_files:
            no_valid_files = int(total_files * splited_percent.valid // 100)
        else:
            no_test_files = 0
        if splited_percent.test and no_train_files and no_valid_files:
            no_test_files = int(total_files - no_train_files - no_valid_files)
        else:
            no_test_files = 0

        # verify
        if no_train_files + no_valid_files + no_test_files > total_files:
            logger.error(f"Unbalanced percentages - {splited_percent.get_percents()}")
            return

        if no_train_files > 0:
            logger.info(f"Handle train - {family}")
            for i in range(no_train_files):
                file = family_files.pop()
                fp = f"{folder_in}/{family}/{file}"
                try:
                    bytes_fp = f"""{folder_out_list["train-bytes"].filepath}/{family}/{file}"""
                    shutil.copy(fp, bytes_fp)
                except Exception as e:
                    logger.warning(f"Cant move file {fp} to {bytes_fp}: {e}")

                try:
                    img_fp = f"""{folder_out_list["train-img"].filepath}/{family}/{file}.png"""
                    img = byte2img_square(fp, width, height)
                    img.save(img_fp)
                except Exception as e:
                    logger.warning(f"Cant convert bytes to image: {fp} - {e}")
            logger.success(f"Handle train - {family} successfully - {no_train_files}/{total_files}")
        else:
            logger.warning("Empty train files")

        if no_valid_files > 0:
            logger.info(f"Handle valid - {family}")
            for i in range(no_valid_files):
                file = family_files.pop()
                fp = f"{folder_in}/{family}/{file}"
                try:
                    bytes_fp = f"""{folder_out_list["valid-bytes"].filepath}/{family}/{file}"""
                    shutil.copy(fp, bytes_fp)
                except Exception as e:
                    logger.warning(f"Cant move file {fp} to {bytes_fp}: {e}")

                try:
                    img_fp = f"""{folder_out_list["valid-img"].filepath}/{family}/{file}.png"""
                    img = byte2img_square(fp, width, height)
                    img.save(img_fp)
                except Exception as e:
                    logger.warning(f"Cant convert bytes to image: {fp} - {e}")
            logger.success(f"Handle valid - {family} successfully - {no_valid_files}/{total_files}")
        else:
            logger.warning("Empty valid files")

        if no_test_files > 0:
            logger.info(f"Handle test - {family}")
            for i in range(no_test_files):
                file = family_files.pop()
                fp = f"{folder_in}/{family}/{file}"
                try:
                    bytes_fp = f"""{folder_out_list["test-bytes"].filepath}/{family}/{file}"""
                    shutil.copy(fp, bytes_fp)
                except Exception as e:
                    logger.warning(f"Cant move file {fp} to {bytes_fp}: {e}")

                try:
                    img_fp = f"""{folder_out_list["test-img"].filepath}/{family}/{file}.png"""
                    img = byte2img_square(fp, width, height)
                    img.save(img_fp)
                except Exception as e:
                    logger.warning(f"Cant convert bytes to image: {fp} - {e}")
            logger.success(f"Handle test - {family} successfully - {no_test_files}/{total_files}")
        else:
            logger.warning("Empty test files")


def generate_dataset(
        folder_in: str,
        train: float,
        valid: float,
        test: float = 0.0,
) -> None:
    # initialize
    root_folder = os.path.dirname(os.path.realpath(folder_in))
    
    splited_percent = SplitedPercent(
        train=train,
        valid=valid,
        test=test,
    )

    folder_out_list = generate_folder_out_name(
        root_folder=root_folder,
        splited_percent=splited_percent,
    )
    split_files(
        folder_in=folder_in,
        folder_out_list=folder_out_list,
        splited_percent=splited_percent,
    )


def get_asm_files(
    folder_in: str,
    folder_out: str,
) -> None:

    if not os.path.isdir(folder_out):
        os.mkdir(folder_out)

    for family in families:
        family_folder_in = f"{folder_in}/{family}"
        family_folder_out = f"{folder_out}/{family}"

        if not os.path.isdir(family_folder_out):
            os.mkdir(family_folder_out)

        files = os.listdir(family_folder_in)
        for file in files:
            file = file.replace(".bytes", ".asm")
            src = f"/home/unibna/thesis/source/dataset/train-asm/{file}"
            dst = f"{family_folder_out}/{file}"
            shutil.copy(src, dst)


def get_test_sample(train_folder, family=3):
    train_files = os.listdir(f"{train_folder}/train-img/{family}")
    valid_files = os.listdir(f"{train_folder}/valid-img/{family}")
    test_files = os.listdir(f"{train_folder}/test-img/{family}")
    pool_files = os.listdir(f"/home/unibna/thesis/source/dataset/train-labled/{family}")

    for file in pool_files:
        file = file.replace(".bytes", ".png")
        if file in train_files:
            continue
        if file in valid_files:
            continue
        if file in test_files:
            continue
        return f"/home/unibna/thesis/source/dataset/train-labled/{family}/{file.replace('.png', '.bytes')}"
