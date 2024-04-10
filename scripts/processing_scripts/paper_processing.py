"""
Create the paper processing data.
"""

# import libraries
import ast
import random
import pandas as pd
import numpy as np
random.seed(0)

def preprocess_data_minor(df_papers):
    # fix small issues in data
    df_papers.loc[df_papers['field_query'] == ' Big Data', 'field_query'] = 'Big Data' # Fixed Big Data spacing issue

    # drop null rows from the data
    df_papers = df_papers.dropna(subset=['venue'])
    df_papers = df_papers.dropna(subset=['publicationTypes'])
    df_papers = df_papers.dropna(subset=['abstract'])
    df_papers = df_papers.drop(columns=['journal_pages'])
    df_papers = df_papers.dropna(subset=['journal_volume'])

    return df_papers


def aggregate_paper_authors(df_authors, df_papers):

    # put all authors of each paper in a list
    df_authors = df_authors.dropna(subset=['authorId'])
    df_author_paper = df_authors.groupby('paperId')['authorId'].agg(list).reset_index()
    df_papers = pd.merge(df_papers, df_author_paper, on='paperId', how='left')
    df_papers.rename(columns={'authorId': 'authorIds'}, inplace=True)
    df_papers = df_papers.dropna(subset=['authorIds'])
    return df_papers

def extract_corresponding_author(df_papers):

    # assumption is that the first author is the corresponding author
    df_papers['corresponding_author'] = df_papers['authorIds'].apply(lambda x: x[0])
    return df_papers

def add_location(df_cities, df_papers):
    capitals = df_cities['capital'].tolist() # Add Location
    df_papers['location'] = [random.choice(capitals) for _ in range(len(df_papers))]
    return df_papers

def paper_approval(df_papers):
    # since paper is published or accepted, therefore assumption is that it is approved
    df_papers['approved'] = 'Y'
    return df_papers


def categorize_publication(df_papers):

    workshop_rows = df_papers[df_papers['venue'].fillna('').str.contains('Workshop')]
    df_papers.loc[workshop_rows.index, 'publicationTypes'] = "['Workshop']"
    conference_rows = df_papers[df_papers['publicationTypes'].fillna('').str.contains('Conference')]
    df_papers.loc[conference_rows.index, 'publicationTypes'] = "['Conference']"
    allowed_values = ["['JournalArticle']", "['Conference']", "['Workshop']"]
    df_papers = df_papers[df_papers['publicationTypes'].isin(allowed_values)]
    df_papers['publicationTypes'] = df_papers['publicationTypes'].str[2:-2]
    mask = df_papers['publicationTypes'].isin(['Workshop', 'Conference'])
    df_papers.loc[mask, 'journal_volume'] = "" # empty string as conference and workshops don't have journals
    return df_papers


# Function to select reviewer IDs for each row
def select_reviewers(row):

    author_ids = row['authorIds']
    num_reviewers = row['number_reviewers']
    reviewers = []
    all_author_ids = set(df_papers['authorIds'].explode())
    potential_reviewers = list(all_author_ids - set(author_ids))
    if potential_reviewers:
        reviewers = random.sample(potential_reviewers, min(num_reviewers, len(potential_reviewers)))  # Use num_reviewers instead of 3
    if any(reviewer_id in author_ids for reviewer_id in reviewers):
        print("Warning: Reviewer ID overlaps with Author ID for row with paperId:", row['paperId'])

    return reviewers


def select_review_texts(row, df_reviews):

    # create a new column 'review_texts' containing a list of review texts for each row
    num_reviews = row['number_reviewers']
    all_reviews = list(df_reviews['Text'])
    return random.sample(all_reviews, num_reviews)


def set_proceedings(row):

    if row['publicationTypes'] in ['Conference', 'Workshop']:
        return row['venue']
    else:
        return np.nan

def set_edition(df_papers):

    df_papers['edition'] = df_papers['proceedings'].str.extract(r'(\d+)(?:st|nd|rd|th)') # use proceedings first
    df_papers['edition'] = df_papers['journal_name'].str.extract(r'(\d+)(?:st|nd|rd|th)') # use journal data next
    # Create a boolean mask to identify rows where 'proceedings' is not NaN but 'edition' is NaN
    mask = (df_papers['proceedings'].notna()) & (df_papers['edition'].isna())
    # Update 'edition' column for rows satisfying the condition
    df_papers.loc[mask, 'edition'] = df_papers.loc[mask, 'year'].astype(str).str[-2:]
    return df_papers

def set_journalname(row):

    if row['publicationTypes'] == 'JournalArticle':
        return row['venue']
    else:
        return np.nan

def add_string_to_list(row):

    row['keywords'].append(row['field_query'])
    return row['keywords']


