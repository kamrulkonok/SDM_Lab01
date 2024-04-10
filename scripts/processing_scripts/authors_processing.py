"""
This script generates the `authors_info.csv`.
The schema consists of the following columns : 
    - authorId (unique Id for the author)
    - name (name of the author)
    - Affiliations (organization to which the author is affiliated to)
    - Affiliation_type (organization type : company or university)
"""

# import libraries
import pandas as pd
import numpy as np
import random
random.seed(0) # to generate the same data output

# import data
df_authors = pd.read_csv('../../data/raw_data/authors_semantic_scholar.csv')
df_authors = df_authors.dropna(subset=['authorId']) # remove paperIds without any authorId
df_authors = df_authors.drop_duplicates(subset=['authorId']) # remove duplicate rows from data
df_authors['authorId'] = df_authors['authorId'].astype(int) # converting the authorId to integer values
df_authors = df_authors[['authorId', 'name']] # remove paperId column


df_university = pd.read_csv('../data/raw_data/universities_list.csv')
df_company = pd.read_csv('../data/raw_data/companies_list.csv')


universities = df_university['Institution Name'][1:51].tolist() # top 50 universities
companies = df_company['company'][:50].tolist() # top 50 companies


# populate the 'Affiliations' & 'Affiliation_type' column synthetically from university and company data
data_length = len(df_authors) # number of authors
affiliations = random.choices(universities + companies, k=data_length)
df_authors['Affiliations'] = affiliations
df_authors['Affiliation_type'] = df_authors['Affiliations'].apply(lambda x: 'university' if x in universities else 'company')

# save data to directory
df_authors.to_csv('../../data/processed_data/authors_info.csv', index=False)



