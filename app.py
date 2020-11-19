# import necessary libraries
import numpy as np
import datetime as dt
import pandas as pd
import requests


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

#################################################
# Database Setup
#################################################


# create route that renders index.html template
@app.route("/")
def home():

    return (
        """List all available api routes."""
        f"Available Routes:<br/>"
        f"/api/v1.0/areas<br>"
    )
    
@app.route("/api/v1.0/areas")
def areas():

    df = pd.read_csv('city geos.csv')
    return jsonify(df['City'].tolist())


if __name__ == "__main__":
    app.run()
