import sys
import requests

import numpy as np
import pandas as pd

from configuration import databaseAuthName, databaseAuthPassword, idcpAuthPassword, icdpAuthName

from etl import extract_voyage_data as evd
from sqlalchemy import create_engine


db_url = 'mysql+pymysql://{}:{}@localhost/ship_recommendation'.format(databaseAuthName,databaseAuthPassword)
db_shipRecommendation = create_engine(db_url)
uim = pd.read_sql('user_item_matrix', con = db_shipRecommendation)
barge_df = pd.read_sql('ships', con = db_shipRecommendation)
ports = pd.read_sql('ports', con = db_shipRecommendation)

def get_voyage_id(from_port, to_port, uim, ports):
    '''
    Get the voyage_id based on the selected locations
    :param from_port: Port the voyage start
    :param to_port: Port the voyage ends
    :param uim: voyage item matrix
    :param ports: database of ports

    :return: voyage_Id
    '''

    # Get codes from from and to ports
    fromPortCode = ports[ports['description'] == from_port]['code'].item()
    toPortCode = ports[ports['description'] == to_port]['code'].item()

    # Get voyage accessory from voyage item matrix
    voyageAccessory = fromPortCode + toPortCode
    if len(voyageAccessory):
        print("list is empty")
    else:
        print("list is not empty")
    return uim[uim['Accessory'] == voyageAccessory].index

def get_barge_names(barge_ids, barge_df = barge_df):
    '''
    INPUT
    barge_ids - a list of barge_ids
    barge_df - original barge dataframe
    OUTPUT
    barges - a list of barges names associated with the barge_ids

    '''

    barge_lst = barge_df[barge_df['Id'].isin(barge_ids)][['Id','Name']]

    return barge_lst


def create_ranked_df(uim, barge_df):
        '''
        INPUT
        user_item_matrix -


        OUTPUT
        ranked_barges -
        '''

        # Pull the average ratings and number of ratings for each barge
        barges = uim.append(uim.sum(numeric_only=True), ignore_index=True)
        barges = pd.DataFrame(barges.iloc[-1].sort_values(ascending = False))[1:-1]
        barges = barges.rename(columns = {288: 'amount_used'})

        listOfId = [int(x) for x in list(barges.index)]
        bargeNames = get_barge_names(listOfId, barge_df)
        bargeNames['Id'] = bargeNames['Id'].astype(str)

        ranked_barges = barges.merge(bargeNames, how = 'left', left_index = True, right_on = 'Id')
        ranked_barges = ranked_barges[['Id','Name','amount_used']]

        return ranked_barges


def find_similar_barge(barge_id, barge_df):
    '''
    INPUT
    barge_id - a barge id
    barge_df - original barge dataframe
    OUTPUT
    similar_barges - an dataframe of  of the most similar barges by name
    '''
    # dot product to get similar barges
    barge_content = pd.get_dummies(barge_df[['categoryTon', 'categoryM3', 'categoryM2','flag']].astype(object))
    barge_content = np.array(barge_content)
    dot_prod_barges = np.dot(barge_content,np.transpose(barge_content))

    # find the row of each barge
    barge_idx = np.where(barge_df['Id'] == barge_id)[0][0]

    # find the most similar barge indices -  get the top 6
    similar_idx = np.argsort(dot_prod_barges[barge_idx])[-6:]


    # delete the barge that we need a substitute for
    indexToDelete = np.where(similar_idx == barge_idx)
    similar_idx = np.delete(similar_idx,indexToDelete)

    similar_barges = barge_df.iloc[similar_idx, ]

    return similar_barges

def find_barge_location(df, latitude, longitude): #(df,locationLatitude, locationLongitude)

    # Get barge positions
    positions = []
    distanceKm = []
    for id in df['Id']:
        try:
            positionDetails = evd.get_ship_position(id)
    #        positions.append(positionDetails['location'])
            bargeLocation = positionDetails['location']

            bargePositionLatitude = positionDetails['latitude']
            bargePositionLongitude = positionDetails['longitude']
            locationLatitude = latitude # should be the load location lat/long
            locationLongitude = longitude
            r = requests.get(url = "https://idcp-ship.cofanoapps.com/getPolyline?from={}%2C{}"
                                   "&to={}%2C{}"
                                   "&shipType=DORTMUNDER&maxDistanceToRoute=10.0"
                                   "&includedistancetopoints"
                                   "&includestreamdistances&properties&".format(bargePositionLatitude,
                                                                                bargePositionLongitude,
                                                                                locationLatitude,
                                                                                locationLongitude),
                            auth= (icdpAuthName,idcpAuthPassword))
            distanceJson = r.json()
            distance = distanceJson['Routes'][0]['Distance']
    #        print(distanceJson['Routes'][0]['Distance'])
            positions.append(bargeLocation)
            distanceKm.append(distance)
        except:
            distanceKm.append(np.nan)
            positions.append(np.nan)
    print(len(positions))
    print(len(distanceKm))
    return positions, distanceKm

def available_barges(timestamp, voyagePlan):
    '''
    Function to check if barge is available at given timestamp
    :param timestamp: Date the barge should
    :param voyagePlan: distributed barges over voyages
    :return: Id's of available barges
    '''

    # Compare barges from voyage plan with timestamp
    unavailableBarges = voyagePlan[voyagePlan['voyage_end'] > timestamp]['ship_id'].item()

    return unavailableBarges




#simBarge = find_similar_barge(2, barge_df)

#print(np.array(simBarge['Name']))
#positions, distanceKm = find_barge_location(simBarge)
#simBarge['positions'] = positions
#simBarge['distanceKm'] = distanceKm
#print(simBarge.info())