def preprocess_data_major(df_papers):

    df_papers['authorIds'] = df_papers['authorIds'].apply(ast.literal_eval)
    df_papers['reviewers'] = df_papers['reviewers'].apply(ast.literal_eval)
    df_papers['comments'] = df_papers['comments'].apply(ast.literal_eval)
    df_papers['keywords'] = df_papers['keywords'].apply(ast.literal_eval)
    df_papers['corresponding_author'] = df_papers['corresponding_author'].astype(int)
    df_papers['authorIds'] = df_papers['authorIds'].apply(lambda lst: ', '.join(map(str, map(int, lst))))
    df_papers['reviewers'] = df_papers['reviewers'].apply(lambda lst: ', '.join(map(str, map(int, lst))))
    df_papers['comments'] = df_papers['comments'].apply(lambda x: ';'.join(x))
    df_papers['keywords'] = df_papers['keywords'].apply(lambda x: ','.join(x))
    df_papers = df_papers.drop_duplicates(subset=['paperId'])
    return df_papers

def split_workshop(df_papers):

    df_workshop = df_papers[df_papers['publicationTypes'] == 'Workshop'].copy()
    df_workshop = df_workshop.drop(columns=['field_query', 'journal_volume', 'journal_name'])
    df_workshop['edition'] = df_workshop['edition'].astype(int)
    return df_workshop

def split_conference(df_papers):

    df_conference = df_papers[df_papers['publicationTypes'] == 'Conference'].copy()
    df_conference = df_conference.drop(columns=['field_query', 'journal_volume', 'journal_name'])
    df_conference['edition'] = df_conference['edition'].astype(int)
    return df_conference

def split_journal(df_papers):

    df_journal = df_papers[df_papers['publicationTypes'] == 'JournalArticle'].copy()
    df_journal = df_journal.drop(columns=['field_query', 'proceedings', 'edition'])
    return df_journal

def data_generation(df_conference):
    # to synthetically generate additional data for query 2
    df = df_conference.copy()
    df['edition'] = df['edition'] - 1
    df['year'] = df['year'] - 1
    df['paperId'] = df['paperId'] + 'a'
    df_conference = df_conference.append(df, ignore_index=True)
    return df_conference

def main():

    # import data
    df_papers = pd.read_csv('../../data/raw_data/papers_semantic_scholar.csv')
    df_authors = pd.read_csv('../../data/raw_data/authors_semantic_scholar.csv')
    df_cities = pd.read_csv('../../data/raw_data/europe-capital-cities.csv')
    df_reviews = pd.read_csv('../../data/raw_data/reviewer_comments.csv')
    df_keywords = pd.read_csv('../../data/processed_data/paper_keywords.csv')
    df_citations = pd.read_csv('../../data/processed_data/citations_info.csv')


    df_papers = preprocess_data_minor(df_papers) # clean up data
    df_papers = aggregate_paper_authors(df_authors, df_papers) # aggregate authors
    df_papers = extract_corresponding_author(df_papers) # extract corresponding author
    df_papers = add_location(df_papers) # Add location data
    df_papers = paper_approval(df_papers) # paper acceptance
    df_papers = categorize_publication(df_papers) # categorize as conference, workshop or journal

    # for reviewers
    df_papers['number_reviewers'] = np.random.choice([2, 3], size=len(df_papers)) # select number of reviewers for a publication
    df_papers['reviewers'] = df_papers.apply(select_reviewers, axis=1)
    df_papers['comments'] = df_papers.apply(lambda row: select_review_texts(row, df_reviews), axis=1)

    # edition & proceedings
    df_papers['proceedings'] = df_papers.apply(lambda row: set_proceedings(row), axis=1)
    df_papers = set_edition(df_papers)

    # journal name & volume
    df_papers['journal'] = df_papers.apply(lambda row: set_journalname(row), axis=1)

    # rename and remove columns
    df_papers.drop(columns=['venue'], inplace=True)
    df_papers.drop(columns=['journal_name'], inplace=True)
    df_papers.rename(columns={'journal': 'journal_name'}, inplace=True)
    df_papers.rename(columns={'location': 'venue'}, inplace=True)

    # keywords
    df_papers = pd.merge(df_papers, df_keywords, on='paperId', how='inner')
    df_papers['keywords'] = df_papers['keywords'].apply(ast.literal_eval)
    df_papers['keywords'] = df_papers.apply(add_string_to_list, axis=1)
    df_papers['keywords'] = df_papers['keywords'].str.lower()

    # citations
    df_citations['Citations'] = df_citations['Citations'].apply(ast.literal_eval)
    df_citations['Citations'] = df_citations['Citations'].apply(lambda x: ', '.join(map(str, x)))
    df_citations = df_citations.drop_duplicates(subset=['paperId'])
    df_papers = pd.merge(df_papers, df_citations, how='inner', on='paperId')

    # split on publication type
    df_workshop = split_workshop(df_papers)
    df_conference = split_conference(df_papers)
    df_journal = split_journal(df_papers)

    # additional data generated for query 2 for conference
    df_conference = data_generation(df_conference)

    # Save to csv
    df_workshop.to_csv('../../data/processed_data/workshop_info.csv', index=False)
    df_conference.to_csv('../../data/processed_data/conference_info.csv', index=False)
    df_journal.to_csv('../../data/processed_data/journal_info.csv', index=False) 

if __name__ == "__main__":
    main()
