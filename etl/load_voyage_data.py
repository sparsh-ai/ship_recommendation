from extract_voyage_data import get_voyages_plan
from configuration import databaseAuthName,databaseAuthPassword
from sqlalchemy import create_engine

db_url = 'mysql+pymysql://{}:{}@localhost/ship_recommendation'.format(databaseAuthName,databaseAuthPassword)
db_shipRecommendation = create_engine(db_url)

get_voyages_plan().to_sql('voyages_plan', con = db_shipRecommendation, if_exists = 'replace')



