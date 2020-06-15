import numpy as np
import matplotlib.pyplot as plt
import os
import time
import pickle
import pandas as pd
import pprofile

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions

from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score

""" Task4 - Classify image similar in taste 
    
    Strategy: Extract features using transfer learning and ResNet50, make classifier therafter.
"""

# Random states
random_state = 4
np.random.seed(random_state)


def piece_together_feature_files():
    train_features = pd.DataFrame()
    for i in range(10):
        current_batch = pd.read_csv(("ResNet50_features/x_train_Resnet50_avg_pool_" + str(i) + ".csv")).iloc[:, 1:]
        train_features = train_features.append(current_batch)
        print(f"Batch {i} appended. Size: {current_batch.shape}")
        del current_batch
    current_batch = pd.read_csv("ResNet50_features/x_train_Resnet50_avg_pool_end.csv").iloc[:, 1:]
    train_features = train_features.append(current_batch)
    print(f"Batch end appended. Size: {current_batch.shape}")
    del current_batch
    train_features.to_csv("ResNet50_features/x_train_Resnet50_avg_pool_total.csv")
    return train_features


def piece_together_feature_files_test():
    test_features = pd.DataFrame()
    for i in range(10):
        if i == 0:
            continue
        current_batch = pd.read_csv(("ResNet50_features/x_train_Resnet50_avg_pool_" + str(i) + ".csv")).iloc[:, 1:]
        test_features = test_features.append(current_batch)
        del current_batch
        print(f"Batch {i} appended.")
    current_batch = pd.read_csv("ResNet50_features/x_train_Resnet50_avg_pool_end.csv").iloc[:, 1:]
    test_features = test_features.append(current_batch)
    del current_batch
    test_features.to_csv("ResNet50_features/x_test_Resnet50_avg_pool_total.csv")
    return test_features


def extract_features_from_images():
    # Check if images have already been extracted
    try:
        feature_list = pickle.load(open("image_features_ResNet50_avg_pooling.p", "rb"))
        image_name_list = pickle.load(open("image_list_ResNet50_avg_pooling.p", "rb"))
        print("[extract_features_from_images] Successfully loaded preexisting ResNet50 features.")
        return feature_list, image_name_list
    except FileNotFoundError:
        # Extract features from images
        print("[extract_features_from_images] Extracting ResNet50 features...")
        # Load images from directory
        image_directory = "food"
        image_list = os.listdir(image_directory)
        feature_list = []
        image_name_list = []

        # Load ResNet50
        model_notop = ResNet50(weights='imagenet', include_top=False, pooling='avg')

        # Extract features from images
        start = time.time()
        for image_name in image_list:
            try:
                # Load image and preprocess
                img = image.load_img(os.path.join(image_directory, image_name), target_size=(224, 224))
                x = image.img_to_array(img)
                x = np.expand_dims(x, axis=0)
                x = preprocess_input(x)

                # Compute features
                features = model_notop.predict(x)
                feature_list.append(features)
                image_name_list.append(image_name)

            # handles the odd operating system helper files in the folder TODO make this safer
            except:
                print(f"[extract_features_from_images] ERROR: with image name {image_name}")

        print(f"[extract_features_from_images] Processing images took: {'%.2f' % (time.time() - start)} seconds")

        # File I/O
        pickle.dump(feature_list, open("image_features_ResNet50_avg_pooling.p", "wb"))
        pickle.dump(image_name_list, open("image_list_ResNet50_avg_pooling.p", "wb"))
        feature_list = pickle.load(open("image_features_ResNet50_avg_pooling.p", "rb"))
        image_name_list = pickle.load(open("image_list_ResNet50_avg_pooling.p", "rb"))

        return feature_list, image_name_list


def create_balanced_training_data(x_input):
    # Create random indexes
    random_indexes = np.random.choice(x_input.index,
                                      size=int(len(x_input.index) / 2),
                                      replace=False)
    # switch image B and C for half the training set randomly to have an balanced dataset of 1 and 0 classifications
    x_input_balanced = x_input
    x_input_balanced.iloc[random_indexes, 2048:4096] = x_input.iloc[random_indexes, 4096:]
    x_input_balanced.iloc[random_indexes, 4096:] = x_input.iloc[random_indexes, 2048:4096]
    labels = pd.DataFrame(np.ones((len(x_input.index), 1)))
    labels.iloc[random_indexes] = 0

    return x_input_balanced, labels


