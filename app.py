# import necessary libraries
import numpy as np
import datetime as dt
import pandas as pd
import requests
import datetime as dt
import math
import joblib


import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct, and_
from sklearn.linear_model import LogisticRegression


from flask import Flask, jsonify
from flask_cors import CORS

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
cors = CORS(app)

#################################################
# Functions Setup
#################################################

citygeos = pd.read_csv("city geos.csv")

POR_df = pd.read_csv('POR.csv')
POR_df.set_index('ClosestCity',inplace = True)


def ReadUSGS(BaseDate = dt.datetime.today()):
    
    StartDate = (BaseDate - dt.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    EndDate = BaseDate.strftime('%Y-%m-%d %H:%M:%S')
    
    url = f'https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime={StartDate}&endtime={EndDate}&maxlatitude=41.961&minlatitude=32.813&maxlongitude=-114.521&minlongitude=-124.255&minmagnitude=2.5&orderby=time'
    
    data = requests.get(url)
    return data.json()

def AddPOR(Main_df):
    periods = np.array([])
    for index, row in Main_df.iterrows():
        catagory = f"Mag{int(row['category']*10)}"
        city = row['ClosestCity']
        
        periods = np.append(periods, POR_df.loc[city,catagory])

        Main_df['POR'] = periods

        return Main_df

def df_to_json(df):
    
    features = []
    
    for index, row in df.iterrows():
        
        # Read record from dataframe 
        lon = row['Longitude']
        lat = row['Latitude']
        mag = row['mag']
        city = row['ClosestCity']
        
        # build record into dictionary 
        record = {
            
            'geometry':{
                'coordinates': [lon, lat, 0]
            },
            
            "properties": {
                'mag': mag,
                'title':city
            }
              
        }
                   
        features.append(record)

    return jsonify({'features':features})

def Json_to_df(response):
    
    rows = []
    for record in response['features']:

        mag = record['properties']['mag']
        lon = record['geometry']['coordinates'][0]
        lat = record['geometry']['coordinates'][1]

        if mag - int(mag) > .5:
            n = 0.5 
        else:
            n = 0


        row = {

            'longitude': lon,
            'latitude': lat,
            'depth': record['geometry']['coordinates'][2],
            'mag': mag,
            'category': int(mag) + n,
            'ClosestCity': FindCity(lat=lat,lon=lon)

        }

        rows.append(row)
        
    df=pd.DataFrame(rows)
    
    return df

def FindCity(lat, lon):
    distCompare = 100000000
    for i in range(0,len(citygeos)):
        latCity = citygeos.iloc[i,1]
        lonCity = citygeos.iloc[i,2]
        x = latCity - lat
        y = (lonCity - lon) * math.cos(lat * math.pi/180)
        distance = 110.25 * (x**2 +y**2)**0.5
        if distance < distCompare:
            Geo = citygeos.iloc[i,0]
            distCompare = distance
    return Geo

def DefineProblem(AtDate):
    
    #myDate = dt.datetime.strptime(AtDate, '%Y-%m-%d %H:%M:%S')

    response = ReadUSGS(AtDate)

    df = Json_to_df(response)

    # df = AddPOR(df)
    
    output_df = generate_features(df)

    return output_df

def generate_features(df):

    features = POR_df.columns
    cities =df['ClosestCity'].unique()

    my_df = pd.DataFrame(columns = features)
    my_df.insert(0,'ClosestCity',cities)
    my_df = my_df.set_index('ClosestCity')
    my_df.fillna(0, inplace =True)

    agg = df.groupby('ClosestCity')['category'].value_counts()
    for item in agg.index:

        #print(item[0], item[1] , agg[item[0]][item[1]])
        my_df['Mag' + str(int(item[1]*10))][item[0]] = agg[item[0]][item[1]]

    cities_df = citygeos.copy()
    cities_df.rename(columns= {'City':'ClosestCity'}, inplace =True)

    output_df = pd.merge(cities_df, my_df, on = 'ClosestCity')
    
    return output_df

    


# create route that renders index.html template
@app.route("/")
def home():

    return (
        """List all available api routes."""
        f"Available Routes:<br/>"
        f"/api/v1.0/areas<br>"
        f"/api/v1.0/past30days/(date YYYY-MM-DD hh:mm:ss)<br>"
        f"/api/v1.0/predict/(date YYYY-MM-DD hh:mm:ss)<br>"
        f"/api/v1.0/target/(date YYYY-MM-DD hh:mm:ss)<br>"
    )
    
@app.route("/api/v1.0/areas")
def areas():

    df = pd.read_csv('city geos.csv')
    return jsonify(df['City'].tolist())

@app.route("/api/v1.0/past30days/<AtDate>")
def past30days(AtDate):
    
    myDate = dt.datetime.strptime(AtDate, '%Y-%m-%d %H:%M:%S')

    json = ReadUSGS(myDate)

    return jsonify(json)

@app.route("/api/v1.0/predict/<AtDate>")
def predict(AtDate):

    myDate = dt.datetime.strptime(AtDate, '%Y-%m-%d %H:%M:%S')

    df = DefineProblem(myDate)

    X = df.iloc[:,3:]

    model = joblib.load('final_model.sav')
    predictions = model.predict(X)
    df.insert(3, 'mag', predictions)
    output_df = df.iloc[:,:4]
    json = df_to_json(output_df)
 

    return json


@app.route("/api/v1.0/target/<AtDate>")
def target(AtDate):

    myDate = dt.datetime.strptime(AtDate, '%Y-%m-%d %H:%M:%S')
    StartDate = (myDate + dt.timedelta(days=30))

    response = ReadUSGS(StartDate)

    print(response)

    my_df = Json_to_df(response)

    my_df = my_df.groupby(my_df['ClosestCity']).max()

    cities_df = citygeos.copy()
    cities_df.rename(columns= {'City':'ClosestCity'}, inplace =True)

    output_df = pd.merge(cities_df, my_df, on = 'ClosestCity')

    json = df_to_json(output_df)

    return json



if __name__ == "__main__":
    app.run()
