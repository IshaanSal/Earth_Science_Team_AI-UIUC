# -*- coding: utf-8 -*-
"""EPA_LSTM_trial(next_24_hours).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WmxMktUoSA5r97zkPlNZxKgWU80xVfoa

https://aqs.epa.gov/aqsweb/airdata/download_files.html#Raw
➡ CO (42101)

This is the link to the original dataset the model needs to be trained on

**The data file I used in this notebook is a reduced version of the original to run faster on colab

**Original(1000000+ lines) ThisVersion(200 lines)
"""

pip install cartopy

import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense
import math
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

#Read csv

df = pd.read_csv("hourly_42101_2021_new.csv")

#check df

df

#dropping all irrelevant columns (only kept the necessary ones)

df = df.drop(["State Code", "County Code", "Parameter Code", "POC", "Datum",
              "Site Num", "MDL", "Uncertainty", "Qualifier", "Method Type",
              "Method Code", "Method Name", "Date of Last Change",
              "Parameter Name", "Units of Measure", "State Name", "County Name",
              "Date GMT", "Time GMT"], axis = 'columns')

#checking drop

df

#First function converts date into day of year, and then normalizes it to scale of 0 to 1
#Second function converts time of day, into hour of day, and then normalizes it to scale of 0 to 1

def adjust_date(arr):
  adjusted_date_local = []

  for date in arr:
    temp = date.split("/")
    curr = temp[2] + "-" + temp[0] + "-"  + temp[1]
    period = pd.Period(curr)
    adjusted_date_local.append(int(period.day_of_year)/365)

  return adjusted_date_local

def adjust_time(arr):
  adjusted_time_local = []

  for time in arr:
    strTime = time.replace(":", ".")
    adjusted_time_local.append(float(strTime)/24)

  return adjusted_time_local

#Creating the new adjusted columns by applying the functions to existing values
#Deleting old non-formatted columns

df["Date Local (adjusted)"] = adjust_date(df["Date Local"])
df["Time Local (adjusted)"] = adjust_time(df["Time Local"])

df = df.drop(["Date Local", "Time Local"], axis = 'columns')

#function that normalizes the longitude and latitude to a scale of 0 to 1

def adjust_long_lat(arr):
  adjusted_long_lat = []

  for pos in arr:
    adjusted_long_lat.append(float(pos)/180)

  return adjusted_long_lat

#Once again adding the new adjusted columns and deleting old non-formatted columns

df["Latitude (adjusted)"] = adjust_long_lat(df["Latitude"])
df["Longitude (adjusted)"] = adjust_long_lat(df["Longitude"])

df = df.drop(["Latitude", "Longitude"], axis = 'columns')

def new_sin(arr):
  sin_ans = []

  for input in arr:
    sin_ans.append(math.sin(input))

  return sin_ans

def new_cos(arr):
  cos_ans = []

  for input in arr:
    cos_ans.append(math.cos(input))

  return cos_ans

df["sin(day of year)"] = new_sin(df["Date Local (adjusted)"])
df["cos(day of year)"] = new_cos(df["Date Local (adjusted)"])
df["sin(time of day)"] = new_sin(df["Time Local (adjusted)"])
df["cos(time of day)"] = new_cos(df["Time Local (adjusted)"])

#checking new edits to df

df

#Turning "Sample Measurement" column into target (output) array and dropping from df

target = df["Sample Measurement"]
df = df.drop("Sample Measurement", axis = 'columns')

#Splitting dataset into 80/20 train/test split and checking shape

split_point1 = int(0.6 * len(df))
split_point2 = int(0.8 * len(df))

x_train = df[0:split_point1]
x_test = df[split_point1:split_point2]
x_val = df[split_point2:]

y_train = target[0:split_point1]
y_test = target[split_point1:split_point2]
y_val = target[split_point2:]

print(x_train.shape, y_train.shape, x_test.shape, y_test.shape, x_val.shape, y_val.shape)

#converting df DataFrame objects to Numpy, so reshape function can be applied

x_train = x_train.to_numpy()
x_test = x_test.to_numpy()
x_val = x_val.to_numpy()

y_train = y_train.to_numpy()
y_test = y_test.to_numpy()
y_val = y_val.to_numpy()

"""Following code implements the method that utilizes 24 hours of input, to predict the next 24 hours

(other file utilizes 23 hours of input, to predict the 24th hour)
"""

#Defining function that uses sliding window method to divide input data set into sequences of 24 hours

def hourly_sequencer(inputArray):
  sequence_length = 24
  sequences = []

  for j in range(inputArray.shape[0]-sequence_length):
    window = []
    for i in range(sequence_length):
      window.append(inputArray[j+i])
      temp_window = np.array(window)

    sequences.append(temp_window.flatten())

  return sequences

#Performs the 24 hour division on the training input data set, and training output data set

x_train_adjusted = hourly_sequencer(x_train)
x_train_adjusted = np.array(x_train_adjusted)

print(x_train_adjusted.shape)

y_train_final = hourly_sequencer(y_train)
y_train_final = np.array(y_train_final)

print(y_train_final.shape)

#Reshaping current data format to fit 3D input array for LSTM
#(num_of_samples, num_timesteps, num_features)
#(total # of data points, 1 incremental timestep, 192 input categories)

x_train_final = np.reshape(x_train_adjusted, (x_train_adjusted.shape[0], 1, x_train_adjusted.shape[1]))

print(x_train_final.shape)

#Building LSTM model

model = Sequential() #For linear stack of layers
model.add(LSTM(x_train_adjusted.shape[0], input_shape=(1, x_train_adjusted.shape[1]))) #LSTM dimensions (≈, 1, 192)
model.add(Dense(24)) #Fully connected output layer with 24 nodes (for predicting 24 hours)

#Compiling and fitting dataset to model

#RMSE used beacuse it computes root mean squared error metric between y_true and y_pred
model.compile(loss="mean_squared_error", optimizer='adam', metrics=[tf.keras.metrics.RootMeanSquaredError()])

model.fit(x_train_final, y_train_final, epochs=5, batch_size=32)

test = np.reshape(x_train_final[1], (x_train_final[1].shape[0], 1, x_train_final[1].shape[1]))
print(test.shape)

test_predicted_val = model.predict(test)

test_predicted_val

y_train_final[1]