This repo contains the (updated) code  we used to replicate the results of Buehlmaier and Whited (2014) now published in the Review of Financial Studies [here](https://doi.org/10.1093/rfs/hhy007). 

### Abstract
The aim of our term paper is to replicate the results of Buehlmaier and Whited (2014) , that is, to examine the pricing implications of financial constraints. One of the contributions of Buehlmaier and Whited's paper is to build a novel measure of financial constraints by textually analyzing the 10-K forms of U.S. listed firms. We follow the same methodology and apply two extensions. First, in the field of textual analysis there exist statistically better algorithms than the one used in the original paper. Thus, in addition to naive Bayes we also apply a support vector machine algorithm to the problem of classifying financially constrained and unconstrained firms. Second, as of today, more data is available and we extend the data period by 4 years.

###### How

The code takes the list of CIKs from the input folder, and searches all the available 10-Ks in Edgar filed in the specified date range. It cleans, stems the MD&A section of these 10-Ks, and extracts the feature vectors by using bag of words derived from the keyword lists available in the inputs folder. Finally,  it pickle the data, trains and estimate SVM and Naive Bayes to classify financially constrained firms.

###### To Do

Upload classification algorithm, implement multi-process and multi-threading to speed up download and feature extraction.