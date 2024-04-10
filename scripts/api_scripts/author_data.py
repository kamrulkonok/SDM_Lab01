import csv
import pandas as pd
import requests
df = pd.read_csv('papers_data.csv')
paper_ids = df['paperId'].unique()

headers = {
    'x-api-key': 'QBCOvr5LpG5R231Hcyc5a1wYmv3kltNy40sKfufK'
}

def get_authors_data(paper_id, headers):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/authors"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if 'data' in response_data: 
            authors = response_data['data']
            return [{
                'paperId': paper_id,
                'authorId': author.get('authorId'), 
                'name': author.get('name'),
                'affiliations': '; '.join([aff.get('name', '') for aff in author.get('affiliations', [])])  # Safely handling affiliations
            } for author in authors]
        else:
            print(f"No author data found for paper ID {paper_id}")
            return []
    else:
        print(f"Failed to fetch data for paper ID '{paper_id}': {response.status_code}, Response: {response.text}")
        return []

authors_data = []
for paper_id in paper_ids:
    authors_data.extend(get_authors_data(paper_id, headers))

filename = 'authors_data.csv'
headers = ['paperId', 'authorId', 'name', 'affiliations']

with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    for author in authors_data:
        writer.writerow(author)

print(f"Author data has been saved to {filename}")
