from neo4j import GraphDatabase
from load_config import load_config

class DataLoader:
    def __init__(self, config):
        self.driver = GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], config['password']),
            encrypted=False
        )

    def close(self):
        """Close the Neo4j database connection."""
        self.driver.close()

    def load_csv_data(self, csv_path, load_function):
        with self.driver.session() as session:
            session.execute_write(load_function, csv_path)

    @staticmethod
    def _load_authors(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (a:Author {{authorId: row.authorId}})
        ON CREATE SET a.name = row.name, a.affiliation = row.Affiliations,
        a.affiliationType = row.Affiliation_type
        """
        tx.run(query)
    @staticmethod
    def _load_papers(tx, csv_filename):
        query_papers = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (p:Paper {{paperId: row.paperId}})
        ON CREATE SET p.title = row.title, p.url = row.url, p.abstract = row.abstract,
                    p.year = toInteger(row.year), p.citationCount = toInteger(row.citationCount)
        """
        tx.run(query_papers)

    @staticmethod

    def _load_authors_relations(tx, csv_filename):
        query_authors = f"""
    LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
    MATCH (p:Paper {{paperId: row.paperId}})
    UNWIND split(row.authorIds, ',') AS authorId
    MATCH (a:Author {{authorId: trim(authorId)}})
    MERGE (a)-[r:WROTE]->(p)
    SET r.corresponding = CASE WHEN row.corresponding_author = authorId THEN true ELSE false END
    """
        tx.run(query_authors)
    @staticmethod
    def _load_publication_venues(tx, csv_filename, venue_type):
        name_property = 'journal_name' if venue_type == 'Journal' else 'proceedings'

        relationship_properties = {
            'Conference': ", edition: toInteger(row.edition), venue: row.venue",
            'Journal': ", edition: toInteger(row.edition), journal_volume: row.journal_volume, venue: row.venue",
            'Workshop': ", edition: toInteger(row.edition), venue: row.venue"
        }
        query_venue = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        WHERE NOT row.{name_property} IS NULL AND row.{name_property} <> ''
        MERGE (v:{venue_type} {{name: row.{name_property}}})
        WITH p, v, row
        MERGE (p)-[r:PUBLISHED_IN]->(v)
        SET r.year = toInteger(row.year), r.edition = toInteger(row.edition), r.venue = row.venue
        """

        if venue_type == 'Journal':
            query_venue += "SET r.journal_volume = row.journal_volume"
        
        tx.run(query_venue)

    @staticmethod
    def _load_citations(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        WHERE row.Citations IS NOT NULL AND row.Citations <> ''
        UNWIND split(row.Citations, ',') AS citationId
        WITH p, trim(citationId) AS trimmedCitationId
        MERGE (cited:Paper {{paperId: trimmedCitationId}})
        MERGE (p)-[:CITES]->(cited)
        """
        tx.run(query)
    
    # Method to load keywords
    @staticmethod
    def _load_keywords(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        UNWIND split(row.keywords, ',') AS keyword
        MERGE (k:Keyword {{text: keyword}})
        """
        tx.run(query)
    @staticmethod
    def _load_keywords_and_relations(tx, csv_filename, delimiter=','):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND split(row.keywords, '{delimiter}') AS keyword
        WITH p, trim(keyword) AS trimmedKeyword
        WHERE trimmedKeyword IS NOT NULL AND trimmedKeyword <> '' 
        MERGE (k:Keyword {{text: trimmedKeyword}})
        MERGE (p)-[:CONTAINS]->(k)
        """
        tx.run(query)
        
    # Method to create 'Reviewed' relationships
    @staticmethod
    def _load_reviews(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND split(row.reviewers, ',') AS reviewerId
        MATCH (r:Author {{authorId: reviewerId}})
        MERGE (r)-[review:REVIEWED]->(p)
        ON CREATE SET review.approved = row.approved, review.comments = row.comments
        """
        tx.run(query)

    @staticmethod
    def _load_authors_and_affiliations(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (a:Author {{authorId: row.authorId}})
        ON CREATE SET a.name = row.name, a.affiliationType = row.Affiliation_type
        WITH a, row
        MERGE (o:Organization {{name: row.Affiliations}})
        MERGE (a)-[:AFFILIATED_TO]->(o)
        """
        tx.run(query)

if __name__ == "__main__":
    config = load_config()
    loader = DataLoader(config)
    loader.load_csv_data("conference_info.csv", DataLoader._load_papers)
    loader.load_csv_data("journal_info.csv", DataLoader._load_papers)
    loader.load_csv_data("workshop_info.csv", DataLoader._load_papers)
    loader.load_csv_data("conference_info.csv", lambda tx, csv_path: DataLoader._load_publication_venues(tx, csv_path, 'Conference'))
    loader.load_csv_data("journal_info.csv", lambda tx, csv_path: DataLoader._load_publication_venues(tx, csv_path, 'Journal'))
    loader.load_csv_data("workshop_info.csv", lambda tx, csv_path: DataLoader._load_publication_venues(tx, csv_path, 'Workshop'))
    loader.load_csv_data("authors_info.csv", DataLoader._load_authors)
    loader.load_csv_data("journal_info.csv", DataLoader._load_authors_relations)
    loader.load_csv_data("workshop_info.csv", DataLoader._load_authors_relations)
    loader.load_csv_data("conference_info.csv", DataLoader._load_authors_relations)
    loader.load_csv_data("conference_info.csv", DataLoader._load_citations)
    loader.load_csv_data("journal_info.csv", DataLoader._load_citations)
    loader.load_csv_data("workshop_info.csv", DataLoader._load_citations)
    loader.load_csv_data("conference_info.csv", DataLoader._load_reviews)
    loader.load_csv_data("journal_info.csv", DataLoader._load_reviews)
    loader.load_csv_data("workshop_info.csv", DataLoader._load_reviews)
    loader.load_csv_data("authors_info.csv", DataLoader._load_authors_and_affiliations)
    loader.load_csv_data("conference_info.csv", lambda tx, path: DataLoader._load_keywords_and_relations(tx, path))
    loader.load_csv_data("journal_info.csv", lambda tx, path: DataLoader._load_keywords_and_relations(tx, path))
    loader.load_csv_data("workshop_info.csv", lambda tx, path: DataLoader._load_keywords_and_relations(tx, path))
    loader.close()