# Goal
The goal is twofold:
- First it's my capstone project of the data scientist program of Udacity. With it I show my acquired skills in
software engineering, data engineering and building a recommendation system.

- Second is to build a PoC for the barging industry to see if funkSVD could indeed be an effective method for the
planning of barges

# Application

## Installation
The application is build in Python running on a Flask framework and with an MySQL database.

The following library's need to be installed
- Flask
- Jinja2
- PyMySQL
- SQLAlchemy
- Shapely
- Plotly
- Dash
- Numpy
- Pandas
- Polyline

## Access prohibited
The application gets the information from an operating system of a barge operator. Because this information is private
the url isn't shown in the application files. The data for the database can be reviewed in csv
- barges or ships are barge_df.csv
- voyages is dfVoyagesPlan.csv
- from and to locations is ports.csv
- user item matrix is uimRaw.csv

## Working method
The application consists of an ETL process to gather data and recommendation system to recommend barges. Furthermore, it
runs on a Flask framework with an HTML access.

### ETL
The ETL extracts voyage data from a barge operator. These are all the voyages in their database, the current voyages and
the locations a barge has sailed from and to.

Based on this information a user_item_matrix is created the voyage routes are the users and the barges are
the items. This gives an overview of the most sailed routes per barge.

After extraction and transformation the data is saved in a MySQL database. Tables are voyage ports, ships (barges),
user_item_matrix and voyage_plan.

