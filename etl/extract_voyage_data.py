import pandas as pd
import requests
from datetime import date, datetime, timedelta
import configuration
import recommendation.recommender_functions as rf


def get_voyages():
    '''
    Function for extracting data from operating system

    :return: dictionary object of voyages
    '''
    # Get information from source
    get_voyages = configuration.bargeOperatorUrlVoyages
    req = requests.get(url=get_voyages, auth=configuration.BasicAuth)
    voyagePages = req.json()
    # save total amount of pages from source
    totalPages = voyagePages['totalPages']

    voyageDictionary = {}

    # loop trough source for all voyages
    for x in range(totalPages):
        voyagePage = configuration.bargeOperatorUrlVoyagesPage.format(x)
        voyageRequest = requests.get(url=voyagePage, auth=configuration.BasicAuth)
        voyages = voyageRequest.json()

        # get voyage, ship, locations and planned departure times from voyages
        for y in range(voyages['numberOfElements']):
            voyage_id = voyages['content'][y]['id']
            ship_id = voyages['content'][y]['ship']['id']
            temp_name = []
            temp_time = []
            for i in [0, 1]:
                try:
                    colom_name = voyages['content'][y]['calls'][i]['location']['id']
                    temp_name.append(colom_name)
                    colom_time = voyages['content'][y]['calls'][i]['ptd']
                    temp_time.append(colom_time)
                except:
                    break
            # save information in a dictionary. If there isn't a location_two in throws an except.
            try:
                voyageItems = {"voyage_id": voyage_id, "ship_id": ship_id,
                               "location_one": temp_name[0], "location_one_ptd": temp_time[0],
                               "location_two": temp_name[1], "location_two_ptd": temp_time[1]}
            except:
                break

            if not voyageDictionary:
                key = 0
            else:
                key = list(voyageDictionary.keys())[-1] + 1
            voyageDictionary[key] = voyageItems

    return voyageDictionary

def get_voyages_plan():
    '''

    :return: Overview of voyage plan
    '''

    # Get information from source
    get_voyages = configuration.bargeOperatorUrlVoyages
    req = requests.get(url=get_voyages, auth=configuration.BasicAuth)
    voyagePages = req.json()
    # save total amount of pages from source
    totalPages = voyagePages['totalPages']

    voyagePlanDictionary = {}
    key = 0

    # loop trough source for all voyages
    for x in range(totalPages):
        voyagePage = configuration.bargeOperatorUrlVoyagesPage.format(x)
        voyageRequest = requests.get(url=voyagePage, auth=configuration.BasicAuth)
        voyages = voyageRequest.json()

        # get voyage, ship, locations and planned departure times from voyages
        for y in range(voyages['numberOfElements']):
            past = date.today() - timedelta(days=7)
            future = date.today() + timedelta(days=7)
            voyageCallsPta = voyages['content'][y]['calls'][0]['pta']
            voyageCallsPta = datetime.date(datetime.strptime(voyageCallsPta, '%Y-%m-%dT%H:%M:%SZ'))

            if voyageCallsPta < future and voyageCallsPta > past:
                voyageId = voyages['content'][y]['id']
                shipId = voyages['content'][y]['ship']['id']
                voyage_start = voyages['content'][y]['calls'][0]['pta']
                try:
                    voyage_end = voyages['content'][y]['calls'][1]['ptd']
                except:
                    print('missing call')

                # shipName = rf.get_barge_names(list[shipId])[1]

                voyagePlan = {"voyage_id": voyageId, "ship_id": shipId,
                              "voyage_start": voyage_start, "voyage_end": voyage_end}

                voyagePlanDictionary[key] = voyagePlan
                key += 1

    dfVoyagePlan = pd.DataFrame.from_dict(voyagePlanDictionary, orient='index')

    # Create barge alias
    dfVoyagePlan['ship_id'] = dfVoyagePlan['ship_id'].astype('object')
    dfVoyagePlan['ship_alias'] = list(dfVoyagePlan['ship_id'].map(str) + 'ship')

    return dfVoyagePlan

def get_ship_position(shipId):
    '''
    Function to retrieve a actual ship position
    :input: Ship id
    :return: position of ship in lat, long and timestamp
    '''
    getShipPosition = configuration.bargeOperatorUrlShipPositions.format(shipId)
    requestShipPosition = requests.get(url=getShipPosition, auth=configuration.BasicAuth)
    positionDetails = requestShipPosition.json()

    position = {'ship_id': shipId, 'location': positionDetails['location']['location'],
                'latitude': positionDetails['latitude'], 'longitude': positionDetails['longitude'],
                'course': positionDetails['course'], 'speed': positionDetails['speed'],
                'timestamp': positionDetails['timestamp']}

    return position


def get_locations():
    '''
    Function to retrieve all locations in data set
    :return: locations
    '''
    # Get information from source
    getLocations = configuration.bargeOperatorUrlLocations
    requestLocations = requests.get(url=getLocations, auth=configuration.BasicAuth)
    locationPages = requestLocations.json()
    # save total amount of pages from source
    totalLocationPages = locationPages['totalPages']

    locationDictionary = {}

    # loop trough source for all voyages
    for x in range(totalLocationPages):
        locationPage = configuration.bargeOperatorUrlLocationsPage.format(x)
        locationRequest = requests.get(url=locationPage, auth=configuration.BasicAuth)
        locations = locationRequest.json()

        # get voyage, ship, locations and planned departure times from voyages
        for y in range(locations['numberOfElements']):
            try:
                location_id = locations['content'][y]['id']
                location_type = locations['content'][y]['type']
                location_code = locations['content'][y]['code']
                location_latitude = locations['content'][y]['position']['latitude']
                location_longitude = locations['content'][y]['position']['longitude']
            except:
                break
            # save information in a dictionary
            locationItems = {"id": location_id, "type": location_type,
                             "code": location_code, "latitude": location_latitude,
                             "longitude": location_longitude}
            key = 0
            if not locationDictionary:
                key = 0
            else:
                key = list(locationDictionary.keys())[-1] + 1
            locationDictionary[key] = locationItems

    return locationDictionary

