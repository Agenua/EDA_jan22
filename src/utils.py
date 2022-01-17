import numpy as np
import pandas as pd
import requests 
import zipfile 
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import datetime
from datetime import date

def download(url):
    ''' 
    Función que descarga el argumento url (en este caso la web de la API de BiciMAD), 
    hace la petición, guarda el archivo.zip y lo descomprime para ver su contenido 
    '''
    filename = 'biciMAD.zip'
    
    r = requests.get(url, allow_redirects=True)
    
    # Guarda el zip
    with open(filename, 'wb') as f:
        f.write(r.content)
    
    # Extrae el contenido del zip
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(".")


def read(filename):
    ''' 
    Función que lee el argumento filename (en este caso un .json), 
    convierte de s a min la columna 'travel_time',
    y devuelve el número de registros y el tiempo del trayecto en bicicleta (mean y median) 
    '''
    df = pd.read_json(filename, lines=True, encoding ='latin-1')

    travel_time_min = df['travel_time']/60 
    n_reg = travel_time_min.count()

    time_mean = travel_time_min.mean()
    time_med = travel_time_min.median()

    return n_reg, time_mean, time_med


def graph_boxplot(filename):
    ''' 
    Función para pintar un boxplot:
    primero lee el argumento filename (.json), 
    convierte de s a min la columna 'travel_time' y la añade a la dataframe,
    filtra la columna 'travel_time_min' excluyendo valores menores de 0 min y mayores de 30 min de trayecto
    '''
    df = pd.read_json(filename, lines=True, encoding ='latin-1')

    travel_time_min = df['travel_time']/60
    df['travel_time_min'] = travel_time_min

    df_no_extr_val = df[(df['travel_time_min'] > 0) & (df['travel_time_min'] < 30)]
    fig = df_no_extr_val.boxplot(column = 'travel_time_min')
    plt.ylabel('minutes')

    return fig


def user_type_count(filename):
    ''' 
    Función para contar el número de registros agrupados por tipo de usuario:
    lee el argumento filename, agrupa por tipo de usuario y escribe un .csv con el resultado
    '''
    
    df = pd.read_json(filename, lines=True, encoding ='latin-1')
    df_group = df.groupby(['user_type']).count().reset_index()
    df_group['user_day_code'].to_csv('records_by_user_type.csv', sep=',')
    cont = df_group['user_day_code']
    return cont


def barplot_byage(filename):
    ''' 
    Función para pintar un barplot del rango de edad de los ususarios con abono anual:
    lee el argumento filename, agrupa por rango de edad, 
    crea una máscara para el tipo de usuario (user_type = 1) y dibuja el gráfico
    '''
    df = pd.read_json(filename, lines=True, encoding ='latin-1')

    c = ['red', 'blue', 'c', 'g', 'yellow', 'lightcoral', 'orange']

    df[df['user_type'] == 1].groupby(['ageRange'])['user_day_code'].count().plot(kind='bar', color=c)
    
    age0 = mpatches.Patch(color='red', label='Indeterminada')
    age1 = mpatches.Patch(color='blue', label='16-17 años')
    age2 = mpatches.Patch(color='c', label='17-18 años')
    age3 = mpatches.Patch(color='g', label='19-26 años')
    age4 = mpatches.Patch(color='yellow', label='27-40 años')
    age5 = mpatches.Patch(color='lightcoral', label='41-65 años')
    age6 = mpatches.Patch(color='orange', label='mayor de 66')
    
    plt.legend(handles = [age0, age1, age2, age3, age4, age5, age6], loc='best', frameon = True, bbox_to_anchor=(1, 1))


def filtrado(filename):
    '''
    Función para filtrar los datos, 
    lee el argumento filename, 
    convierte la fecha en formato amigable,
    convierte la duración del trayecto de s a min, filtra por una duración determinada,
    elimina tipos de usuarios de tipo indeterminado,
    elimina rango de edad indeterminado,
    limpia la columna del código postal, filtra por códigos de la Com.Madrid (28XXX),
    y elimina las columnas que ya no son de interés
    '''

    df = pd.read_json(filename, lines=True, encoding ='latin-1')

    #Arregla columna fecha 'unplug_hourTime'
    df['date'] = pd.to_datetime(df['unplug_hourTime'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour

    #Convierte columna 'travel_time' de s a min
    df['travel_time_min'] = df['travel_time']/60

    #Filtra por trayectos mayores de 3 min y 180 min (3h)
    df_time = df[(df['travel_time_min'] > 3) & (df['travel_time_min'] < 180)]

    #Filtra por user_type 1 (pase anual) y 2 (ocasional)
    df_usertyp = df_time[(df_time['user_type'] == 1) | (df_time['user_type'] == 2)] 

    #Filtra por edad, elimina la edad indeterminada
    df_age = df_usertyp[(df_usertyp['ageRange'] != 0)]

    #'zip_code' contiene NaN y emails
    # Se asume que son residentes en Madrid, selecciona números >= 28000 y < 29000
    df_age['zip_code2'] = df_age['zip_code'].str.extract('(\d\d\d\d\d)')
    df_mask_code = df_age[(df_age['zip_code2'] >= '28000') & (df_age['zip_code2'] < '29000')]
    df_code = df_mask_code.dropna(axis=0)

    #Elimina columnas que no interesan:
    df_filt = df_code.drop(columns = ['travel_time', 'unplug_hourTime', 'zip_code'], axis = 1)

    return df_filt