I've extracted the barge information in a different method. See
[Medium](https://medium.com/@frank.landheer/a-complete-barge-directory-cf97edef3e59) for further information.

### Recommendation
The recommendation consists of two modules, the recommender and recommender_functions. The recommender functions
retrieves important information like barge names or voyage ids. It also consists of simple recommendation scripts like
finding similar barges or ranking barges.

The recommender module offers a class that fits an funkSVD model on the barge voyages. Based on the barge information
and voyage information it creates latent features and predicts the 'rating' of a voyage. The rating is determine by how
often a barge was used for a voyage. More voyage means a higher rating. The user_item_matrix is normalized for that
purpose.

### Webscreens
The webscreens offer an overview of available barges and a method to request barges. When selecting a from and to port
the recommender will search for the voyage and based on the prediction and the distance of the barge towards the load
location is recommends 5 barges. The voyage "Rotterdam" to "Geertruidenberg" will result in such a recommendation.

If the voyage isn't found the recommender will give the highest ranked barges. If a prefered barge is mentioned the
recommender will search for the barges most similar to the one given.

# Project definition
Transportation of inland waterways is an important aspect of the logistic supply chain in Western Europe. Thousands
of barges transport millions tonnage of cargo everyday, like agriculture products (dry bulk), commercial products
(containers), oil and minerals (wet bulk) or parts of wind mills (break bulk). This market is controlled by brokers
who are responsible for gathering cargo transport assignments and offering them to barge operators. Finding correct
barges for a specific assignment depends on barge properties, availability and position. Can it carry the cargo between
the load and discharge location? Is it available? And will it be on time?

This is a specific knowledge and therefore brokers are highly sought after and preserved when part of a company. Online
services are highly effective in offering recommendations. The streaming service netflix for instance, who uses
funkSVD to improve their recommendation system for movies or TV shows.

## Problem statement
Is it possible to build a recommendation system for inland barges based on the systems content, rank and funkSVD?

### Strategy for solving the problem
1. Is it possible to gather information needed to build a recommendation system?
To answer this question planning information is retrieved from a barge operating system from a barge operator. This
system has an API available on request.

2. Is it possible to transform the data such that it can support a recommendation system?
Barges have specific proporties that can be used to match them with other barges and therefore find similar ones. The
barge data should be good enough to proof this.

Netflix uses a ranking system. Barge however aren't directly ranked on their performance by users. They do however sail
routes. Certain routes more often then other routes. In stead of using a classic user_item_matrix, in this case we
would use a route_barge_matrix. The idea would be, if a barge is used often for a route, it his an higher ranking and
therefore more suited to sail that route again. As would similar barges.

There are some disadvantages to this logic when predicting ratings. Rating a barge on how often it sails a route does
imply that it's suited for the job, but an exact copy of that barge could have sailed that same route once and would
get a bad rating. This is a limitation that we except for this proof of concept.

Another disadvantages is the data. A broker has his relation fleet which consists of own barges, barges under contract
and preferred barges. Most data bases of barge operators will consist of routes from these barges. But having a lot
of other barges in the market and in the database would mean that the database won't have that much data to train the
model on. This could be solved, but is out of scope for this proof of concept.

3. Is it possible to build a recommendation system?
For the current strategy the recommendation system will be build based on rank, content and recommendations. There are,
however, more parameters to consider.

- Brokers have contracts with certain barges and would like to use these before they would use barges from the market.
Own barges have priority.
- Barges should be available, shouldn't be planned for a voyage.
- Barges should be able to carry the specific product.

These limitations or filters are out of scope for this version of the product.

4. Is it possible to build a web application that can be used to recommend barges for voyages?
For the first version the web application should be simple. We would like to have access to the master data
(barges, locations and voyages) and do a recommendation request. It should be possible to get a request based on:
- Rank
- Content
- Recommendation

5. Are we able to proof the effectiveness of the recommendation system?
The effectiveness of a recommendation system can be evaluated based:

- User studies
Plan would be to have the barge operator, who shared their data, to test the system in an enclosed environment. Giving
the voyage plan and unplanned voyages. Plus giving them the assignment to plan them with the recommendation system.
Would the use the recommendation?

- Online evaluations (A/B test)
We can also execute a A / B test. Running the recommendation system every day based on the situation of the barge
operator before they plan the barges and see if the recommendation and actual plan overlaps. Even better would be to
mirror the planning, while planning.

- Offline evaluations
We can use the root mean square error to evaluate the accuracy of the matrix factorisation.

For this project the offline evaluation is executed.

# Analysis
There're to important datasets for this problem. First are the barge data and second is the user_item_matrix. The
barge data. As we can see in the ship_recommendation > etl > data > Barge.html file the visualisation of the dataset.
In this case around 3/5 of the data needed was missing, especially about the cargo capacity of the barge.
Based on the dimensions of the barge it was possible to create a linear regression problem and by using an Ordinary
Least Squares model strongest relations between features and labels could be determined. With a machine learning
pipeline three classifier models were evaluated. Concluding that a randomForestClassifier was the best model to fill the
null values. For ***Analysis*** ***Methodology*** and ***Results*** please view the mentioned Barge.html document.
Second problem is the user_item_matrix which consists of null values for 93% of the cases. Because the matrix is based
on the route database of the barge operators all routes do have some values and can be used to make predictions.

# Methodology
Preprocessing of the data is done with the transform_voyage_data module. This module creates a user_item_matrix by
requesting all voyages from the barge operators database (extract_voyage_data) and pivoting these voyages in a table.
The biggest problem with this matrix. The barges sail between addresses, which made the matrix really large.
For the problem, finding recommendations for routes for inland shipping, the addresses isn't the detail level
necessary, it could also be a port to port route. Therefore the transform_voyage_data takes the lat / long from the
addresses and maps them to a port are based on the Polygon. This minimises the matrix and null values without loosing
valuable data.

# Result
Fine tuning the funkSVD algorithm was mainly trail and error. With an latent_feature number of 12 and 200 iterations
the means squared error ended on 0.00001, which should give good results. As you can see
![training1 svd](/images/TrainingfunkSVDmodel1of2.png)


![training2 svd](/images/Train funkSVD model 2of2.png)

This image als also shows the validation with testing the Root Mean Squared Error, which is 0.00312. The distribution
of differences between actual and predicted ratings show a low variance. Keep in mind that the numbers could range
between the 0 and 10. This all shows that the predict model is highly reliable for at least predicting the known
ratings.
Als in this image are the automated tests for the ranked and content based recommendation system. These results will
also show in the webscreens

The landing page of the webscreens shows a table with all barge information
[barges](/images/Landing page.png)

When we select the recommendation link in the header we get the opportunity to fill in information and activate the
recommendation system. We also see the current voyageplan. Due to privacy reasons the barges have aliases.
![recommendationpage](/images/Select information to get recommendation.png)

Result when selecting route 277, Rotterdam to Geertruidenberg. Recommendation based on funkSVD
![funkSVDRecommendation](/images/recommendation voyage with id 277 sorted on closest positions from port.png)

Result when selection known barge 2. Recommendation based on content.
![bargeRecommendation](/images/Recommendation barge with id 2 sorted on closest positions from port.png)

Result when selecting unknown barge. Recommendation based on rank.
![unknwonBargeRecommendation](/images/Recommendation highest ranked barges sorted on closest positions from port.png)


For a data scientist it's interesting to test the funkSVD method on a logistical problem. There are, however, some down-
sides. First of all the cold start problem. New routes won't have barge registrations, which leaves us in the dark.
This is now tackled by the ranked and content recommendation. However, all barges have and share GPS positions which can
be retrieved by providers as vesselfinder.com . This gives as access to big database that can analyse and retrieve barge
movements for routes. This could improve the lack of data.

Furthermore, this recommendation system is build on a single demand and supply problem. Can you transport this cargo
with that barge? To optimise planning we shouldn't look at a single barge, but at a fleet of barges and consider metrics
like fleet capacity, minimal sailing routes and minimising costs. For a machine learning approach reinforcement learning
offers a promising solution. Still, this is for barges that are planned to carrier one cargo as is usual in the bulk
transport. If we don't plan barges entirely full, but fill it up with containers, than a heuristic approach could also
be sufficient or at least should support an machine learning model.

# Conclusion
This project had two goals:
1. show case my acquired skills in software engineering, data engineering and building a recommendation system.
2. Build a PoC for the barging industry to see if funkSVD could indeed be an effective method for the planning of barges

To reach this goal I've set up an ETL pipeline to fill a database and build a recommendation system based on content,
rank and a factorisation matrix. This system is build in a FLASK framework which means it has a front end and is suited
to publish on the web. During this project I've encountered multiple challenges.

ETL - The API that I used worked with pagination, which means I had to figure out how to loop through pages and extract the
information. This does take extra time for the system. A improvement of the could would by to iterate only through id
fields first and match those with the entities already stores, such that the more elaborate loops can be used for new
data.
That would also be another improvement. When placing it on a webserver, build in a cronjob to run the ETL periodically.

Recommender - During the recommendation I saw that the algorithm build during wasn't suitable for this case because of
the context of the problem and the data structure. I needed to adjust multiple elements and really think through the
process to obtain a fundamental understanding of making predictions with SVD. I'm confident in my code. The results of
the code is good, maybe a bit too good. I'm  looking for a method to better evaluate.
I've created a class from scratch for the recommendation to acquire experience with the part of coding. Although I've
learned a lot from this, I should take more time to find the benefits of class for this situation.

Web application - Building the web app from scratch has given me a better understanding of the connection between
back end and front end. My FLASK, Plotly and HTML skills did improve.

## Improvements
The following improvements can be made:

- Find a way that the webapp doesn't break if you ask for second recommendation;
- Add progress bar in webapp to give feedback to the user that the monkeys are working on the problem;
- Add relation type to barges to see if it is an own barge;
- Add more categories to barge, like owner, to improve content based recommendation;
- Implement function recommender_function.available_barges() in the recommendation to filter barges on availabilities;
- Build in a cronjob to update at least daily;
- Build an ETL for extracting unplanned routes so you can set up an online evaluations (A/B test);
- Adjust the barge table in on the webscreen with pagination and search options;



