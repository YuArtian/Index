"""
Graph service - manages knowledge graph in Neo4j.

Handles concept extraction from document chunks and graph CRUD operations.
"""

from dataclasses import dataclass

import anthropic
from loguru import logger
from neo4j import AsyncGraphDatabase, AsyncDriver


@dataclass
class Concept:
    name: str
    category: str
    description: str


@dataclass
class Relation:
    source: str
    target: str
    relation: str


@dataclass
class ExtractionResult:
    concepts: list[Concept]
    relations: list[Relation]


class GraphService:
    """Service for managing the knowledge graph in Neo4j."""

    def __init__(self, uri: str, user: str, password: str, anthropic_api_key: str):
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self._client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

    async def close(self):
        await self._driver.close()

    async def verify_connection(self):
        """Verify Neo4j is reachable."""
        async with self._driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            record = await result.single()
            return record["n"] == 1

    async def setup_constraints(self):
        """Create uniqueness constraint on Concept name."""
        async with self._driver.session() as session:
            await session.run(
                "CREATE CONSTRAINT concept_name IF NOT EXISTS "
                "FOR (c:Concept) REQUIRE c.name IS UNIQUE"
            )
        logger.info("Neo4j constraints created")

    # ------------------------------------------------------------------
    # Concept extraction via Claude
    # ------------------------------------------------------------------

    async def extract_concepts(self, text: str) -> ExtractionResult:
        """Use Claude to extract concepts and relations from text."""
        response = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"""从以下文本中提取知识概念和它们之间的关系。

要求：
1. 概念名称要简洁、规范化（如"React Fiber"而不是"React的Fiber架构"）
2. 类别从以下选择：技术、概念、工具、语言、框架、算法、设计模式、原理、人物、其他
3. 关系要具体（如"使用了"、"属于"、"实现了"、"依赖"、"对比"、"包含"）
4. 只提取文本中明确提到的关系，不要推测

返回严格的 JSON 格式，不要添加任何其他内容：
{{"concepts": [{{"name": "概念名", "category": "类别", "description": "一句话描述"}}], "relations": [{{"source": "概念A", "target": "概念B", "relation": "关系"}}]}}

文本：
{text}"""}],
        )

        import json
        try:
            content = response.content[0].text
            # Handle possible markdown code block wrapping
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(content)
            concepts = [Concept(**c) for c in data.get("concepts", [])]
            relations = [Relation(**r) for r in data.get("relations", [])]
            return ExtractionResult(concepts=concepts, relations=relations)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse concept extraction: {e}")
            return ExtractionResult(concepts=[], relations=[])

    # ------------------------------------------------------------------
    # Graph write operations
    # ------------------------------------------------------------------

    async def save_concepts(
        self, extraction: ExtractionResult, doc_id: str, chunk_ids: list[str]
    ):
        """Save extracted concepts and relations to Neo4j using batch UNWIND."""
        if not extraction.concepts and not extraction.relations:
            return

        async with self._driver.session() as session:
            # Batch merge concepts in one query
            if extraction.concepts:
                concept_data = [
                    {"name": c.name, "category": c.category, "description": c.description}
                    for c in extraction.concepts
                ]
                await session.run(
                    """
                    UNWIND $concepts AS c
                    MERGE (n:Concept {name: c.name})
                    ON CREATE SET n.category = c.category,
                                  n.description = c.description,
                                  n.created_at = datetime()
                    ON MATCH SET n.description = CASE
                        WHEN size(n.description) < size(c.description) THEN c.description
                        ELSE n.description
                    END
                    """,
                    concepts=concept_data,
                )

            # Batch merge relations in one query
            if extraction.relations:
                rel_data = [
                    {"source": r.source, "target": r.target, "relation": r.relation}
                    for r in extraction.relations
                ]
                await session.run(
                    """
                    UNWIND $rels AS r
                    MATCH (a:Concept {name: r.source})
                    MATCH (b:Concept {name: r.target})
                    MERGE (a)-[rel:RELATES_TO {type: r.relation}]->(b)
                    ON CREATE SET rel.weight = 1,
                                  rel.doc_ids = [$doc_id],
                                  rel.chunk_ids = $chunk_ids,
                                  rel.created_at = datetime()
                    ON MATCH SET rel.weight = rel.weight + 1,
                                 rel.doc_ids = CASE
                                     WHEN NOT $doc_id IN rel.doc_ids
                                     THEN rel.doc_ids + $doc_id
                                     ELSE rel.doc_ids
                                 END,
                                 rel.chunk_ids = rel.chunk_ids + $chunk_ids
                    """,
                    rels=rel_data,
                    doc_id=doc_id,
                    chunk_ids=chunk_ids,
                )

        logger.info(
            f"Saved {len(extraction.concepts)} concepts, "
            f"{len(extraction.relations)} relations for doc {doc_id}"
        )

    async def extract_and_save(
        self, chunks: list[str], doc_id: str, chunk_ids: list[str]
    ):
        """Extract concepts from all chunks and save to graph.

        Batches chunks into large groups (~30k chars) to minimize API calls.
        A 300-chunk book now triggers ~3 calls instead of ~50.
        """
        batch_text = ""
        batch_chunk_ids: list[str] = []
        # 30k chars ≈ ~8k tokens → well within Claude's context window
        batch_size = 30000

        for i, chunk in enumerate(chunks):
            batch_text += chunk + "\n\n"
            batch_chunk_ids.append(chunk_ids[i] if i < len(chunk_ids) else "")

            if len(batch_text) >= batch_size or i == len(chunks) - 1:
                extraction = await self.extract_concepts(batch_text)
                if extraction.concepts:
                    await self.save_concepts(extraction, doc_id, batch_chunk_ids)
                batch_text = ""
                batch_chunk_ids = []

        logger.info(f"Graph extraction completed for doc {doc_id}")

    # ------------------------------------------------------------------
    # Graph read operations
    # ------------------------------------------------------------------

    async def get_graph(self, limit: int = 200) -> dict:
        """Get the full knowledge graph (nodes + edges) for visualization."""
        async with self._driver.session() as session:
            # Get nodes
            nodes_result = await session.run(
                """
                MATCH (c:Concept)
                OPTIONAL MATCH (c)-[r]-()
                WITH c, count(r) AS connections
                RETURN c.name AS name, c.category AS category,
                       c.description AS description, connections
                ORDER BY connections DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            nodes = [dict(record) async for record in nodes_result]

            # Get edges between the returned nodes
            node_names = [n["name"] for n in nodes]
            edges_result = await session.run(
                """
                MATCH (a:Concept)-[r:RELATES_TO]->(b:Concept)
                WHERE a.name IN $names AND b.name IN $names
                RETURN a.name AS source, b.name AS target,
                       r.type AS relation, r.weight AS weight
                """,
                names=node_names,
            )
            edges = [dict(record) async for record in edges_result]

        return {"nodes": nodes, "edges": edges}

    async def get_neighbors(self, concept_name: str, depth: int = 2) -> dict:
        """Get a concept and its neighbors up to N hops."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH path = (start:Concept {name: $name})-[r:RELATES_TO*1.."""
                + str(min(depth, 5))
                + """]->(end:Concept)
                WITH nodes(path) AS ns, relationships(path) AS rs
                UNWIND ns AS n
                WITH collect(DISTINCT n) AS allNodes, collect(DISTINCT rs) AS allRels
                UNWIND allNodes AS node
                WITH allNodes, allRels, node
                OPTIONAL MATCH (node)-[r]-()
                WITH allNodes, allRels,
                     node.name AS name, node.category AS category,
                     node.description AS description, count(r) AS connections
                WITH allNodes, allRels,
                     collect({name: name, category: category,
                              description: description, connections: connections}) AS nodes
                UNWIND allRels AS relList
                UNWIND relList AS rel
                WITH nodes, collect(DISTINCT {
                    source: startNode(rel).name,
                    target: endNode(rel).name,
                    relation: rel.type,
                    weight: rel.weight
                }) AS edges
                RETURN nodes, edges
                """,
                name=concept_name,
            )
            record = await result.single()
            if record:
                return {"nodes": record["nodes"], "edges": record["edges"]}
            return {"nodes": [], "edges": []}

    async def search_concepts(self, query: str, limit: int = 20) -> list[dict]:
        """Search concepts by name (case-insensitive contains)."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Concept)
                WHERE toLower(c.name) CONTAINS toLower($query)
                OPTIONAL MATCH (c)-[r]-()
                WITH c, count(r) AS connections
                RETURN c.name AS name, c.category AS category,
                       c.description AS description, connections
                ORDER BY connections DESC
                LIMIT $limit
                """,
                query=query,
                limit=limit,
            )
            return [dict(record) async for record in result]

    async def get_stats(self) -> dict:
        """Get graph statistics."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Concept)
                WITH count(c) AS conceptCount
                OPTIONAL MATCH ()-[r:RELATES_TO]->()
                RETURN conceptCount, count(r) AS relationCount
                """
            )
            record = await result.single()
            return {
                "concepts": record["conceptCount"],
                "relations": record["relationCount"],
            }

    async def delete_document_concepts(self, doc_id: str):
        """Remove relations tied to a document. Clean up orphan concepts."""
        async with self._driver.session() as session:
            # Remove doc_id from relations and delete if no doc_ids left
            await session.run(
                """
                MATCH ()-[r:RELATES_TO]->()
                WHERE $doc_id IN r.doc_ids
                SET r.doc_ids = [x IN r.doc_ids WHERE x <> $doc_id],
                    r.weight = r.weight - 1
                WITH r WHERE size(r.doc_ids) = 0
                DELETE r
                """,
                doc_id=doc_id,
            )
            # Remove orphan concepts (no relations)
            await session.run(
                """
                MATCH (c:Concept)
                WHERE NOT (c)-[:RELATES_TO]-() AND NOT ()-[:RELATES_TO]-(c)
                DELETE c
                """
            )
        logger.info(f"Cleaned graph for doc {doc_id}")
