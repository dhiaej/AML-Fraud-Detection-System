class Neo4jConnector:
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def find_laundering_rings(self):
        query = """
        MATCH (a:User)-[t:TRANSACTION]->(b:User)-[t2:TRANSACTION]->(c:User)-[t3:TRANSACTION]->(a)
        WHERE a.user_id <> b.user_id AND b.user_id <> c.user_id AND c.user_id <> a.user_id
        RETURN a, b, c
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [{"a": record["a"], "b": record["b"], "c": record["c"]} for record in result]