import os
from loguru import logger

import cv2
import numpy as np
from keras.models import load_model

import utils


def predict(
    model_fp: str,
    bytes_fp: str = None,
    image_fp: str = None,
    img_shape = [1, 256, 256, 3]
):
    # load model
    model = load_model(model_fp)
    model.compile(
        loss='categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy'],
    )

    if bytes_fp and image_fp:
        logger.error('bytes_fp and image_fp are not passed at the same time')
        return

    if bytes_fp:
        img = utils.byte2img_square(bytes_fp)
        if not img:
            logger.error(f"Cant convert bytes to image")
            return
        image_fp = f"{bytes_fp}.png"
        img.save(image_fp)
    
    if not image_fp:
        logger.error(f"No image to predict")
        return

    img = cv2.imread(image_fp)
    img_np = np.reshape(img, img_shape)

    # predict
    try:
        res = model.predict(img_np)
    except Exception as e:
        logger.error(f"Cant predict {image_fp}")
        res = [[]]

    return res


if __name__ == "__main__":
    model_fp = "./model/2022-04-25 17_44_17.889099_checkpoint.h5"
    # bytes_fp = utils.get_test_sample("./dataset/8-2-0.0")
    bytes_fp = ""
    res = predict(model_fp=model_fp, bytes_fp=bytes_fp)
    print(res)
