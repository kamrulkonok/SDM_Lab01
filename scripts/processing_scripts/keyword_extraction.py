"""
This script extracts the main keywords present in the papers.
"""
# import libraries
import pandas as pd
import spacy
from collections import Counter
import string

# Load the SpaCy English language model
nlp = spacy.load('en_core_web_sm')

def preprocess_text(text):
    # preprocess text by lowering case, removing punctuation and stopwords.
    text = str(text).lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    return ' '.join(tokens)

def extract_keywords(text, field_query, n=4):
    # extract keywords from text using SpaCy for NLP processing, including the field_query.
    processed_text = preprocess_text(text)
    doc = nlp(processed_text)
    words = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]  # Extract nouns and proper nouns
    words.append(field_query.lower())
    most_common_words = [word[0] for word in Counter(words).most_common(n)]
    if field_query.lower() not in most_common_words:
        most_common_words.pop()
        most_common_words.append(field_query.lower())
    return most_common_words

def main():
    file_path = '../../data/raw_data/papers_semantic_scholar.csv'
    papers_data = pd.read_csv(file_path)
    papers_data['keywords'] = papers_data.apply(lambda x: extract_keywords(x['abstract'], x['field_query']), axis=1)
    keywords_info = papers_data[['paperId', 'keywords']]
    keywords_info.to_csv('../../data/processed_data/paper_keywords.csv', index=False)

if __name__ == "__main__":
    main()