def create_feature_vectors():
    # Try to load preexisting data
    # try:
    #     train_features = pd.read_csv("x_train_Resnet50_avg_pool_balanced_10percent.csv").iloc[:, 1:]
    #     test_features = pd.read_csv("x_test_Resnet50_avg_pool.csv").iloc[:, 1:]
    #     test_features = pd.DataFrame()
    #     train_labels = pd.read_csv("y_train_Resnet50_avg_pool_balanced_10percent.csv").iloc[:, 1:]
    #     print("[create_feature_vectors] Loaded preexisting feature vectors.")
    #     return train_features, train_labels, test_features
    # except FileNotFoundError:
    #     print("[create_feature_vectors] Creating feature vectors...")
    # Prepare directory
    dir_name = "ResNet50_features_balanced"
    os.makedirs(dir_name, exist_ok=True)

    # Truncate .jpg off of list of images
    list_of_image_names = [os.path.splitext(image_filename)[0] for image_filename in list_of_images]

    # # Create random indexes
    # random_indexes = np.random.choice(train_triplets.index,
    #                                   size=int(len(train_triplets.index) / 2),
    #                                   replace=False)
    # # switch image B and C for half the training set randomly to have an balanced dataset of 1 and 0 classifications
    # train_triplets_balanced = pd.read_table("train_triplets.txt", names=['A', 'B', 'C'], delimiter=' ', dtype=str)
    # train_triplets_balanced.iloc[random_indexes, 1] = train_triplets.iloc[random_indexes, 2]
    # train_triplets_balanced.iloc[random_indexes, 2] = train_triplets.iloc[random_indexes, 1]
    # train_labels = pd.DataFrame(np.ones((len(train_triplets.index), 1), dtype=int))
    # train_labels.iloc[random_indexes] = 0

    # Create train features dataframe
    train_features = pd.DataFrame()
    print("[create_feature_vectors] Training features...")
    for index, row in train_triplets.iterrows():
        # index = list_of_image_names.index(row['A']) # Find the index of an imagename in the feature list
        # list_of_features[index] # get the feature at that index
        features = np.concatenate((
            np.ones((1, 1)).reshape(-1) * index,
            list_of_features[list_of_image_names.index(row['A'])].reshape(-1),
            list_of_features[list_of_image_names.index(row['B'])].reshape(-1),
            list_of_features[list_of_image_names.index(row['C'])].reshape(-1)
        ))
        # The following line takes at least 40% of the execution time
        train_features = train_features.append(pd.DataFrame(features.reshape(1, -1)))
        if index % 10000 == 0 and index != 0:
            print(index / len(train_triplets.index))
            train_features.to_csv(os.path.join(
                dir_name,
                ("x_train_Resnet50_avg_pool_" + str(int(index / 10000)) + ".csv")))
            del train_features
            train_features = pd.DataFrame()
    print("[create_feature_vectors] Training features done.")
    train_features.to_csv(os.path.join(
                dir_name,
                "x_train_Resnet50_avg_pool_end.csv"))
    del train_features

    # Create test features dataframe
    test_features = pd.DataFrame()
    print("[create_feature_vectors] Test features...")
    for index, row in test_triplets.iterrows():
        # index = list_of_image_names.index(row['A']) # Find the index of an imagename in the feature list
        # list_of_features[index] # get the feature at that index, reshape(-1) to make a 1d array
        features = np.concatenate((
            np.ones((1, 1)).reshape(-1) * index,
            list_of_features[list_of_image_names.index(row['A'])].reshape(-1),
            list_of_features[list_of_image_names.index(row['B'])].reshape(-1),
            list_of_features[list_of_image_names.index(row['C'])].reshape(-1)
        ))
        test_features = test_features.append(pd.DataFrame(features.reshape(1, -1)))
        if index % 10000 == 0 and index != 0:
            print(index / len(test_triplets.index))
            test_features.to_csv(os.path.join(
                dir_name,
                ("x_test_Resnet50_avg_pool_" + str(int(index / 10000)) + ".csv")))
            del test_features
            test_features = pd.DataFrame()
    print("[create_feature_vectors] Test features done.")
    test_features.to_csv(os.path.join(
                dir_name,
                "x_test_Resnet50_avg_pool_end.csv"))
    del test_features


if __name__ == '__main__':
    # Extract features from images
    list_of_features, list_of_images = extract_features_from_images()

    # # Load traning and test triplets
    train_triplets = pd.read_table("train_triplets.txt", names=['A', 'B', 'C'], delimiter=' ', dtype=str)
    test_triplets = pd.read_table("test_triplets.txt", names=['A', 'B', 'C'], delimiter=' ', dtype=str)

    # Create feature vectors and labels
    create_feature_vectors()

    # # Train test split
    # X_train, X_test, y_train, y_test = train_test_split(
    #     x_train, y_train_labels, test_size=0.33, random_state=random_state, stratify=y_train_labels)
    #
    # # Instantiate models
    # print("Fitting models")
    # models = {
    #     # "Support Vector Classifier": SVC(verbose=1, random_state=random_state),
    #     # "Linear Support Vector Classifier": LinearSVC(verbose=1, random_state=random_state, max_iter=10000),
    #     "Multilayer Perceptron Classifier": MLPClassifier(random_state=random_state, verbose=1,
    #                                                       tol=0.0000001)
    # }
    #
    # # Train and predict for models
    # for model_name, model in models.items():
    #     print("Training", model_name, "...")
    #     model.fit(X_train, y_train)
    #     y_test_hat = model.predict(X_test)
    #     print("Accuracy score of", model_name, accuracy_score(y_true=y_test, y_pred=y_test_hat))
    #
    # # Evaluate
    # for model_name, model in models.items():
    #     y_test_hat = model.predict(X_test)
    #     print("Accuracy score of", model_name, accuracy_score(y_true=y_test, y_pred=y_test_hat))

    # TODO: Find out how to create the training/test data:
    # --
    # -- the encoding of the images from ResNet50 has shape (1, 7, 7, 2048), (huge!), flatten into a 1D array?
    # --- there are also ways to modify the encoding such that a pooling is applied at the end to give a lower
    # --- dimensional encoding that might be more tractable