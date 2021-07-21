import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from configuration  import databaseAuthName,databaseAuthPassword

from recommendation import recommender_functions as rf

from sqlalchemy import create_engine

db_url = 'mysql+pymysql://{}:{}@localhost/ship_recommendation'.format(databaseAuthName,databaseAuthPassword)
db_shipRecommendation = create_engine(db_url)
uimRaw = pd.read_sql('user_item_matrix', con = db_shipRecommendation)
barge_df = pd.read_sql('ships', con = db_shipRecommendation)

class Recommender():
    '''
    This Recommender uses FunkSVD to make predictions of exact ratings. 
    '''

    def __init__(self):
        '''
        No attributes needed
        '''

    def fit(self, barge_df, uimRaw, iters = 100, latent_features = 12, learning_rate=0.0001):
        '''
        This function performs matrix factorization using a basic form of FunkSVD with no regularization

        INPUT:
        :param uim: user item matrix
        :param barge_df: list with barges
        :param latent_features: (int) the number of latent features
        :param learning_rate: (int) the learning rate
        :param iters: (int) number of iterations

        :return:


        '''
        # user item matrix counts the amount of times a barge has traveled the route.
        # Should normalize these numbers


        uimRaw.drop(columns=['Accessory', 'index'], inplace=True)

        # Get barge columns, with barges (ignore first column, voyage)
        bargeColumns = uimRaw.columns
        bargeIndices = list(range(len(bargeColumns)))
        self.bargeColumnsMap = {}

        # Create dictionary to map barge id ot indices
        for i, j in zip(bargeIndices, bargeColumns):
            self.bargeColumnsMap[j] = i

        # give barge indices instead of ids
        uimRaw = uimRaw.rename(columns=self.bargeColumnsMap)

        # Find largest number in row
        df_max = uimRaw.max(axis=1)

        uim = uimRaw.loc[:, bargeIndices].div(df_max, axis=0).round(1) * 10

        # store user item matrix as attribute
        self.uim = uim

        # store other parameters as input
        self.latent_features = latent_features
        self.learning_rate = learning_rate
        self.iters = iters

        # set up useful values to be used through the rest of the function
        self.nVoyages = self.uim.shape[0]
        self.nBarges = self.uim.shape[1]

        self.num_ratings = np.count_nonzero(uim)
        self.voyage_ids_series = np.array(self.uim.index)
        self.barge_ids_series = np.array(self.uim.columns)

        # initialize the voyage and barge matrices with random values
        voyage_mat = np.random.rand(self.nVoyages, self.latent_features)
        barge_mat = np.random.rand(self.latent_features, self.nBarges)

        # initialize sse at 0 for first iteration
        sse_accum = 0

        # keep track of iteration and MSE
        print("Optimisation Statistics")
        print("Iterations | Mean Squared Error ")

        # for each iteration
        for iteration in range(self.iters):

            # update our sse
            old_sse = sse_accum
            sse_accum = 0

            # For each voyage-barge pair
            for i in range(self.nVoyages):
                for j in range(self.nBarges):

                    # if the rating exists
                    if self.uim.loc[i][j] > 0:

                        # compute the error as the actual minus the dot product of the voyage and barge latent features
                        diff = self.uim.loc[i][j] - np.dot(voyage_mat[i, :], barge_mat[:, j])

                        # Keep track of the sum of squared errors for the matrix
                        sse_accum += diff**2

                        # update the values in each matrix in the direction of the gradient
                        for k in range(self.latent_features):
                            voyage_mat[i, k] += self.learning_rate * (2*diff*barge_mat[k, j])
                            barge_mat[k, j] += self.learning_rate * (2*diff*voyage_mat[i, k])

            # print results
            print("%d \t\t %f" % (iteration+1, sse_accum / self.num_ratings))

        # SVD based fit
        # Keep voyage_mat and barge_mat for safe keeping
        self.voyage_mat = voyage_mat
        self.barge_mat = barge_mat

        return voyage_mat, barge_mat
        # Knowledge based fit
  #      self.ranked_barge = rf.find_similar_barge(barge_id, barge_df) # unecertain how this would work


    def predict_rating(self,voyage_id, barge_id):
        '''
        INPUT:
        barge_id - the barge_id from the rating df
        voyage_id - the voyage_id according the voyages df
        barge_df - the database of barges

        OUTPUT:
        pred - the predicted rating for barge_id-voyage_id according to FunkSVD
        '''


        try:# Voyage row and barge Column

            voyage_row = np.where(self.voyage_ids_series == voyage_id)[0][0]
            barge_col = np.where(self.barge_ids_series == barge_id)[0][0]

            # Take dot product of that row and column in U and V to make prediction
            pred = np.dot(self.voyage_mat[voyage_row, :], self.barge_mat[:, barge_col])

            return pred

        except:
            print("I'm sorry, but a prediction cannot be made for this voyage-barge pair.  It looks like one of these items does not exist in our current database.")

            return None


    def validation_comparison(self):
        '''
        Validationtest of the difference between the actual and predicted ratings.

        :return: Root mean squared error, list with actual ratings, list with predict ratings and percentage of data
        that was predicted.
        '''
        val_df = self.uim.stack().reset_index()
        val_df = val_df.rename(columns = {'level_0' : 'voyage', 'level_1' : 'barge', 0 : 'rating'})

        val_voyages = np.array(val_df['voyage'])
        val_barges = np.array(val_df['barge'])
        val_ratings = np.array(val_df['rating'])


        sse = 0
        num_rated = 0
        preds ,acts = [], []

        for idx in range(len(val_voyages)):
            if val_ratings[idx] > 0:
                pred = self.predict_rating(val_voyages[idx],val_barges[idx])

                act = val_ratings[idx]

                sse += (act - pred)**2
                num_rated += 1
                preds.append(pred)
                acts.append(act)
            else:
                continue

        rmse = np.sqrt(sse / num_rated)
        perc_rated = num_rated / len(val_voyages)

        return rmse, perc_rated, preds, acts

    def visualise_validation_comparison(self, rmse, perc_rated, preds, acts):
        '''
        Give visualisation of validation comparison by mapping the difference between the predicted and
        actual ratings. Furthermore, giving the Root Mean Squared Error to determine accuracy of model and
        inform what percentage of data the test was run.
        :param preds:Predicted ratings
        :param acts: actual ratings
        :param rmse: Root mean squared error
        :param perc_rated: Percentage of data that is rated

        :return: Printed statement about RMSE and perc_rated. And a distribution of the difference beteen actuals and
        predicted values
        '''

        print('{} percent of all predicted ratings have been tested. That data reaches between the 0 and 10. '
              'The root mean square error is {}.'.format(round(perc_rated*100,1),round(rmse,5)))
        diff = np.array(preds) - np.array(acts)
        plt.figure(figsize=(8, 8))
        plt.hist(diff, density=True, alpha=.5, label = 'Rating diff');
        plt.legend(loc=2, prop={'size': 15});
        plt.xlabel('Difference in rating');
        plt.title('Distribution of difference between actual and predicted');

        return plt.show()

    def make_recommendations(self, _id, _id_type='barge', rec_num=5):
        '''
        INPUT:
        _id - either a voyage or barge id (int)
        _id_type - "voyage" or "barge" (str)
        rec_num - number of recommendations to return (int)

        OUTPUT:
        recs - (array) a list or numpy array of recommended barge like the
                       given barge, or recs for a voyage given
        '''
        # if the voyage is available from the matrix factorization data,
        # I will use this and rank barges based on the predicted values
        # For use with voyage indexing
        rec_ids, rec_names = None, None
        if _id_type == 'voyage':
            if _id in self.voyage_ids_series:
                # Get the index of which row the voyage is in for use in U matrix
                idx = np.where(self.voyage_ids_series == _id)[0][0]

                # take the dot product of that row and the V matrix
                preds = np.dot(self.voyage_mat[idx,:],self.barge_mat)

                # pull the top barges according to the prediction
                indices = preds.argsort()[-rec_num:][::-1] #indices
                rec_ids = self.barge_ids_series[indices]

                rec_ids = [list(self.bargeColumnsMap)[i] for i in (rec_ids)]
                for i in range(0, len(rec_ids)):
                    rec_ids[i] = int(rec_ids[i])

                rec_names = list(rf.get_barge_names(rec_ids, barge_df)['Name'])

            else:
                # if we don't have this voyage, give just top ratings back
                rec_names = rf.create_ranked_df(self.uim, barge_df) #doesn't give the Id's
                print("Because this voyage wasn't in our database, we are giving back the top barges "
                      "recommendations for all voyages.")

        # Find similar barges if it is a barge that is already occupied
        else:
            if str(_id) in list(self.bargeColumnsMap.keys()):
                rec_ids = list(rf.find_similar_barge(int(_id), barge_df)['Id'])[:rec_num]
                rec_names = list(rf.find_similar_barge(int(_id), barge_df)['Name'])[:rec_num]
            else:
                rec_ids = list(rf.create_ranked_df(uimRaw,barge_df)['Id'])[:rec_num]
                rec_names = list(rf.create_ranked_df(uimRaw,barge_df)['Name'])[:rec_num]
                print("That barge doesn't exist in our database. We only have the highest ranked barges.")

        return rec_ids, rec_names

    if __name__ == '__main__':
        import recommender as r

        # instantiate recommender
        rec = r.Recommender()

        # fit recommender
        rec.fit(barge_df, uimRaw, learning_rate=.01, iters=200)

        # check result of recommendation system factorisation matrix
        rmse, perc_rated, preds, acts = rec.validation_comparison()
        print(rec.visualise_validation_comparison(rmse, perc_rated, preds, acts))

        # test if recommendation system for voyage id gives barges. No assert because of different outcomes.
        print(rec.make_recommendations(277, _id_type='voyage'))

        # test if recommendation system for now barge gives similar barges
        assert rec.make_recommendations(2)[1] == ['Vesta', 'Senda', 'Archelle', 'Waalstroom', 'Bumbastad']

        # test if recommendation system for unknown route and unknown barge gives highest ranked barges
        assert rec.make_recommendations(2301)[1] == ['Presto', 'Endurance II', 'Eiltank 84', 'Company', 'Chris']
        print('Test is a success')