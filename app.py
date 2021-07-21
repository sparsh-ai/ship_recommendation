from flask import Flask, request, render_template, session, redirect
import numpy as np
import pandas as pd
import sys

from configuration import databaseAuthName, databaseAuthPassword
from sqlalchemy import create_engine

sys.path.append("../recommendation")
from recommendation import recommender
from recommendation import recommender_functions as rf
from etl.transform_voyage_data import voyage_planbord

app = Flask(__name__)

db_url = 'mysql+pymysql://{}:{}@localhost/ship_recommendation'.format(databaseAuthName, databaseAuthPassword)
db_shipRecommendation = create_engine(db_url)
conn = db_shipRecommendation.connect()

df_barges = pd.read_sql('ships', con=db_shipRecommendation)
df = df_barges[
    ['Name', 'ENI', 'capacityTon', 'capacityM3', 'lengthCm', 'widthCm', 'flag', 'avgFuelConsumptionLtrKm']].sort_values(
    by='Name', ascending=True)
df_uimRaw = pd.read_sql('user_item_matrix', con=db_shipRecommendation)
df_ports = pd.read_sql('ports', con=db_shipRecommendation)
dfVoyagesPlan = pd.read_sql('voyages_plan', con=db_shipRecommendation)


@app.route('/', methods=("POST", "GET"))
def html_table():
    return render_template('barges.html', tables=[df.to_html(classes="table table-striped ",
                                                             header=True,
                                                             index_names=True)])


@app.route('/voyages', methods=("POST", "GET"))
def voyages():
    graphJSON = voyage_planbord()

    return render_template('voyages.html', graphJSON=graphJSON)


@app.route('/recommendations', methods=("POST", "GET"))
def data():
    if request.method == "GET":
        selectBarges = "SELECT Name FROM ships ORDER BY Name"
        selectPorts = "SELECT description FROM ports ORDER BY description"

        barges = db_shipRecommendation.execute(selectBarges)
        ports = db_shipRecommendation.execute(selectPorts)
        ports2 = db_shipRecommendation.execute(selectPorts)

        graphJSON = voyage_planbord()

        return render_template('recommendations.html', fromPorts=ports, toPorts=ports2, barges=barges,
                               graphJSON=graphJSON)

    elif request.method == "POST":
        from_port = request.form.get('from_port')
        to_port = request.form.get('to_port')
        start_date = request.form.get('start_date')
        prefered_barge = request.form.get('prefered_barge')

        latitude = df_ports[df_ports['description'] == from_port]['latitude'].item()
        longitude = df_ports[df_ports['description'] == from_port]['longitude'].item()


        if len(rf.get_voyage_id(from_port, to_port, df_uimRaw, df_ports)) == False:
            bargeId = df_barges[df_barges['Name'] == prefered_barge]['Id'].item()
            rec = recommender.Recommender()
            rec.fit(df_barges, df_uimRaw, learning_rate=.01, iters=1)
            recommendations = rec.make_recommendations(bargeId)[0]

        else:
            voyageId = rf.get_voyage_id(from_port, to_port, df_uimRaw, df_ports)
            rec = recommender.Recommender()
            rec.fit(df_barges, df_uimRaw, learning_rate=.01, iters=200)
            recommendations = rec.make_recommendations(voyageId[0], 'voyage')[0]

        recommendations = [int(recom) for recom in recommendations]
        recommender_df = df_barges[df_barges['Id'].isin(recommendations)]


        positions, distanceKm = rf.find_barge_location(recommender_df, latitude, longitude)
        recommender_df['positions'] = positions
        recommender_df['distanceKm'] = distanceKm

        recommender_df = recommender_df[['Name', 'ENI', 'capacityTon', 'positions', 'distanceKm']].sort_values(
            'distanceKm',
            ascending=True)

        graphJSON = voyage_planbord()

        return render_template('recommendations.html', graphJSON=graphJSON,
                               tables=[recommender_df.to_html(classes="table table-striped ",
                                                              header=True,
                                                              index_names=True)])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
