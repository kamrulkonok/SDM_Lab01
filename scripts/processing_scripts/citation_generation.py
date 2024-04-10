"""
Citations : Synthetically generate a number of citations from papers in the existing dataset.
"""

# import libraries
import pandas as pd
import numpy as np
import random
import ast
random.seed(0)


# Function to generate citations for each row
def generate_citations(row, all_paper_ids):
    paper_id = row['paperId']
    cite_number = row['synthetic_cites']
    other_paper_ids = np.delete(all_paper_ids, np.where(all_paper_ids == paper_id)) # Remove the current paperId from the list of all_paper_ids
    citations = list(np.random.choice(other_paper_ids, cite_number, replace=False)) # Randomly select cites_number IDs from other_paper_ids
    return citations


def main():

    # import data
    df_citations = pd.read_csv('../../data/raw_data/papers_semantic_scholar.csv')

    # generate synthetic citations
    random_numbers = np.random.randint(15, 51, size=len(df_citations)) # randomly generate number of papers
    df_citations['synthetic_cites'] = random_numbers # number of cites for each paper
    all_paper_ids = df_citations['paperId'].unique()
    df_citations['Citations'] = df_citations.apply(lambda row: generate_citations(row, all_paper_ids), axis=1) # Apply the function to each row to generate the citations
    df_citations = df_citations.drop(columns=['synthetic_cites'])
    df_citations.to_csv('../../data/processed_data/citations_info.csv', index=False)

if __name__ == "__main__":
    main()


