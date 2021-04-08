# -*- coding: utf-8 -*-
"""Fine Tuning ResNet-50 on Clothes.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17p2GEbK_Dt88SPughzoJ_jKj4ntyI4h8
"""
import os
import tensorflow as tf
from tensorflow.keras import callbacks
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Flatten, Input, BatchNormalization, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2

DATADIR = 'C:\\Users\\Vargha\\Desktop\\top'
CATEGORIES = ['hawaei', 'picture', 'plaid', 'plain', 'spotted', 'stripe', 'zigzag']

train = tf.keras.preprocessing.image_dataset_from_directory(DATADIR,
                                                            label_mode="categorical",
                                                            # class_names=CATEGORIES,
                                                            validation_split=0.2,
                                                            subset='training',
                                                            batch_size=32,
                                                            seed=42,
                                                            image_size=(224, 224)
                                                            )

val = tf.keras.preprocessing.image_dataset_from_directory(DATADIR,
                                                          label_mode="categorical",
                                                          # class_names=CATEGORIES,
                                                          validation_split=0.2,
                                                          subset='validation',
                                                          batch_size=32,
                                                          seed=42,
                                                          image_size=(224, 224)
                                                          )

inputs = Input((224, 224, 3))
base_model = MobileNetV2(weights='imagenet', include_top=False, input_tensor=inputs)
for layer in base_model.layers[:145]:
    layer.trainable = False
for i, layer in enumerate(base_model.layers):
    print(i, layer.name, "-", layer.trainable)
x = Flatten()(base_model.output)
x = BatchNormalization()(x)
x = Dense(256, activation='relu')(x)
x = Dropout(0.5)(x)
x = BatchNormalization()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)
x = BatchNormalization()(x)
x = Dense(64, activation='relu')(x)
x = Dropout(0.5)(x)
x = BatchNormalization()(x)
outputs = Dense(7, activation='softmax', kernel_initializer='he_normal', kernel_regularizer=l2(1e-2))(x)

model = Model(inputs=base_model.input, outputs=outputs)

model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])

model.summary()

model_checkpoint = callbacks.ModelCheckpoint(os.path.abspath('transfer_learning_MobileNetV2.h5'), monitor='val_accuracy',
                                             verbose=1, save_best_only=True)

tensorboard = callbacks.TensorBoard(os.path.abspath('transfer_learning_logs_MobileNetV2'))

lr_reducer = callbacks.ReduceLROnPlateau(monitor='val_accuracy',
                                         patience=5,
                                         factor=0.1,
                                         verbose=1)

CSVlogger = callbacks.CSVLogger(os.path.abspath('training_mobileNetV2.log'))

early_stopping = callbacks.EarlyStopping(monitor='val_loss', patience=35, verbose=1)

Callbacks = [model_checkpoint, lr_reducer, CSVlogger, tensorboard, early_stopping]

history = model.fit(train, batch_size=32, epochs=400, validation_data=val, verbose=1, callbacks=Callbacks)