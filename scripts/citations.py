import csv
import pandas as pd
import requests

df = pd.read_csv('papers_data.csv')
paper_ids = df['paperId'].unique()

def get_paper_data(paper_id, api_key):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
    
    params = {
        "fields": "citations.paperId,citations.authors"
    }
    
    headers = {
        "x-api-key": api_key
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        citations = []
        for citation in data.get("citations", []):
            citation_id = citation.get("paperId")
            authors = citation.get("authors", [])
            author_details = [{"authorId": author.get("authorId"), "name": author.get("name")} for author in authors]
            citations.append({"citationId": citation_id, "authors": author_details})
        
        return {"paperId": paper_id, "citations": citations}
    else:
        return {"error": "Failed to retrieve data for paper ID {}: status code: {}".format(paper_id, response.status_code)}

# API key
api_key = "QBCOvr5LpG5R231Hcyc5a1wYmv3kltNy40sKfufK"
all_citations_data = [get_paper_data(paper_id, api_key) for paper_id in paper_ids]
all_citations_data = [get_paper_data(paper_id, api_key) for paper_id in paper_ids]

with open('citations_data.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['paperId', 'citationId', 'authorIds', 'authorNames'])
    
    for paper in all_citations_data:
        if "error" not in paper:
            for citation in paper["citations"]:
                # Filtering out None authorId values and converting each authorId to string
                author_ids = "; ".join([str(author["authorId"]) for author in citation["authors"] if author["authorId"] is not None])
                # Filtering out None author names and converting each name to string
                author_names = "; ".join([str(author["name"]) for author in citation["authors"] if author["name"] is not None])
                writer.writerow([paper["paperId"], citation["citationId"], author_ids, author_names])

print("Citation data has been saved to citations_data.csv")

