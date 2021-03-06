import tensorflow as tf
from tensorflow.keras import callbacks
from tensorflow.keras.layers import Dense, Input, Conv2D, AveragePooling2D, add, Flatten, BatchNormalization, \
    Activation
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
import os
import cv2
import imgaug as iaa

DATADIR = '/content/data'
path = '/content/data'
target = '/content/data'
CATEGORIES = ['hawaei', 'picture', 'plaid', 'plain', 'spotted', 'stripe', 'zigzag']

for i in range(1, 5):
    for cat in CATEGORIES:
        for image in (os.listdir(os.path.join(path, cat))):
            img = cv2.imread(os.path.join(path, cat, image))
            w = 224
            h = 224
            if i == 1:
                seq = iaa.Sequential([
                    # 1
                    iaa.PadToFixedSize(width=w + 100, height=h + 100),
                    iaa.Fliplr(1.0),
                    iaa.Rotate(rotate=(-30, 30)),
                    iaa.ScaleX(scale=(0.8, 1.0)),
                    iaa.MultiplyHue((0.5, 1.5)),
                ])
                images_aug = seq(image=img)
                image_split = image.split(sep='.')
                image_name = image_split[0] + str(i) + '.' + image_split[1]
                cv2.imwrite(os.path.join(target, cat, '{image_name}.jpg'.format(image_name=image_name)), images_aug)
            if i == 2:
                seq = iaa.Sequential([
                    iaa.Crop(percent=0.1),
                    iaa.ScaleX(scale=(0.8, 0.9)),
                    iaa.Fliplr(1.0),
                    iaa.ChangeColorTemperature((1100, 10000)),
                    iaa.MultiplyHue((0.5, 1.5))
                ])
                images_aug = seq(image=img)
                image_split = image.split(sep='.')
                image_name = image_split[0] + str(i) + '.' + image_split[1]
                cv2.imwrite(os.path.join(target, cat, '{image_name}.jpg'.format(image_name=image_name)), images_aug)
#             if i == 3:
#                 seq = iaa.Sequential([
#                     iaa.PadToFixedSize(width=w + 200, height=200 + h),
#                     iaa.Affine((1.1, 1.3)),
#                     iaa.Rotate((-5, 5)),
#                     iaa.TranslateX(percent=0.04),
#                     iaa.ShearX((-15, 15))
#                 ])
#                 images_aug = seq(image=img)
#                 image_split = image.split(sep='.')
#                 image_name = image_split[0] + str(i) + '.' + image_split[1]
#                 cv2.imwrite(os.path.join(target, cat, '{image_name}.jpg'.format(image_name=image_name)), images_aug)

# if i == 4:
#     seq = iaa.Sequential([
#         iaa.PadToFixedSize(width=w + 100, height=h + 100),
#         iaa.Fliplr(1.0),
#         iaa.Crop(percent=0.02),
#         iaa.TranslateX(percent=[-0.1, 0.1]),
#         iaa.ChangeColorTemperature((6000, 11000))
#     ])
#     images_aug = seq(image=img)
#     image_split = image.split(sep='.')
#     image_name = image_split[0] + str(i) + '.' + image_split[1]
#     cv2.imwrite(os.path.join(target, cat, image_name, '.jpg'), images_aug)

# datagen = ImageDataGenerator(
#     rotation_range=30,
#     width_shift_range=[0.2,0.3],
#     height_shift_range=[0.2,0.3],
#     shear_range=0.2,
#     horizontal_flip=True)

# for cat in CATEGORIES:
#     for filename in (os.listdir(os.path.join(path, cat))):
#         img = Image.open(os.path.join(path, cat, filename))
#         x = img.convert('RGB')
#         x = img_to_array(img)
#         x = x.reshape((1,) + x.shape)

#         i = 0
#         for batch in datagen.flow(x, batch_size=1,
#                                   save_to_dir=os.path.join(target, cat), save_prefix='AUG',
#                                   save_format='png'):
#             i += 1
#             if i > 20:
#                 break

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

num_stacks = 3
num_blocks = 3
filter_sizes = [16, 32, 64]


def res_layer(inputs, filters, strides=1, kernel_size=3, activation='relu', batch_normalization=True):
    x = Conv2D(filters=filters, kernel_size=kernel_size, strides=strides, padding='same',
               kernel_initializer='he_normal',
               kernel_regularizer=l2(1e-3))(inputs)
    if batch_normalization:
        x = BatchNormalization()(x)
    if activation is not None:
        x = Activation(activation)(x)
    return x


def stack_layer(x, num_stacks, num_blocks, filters_list):
    for stack in range(num_stacks):
        for blocks in range(num_blocks):
            if stack != 0 and blocks == 0:
                strides = 2
            else:
                strides = 1

            y = res_layer(x, filters_list[stack], strides=strides)
            y = res_layer(y, filters_list[stack], strides=1, activation=None)

            if stack != 0 and blocks == 0:
                x = res_layer(x, filters_list[stack], kernel_size=1, strides=2, activation=None,
                              batch_normalization=False)
            x = add([x, y])
            x = Activation('relu')(x)
    return x


inputs = Input((224, 224, 3))
x = res_layer(inputs, filters=filter_sizes[0])
x = BatchNormalization()(x)
x = stack_layer(x, num_stacks, num_blocks, filter_sizes)
x = BatchNormalization()(x)
x = AveragePooling2D(8)(x)
x = BatchNormalization()(x)
x = Flatten()(x)
x = BatchNormalization()(x)
outputs = Dense(7, activation='softmax', kernel_initializer='he_normal', kernel_regularizer=l2(1e-2))(x)

model = Model(inputs, outputs)

model.summary()

model_checkpoint = callbacks.ModelCheckpoint('/content/drive/MyDrive/model_checkpoint(10_1).h5', monitor='val_accuracy',
                                             verbose=1, save_best_only=True)

tensorboard = callbacks.TensorBoard('/content/drive/MyDrive/logs1')

lr_reducer = callbacks.ReduceLROnPlateau(monitor='val_accuracy',
                                         patience=5,
                                         factor=0.1,
                                         verbose=1)

CSVlogger = callbacks.CSVLogger('/content/drive/MyDrive/training(10).log')

early_stopping = callbacks.EarlyStopping(monitor='val_loss', patience=35, verbose=1)

Callbacks = [model_checkpoint, lr_reducer, CSVlogger, tensorboard, early_stopping]

# new_model = load_model(os.path.abspath('ResNet on Clothes.h5'))
model.compile(loss="categorical_crossentropy", optimizer=Adam(0.001), metrics=["accuracy"])

model.fit(train, batch_size=32, epochs=400, validation_data=val, verbose=1)


#Predictions

# img_path = ('C:\\Users\\Vargha\\Desktop\\jack-and-jones_244124_12181602_WHISPER-WHITE_20201215T092917_01.jpg')
# img = image.load_img(img_path, target_size=(224, 224))
# img_array = image.img_to_array(img)
# img_batch = np.expand_dims(img_array, axis=0)
#
# img_preprocessed = preprocess_input(img_batch)
# classes = np.argmax(new_model.predict(img_preprocessed))
# classes = classes.astype(np.int)
# i = 0
# for name in CATEGORIES:
#     if classes == i:
#         print('Class:', name)
#     i += 1
#
# prediction = new_model.predict(img_preprocessed)
# print(prediction)


# print(decode_predictions(prediction, top=3)[0])