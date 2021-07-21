import pandas as pd
import polyline
from shapely.geometry import Point, Polygon

from etl.extract_voyage_data import get_voyages,get_locations
from configuration import databaseAuthName, databaseAuthPassword
import pymysql
from sqlalchemy import create_engine

import plotly
import plotly.express as px
import json

db_url = 'mysql+pymysql://{}:{}@localhost/ship_recommendation'.format(databaseAuthName,databaseAuthPassword)
db_shipRecommendation = create_engine(db_url)
df_ports = pd.read_sql('ports', con = db_shipRecommendation)
dfVoyagesPlan = pd.read_sql('voyages_plan', con = db_shipRecommendation)


def create_user_item_matrix(df):
    '''
    Function to create a user_item_matrix of historical cargo allocation barges
    :param dataframe:

    :return: user_item_matrix where the voyage routes are the users and the barges are the items.
    '''

    df = df[['ship_id','port_one','port_two']]
    df['accessory'] = list(df['port_one'].map(str) + df['port_two'].map(str))

    ship_rates = df.groupby(['accessory','ship_id'])['ship_id'].count().sort_values().to_frame(name = 'count').reset_index()

    user_item_matrix = ship_rates.pivot(index='accessory', columns='ship_id', values= 'count')
    user_item_matrix = user_item_matrix.fillna(0)

    return pd.DataFrame(user_item_matrix.to_records())


def port_allocation(var_name, df_call, df_ports):
    '''
    Allocates ports to locations

    input: Dataframe of voyage with start and end that can be ports or locations
    output: Dataframe of voyages with start and end that are known ports, else locations
    '''
    count_iteration = 0
    count_ports = 0
    port_locations = []

    for labels, rows in df_call.iterrows():
        location_point = Point(rows['latitude'], rows['longitude'])
        for col, ind in df_ports.iterrows():
            decoder = polyline.decode(ind['encodedPolyline'])
            port_check = Polygon(decoder)
            if location_point.within(port_check):
                port_locations.append(ind['code'])
                count_ports += 1
                break
        count_iteration += 1
        if count_iteration != count_ports:
            port_locations.append(rows[var_name])
            count_ports += 1

    return port_locations


def retrieve_ports(df_voyages, df_locations,df_ports, retrievePortsFrom=['location_one', 'location_two']):
    '''
    Gets port codes from locations
    :return: List of port one and port two codes
    '''

    for loc in retrievePortsFrom:
        retrieve_loc = df_voyages.merge(df_locations, how='left', left_on=loc, right_on='id')
        retrieve_loc = retrieve_loc[[loc, 'code', 'latitude',
                                     'longitude']]
        if loc == 'location_one':
            port_one = port_allocation(loc, retrieve_loc, df_ports)
        else:
            port_two = port_allocation(loc, retrieve_loc, df_ports)

    return port_one, port_two

def voyage_planbord():
    '''

    :return: planbord for voyages in Json format to use for HTML
    '''


    fig = px.timeline(dfVoyagesPlan, x_start="voyage_start", x_end="voyage_end", y="ship_alias", color="voyage_id")
    fig.update_yaxes(autorange="reversed")

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


#df_voyages = pd.DataFrame.from_dict(get_voyages(), orient='index')
#df_locations = pd.DataFrame.from_dict(get_locations(), orient='index')
#df_voyages['port_one'],df_voyages['port_two'] = retrieve_ports(df_voyages, df_locations,df_ports,)
#uim = create_user_item_matrix(df_voyages)