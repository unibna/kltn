
import os
import time
import datetime
import numpy as np
from PIL import Image
import cv2

import keras.preprocessing
from keras.models import Sequential, load_model
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense

import utils


class MalwareConvNet:

    # data config
    img_size = (256, 256, 3)
    no_train_samples = 1390
    no_test_samples = 83

    # model config
    batch_size = 32
    epochs = 32
    input_shape = (256, 256, 3)
    pool_size = (2, 2)
    num_classes = 9

    def generate_data(self, train_folder: str, test_folder: str):
        image_generator = ImageDataGenerator(rescale=1/255, validation_split=0.2)    

        self.train_generator = image_generator.flow_from_directory(batch_size=self.batch_size,
                                                        directory=train_folder,
                                                        shuffle=True,
                                                        target_size=(256, 256), 
                                                        subset="training",
                                                        class_mode='categorical')
        
        self.test_generator = image_generator.flow_from_directory(batch_size=self.batch_size,
                                                        directory=test_folder,
                                                        shuffle=True,
                                                        target_size=(256, 256), 
                                                        subset="validation",
                                                        class_mode='categorical')

    def build_model(self, **kwargs):
        self.model = Sequential()

        self.model.add(Conv2D(32, (3, 3), input_shape=self.input_shape))
        self.model.add(Activation('relu'))
        self.model.add(MaxPooling2D(pool_size=self.pool_size))

        self.model.add(Conv2D(64, (3, 3)))
        self.model.add(Activation('relu'))
        self.model.add(MaxPooling2D(pool_size=self.pool_size))

        self.model.add(Conv2D(64, (3, 3)))
        self.model.add(Activation('relu'))
        self.model.add(MaxPooling2D(pool_size=self.pool_size))

        self.model.add(Flatten())
        self.model.add(Dense(64))
        self.model.add(Activation('relu'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(self.num_classes))
        self.model.add(Activation('softmax'))

        self.model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy'],
        )

    def load_model(self, model_fp: str):
        self.model = load_model(model_fp)
        self.model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy'],
        )

    def train(self, model_folder: str = None):
        steps_per_epoch = self.no_train_s // self.batch_size
        test_steps = self.no_test_samples // self.batch_size
        model_checkpoint_fp = f"{model_folder}/{datetime.datetime.now()}_checkpoint.h5"
        print(f"Store in {model_checkpoint_fp}")

        self.model.fit(
            self.train_generator,
            steps_per_epoch=steps_per_epoch,
            epochs=self.epochs,
            validation_data=self.test_generator,
            validation_steps=test_steps,
        )
        self.model.save(model_checkpoint_fp)

    def run(self, **kwargs):
        train_folder = kwargs.get("train_folder", "")
        test_folder = kwargs.get("test_folder", "")
        model_folder = kwargs.get("model_folder", "")

        self.generate_data(train_folder, test_folder)
        self.build_model()
        self.train(model_folder)

mal_model = MalwareConvNet()