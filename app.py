# import necessary libraries
import numpy as np
import datetime as dt
import pandas as pd
import requests
import datetime as dt
import math


import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct, and_

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
        lon = row['longitude']
        lat = row['latitude']
        depth = row['depth']
        mag = row['mag']
        city = row['ClosestCity']
        
        # build record into dictionary 
        record = {
            
            'geometry':{
                'coordinates': [lon, lat, depth]
            },
            
            "properties": {
                'mag': mag,
                'title':city
            }
              
        }
                   
        features.append(record)

    return jsonify({'features':features})



    


# create route that renders index.html template
@app.route("/")
def home():

    return (
        """List all available api routes."""
        f"Available Routes:<br/>"
        f"/api/v1.0/areas<br>"
        f"/api/v1.0/predict/(date YYYY-MM-DD hh:mm:ss)<br>"
    )
    
@app.route("/api/v1.0/areas")
def areas():

    df = pd.read_csv('city geos.csv')
    return jsonify(df['City'].tolist())

@app.route("/api/v1.0/predict/<AtDate>")
def predict(AtDate):

    myDate = dt.datetime.strptime(AtDate, '%Y-%m-%d %H:%M:%S')

    return jsonify(ReadUSGS(myDate))



if __name__ == "__main__":
    app.run()
