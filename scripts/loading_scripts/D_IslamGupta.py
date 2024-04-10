from neo4j import GraphDatabase
from load_config import load_config

class GraphAlgorithms:
    def __init__(self, config):
        """ Initialize the database connection """
        self.driver = GraphDatabase.driver(
            config["uri"], 
            auth=(config["user"], config["password"]),
            encrypted=False
        )

    def close(self):
        """ Close the Neo4j database connection """
        self.driver.close()

    def execute_query(self, query):
        with self.driver.session() as session:
            return [record for record in session.run(query)]

    def project_graph(self, graph_name):
        query = f"""
        CALL gds.graph.project(
            '{graph_name}',
            ['Paper', 'Author'],
            {{
                WROTE: {{type: 'WROTE', orientation: 'NATURAL'}}
            }}
        )
        YIELD graphName, nodeCount, relationshipCount
        """
        result = self.execute_query(query)
        print(f"Graph '{graph_name}' projected successfully with {result[0]['nodeCount']} nodes and {result[0]['relationshipCount']} relationships.")


    def run_pagerank(self, graph_name):
        """ Run the PageRank algorithm on the specified graph """
        query = f"""
        CALL gds.pageRank.stream('{graph_name}')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).paperId AS paperID, score
        ORDER BY score DESC
        LIMIT 10
        """
        results = self.execute_query(query)
        print("PageRank scores:")
        for result in results:
            paperID = result.get("paperID")
            score = result.get("score")
            print(f'Paper ID: {paperID}, Score: {score}')

    def run_scc(self, graph_name):
        """ Run the Strongly Connected Components algorithm """
        query = f"""
        CALL gds.scc.stream('{graph_name}')
        YIELD nodeId, componentId
        RETURN gds.util.asNode(nodeId).paperId AS paperID, componentId
        ORDER BY componentId DESC
        LIMIT 10
        """
        results = self.execute_query(query)
        print("Strongly Connected Components:")
        for result in results:
            paperID = result.get("paperID")
            componentId = result.get("componentId")
            print(f'Paper ID: {paperID}, Component ID: {componentId}')

if __name__ == "__main__":
    config = load_config()
    graph_algo = GraphAlgorithms(config)

    graph_name = "Hola" 

    graph_algo.project_graph(graph_name)

    graph_algo.run_pagerank(graph_name)
    graph_algo.run_scc(graph_name)

    graph_algo.close()
