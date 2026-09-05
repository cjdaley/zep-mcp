import json
from typing import Literal, TypedDict, NotRequired


class MessageDict(TypedDict):
    role: str
    content: str
    name: NotRequired[str]


def register(mcp, zep):
    """Register memory tools."""

    @mcp.tool(tags={"memory"}, annotations={"readOnlyHint": True})
    def search_graph(
        query: str,
        user_id: str | None = None,
        graph_id: str | None = None,
        scope: Literal["edges", "nodes", "episodes"] = "edges",
        limit: int = 10,
        reranker: Literal["rrf", "mmr", "node_distance", "episode_mentions", "cross_encoder"] | None = None,
        mmr_lambda: float | None = None,
    ):
        """Search a knowledge graph for relevant facts, entities, or episodes.
        Keep queries concise and specific for best results."""
        from utils import _require_one_of
        _require_one_of(user_id=user_id, graph_id=graph_id)
        kwargs = dict(
            user_id=user_id,
            graph_id=graph_id,
            query=query,
            scope=scope,
            limit=limit,
        )
        if reranker is not None:
            kwargs["reranker"] = reranker
        if mmr_lambda is not None:
            kwargs["mmr_lambda"] = mmr_lambda
        return zep.graph.search(**kwargs)

    @mcp.tool(tags={"memory"}, annotations={"readOnlyHint": True})
    def get_task(task_id: str):
        """Poll the status of an async Zep operation (batch import, cloning, etc.)."""
        return zep.task.get(task_id=task_id)

    @mcp.tool(tags={"memory"})
    def add_messages(
        thread_id: str,
        messages: list[MessageDict],
    ):
        """Add messages to a thread. Each message needs 'role' (user/assistant/system),
        'content', and optionally 'name'."""
        from zep_cloud import Message
        msg_objects = [Message(**m) for m in messages]
        return zep.thread.add_messages(thread_id=thread_id, messages=msg_objects)

    @mcp.tool(tags={"memory"}, annotations={"readOnlyHint": True})
    def get_context(
        thread_id: str,
        template_id: str | None = None,
    ):
        """Get the assembled context block for a user based on thread history.
        Optionally pass a template_id for custom formatting."""
        kwargs = dict(thread_id=thread_id)
        if template_id is not None:
            kwargs["template_id"] = template_id
        return zep.thread.get_user_context(**kwargs)

    @mcp.tool(tags={"memory"})
    def add_graph_data(
        type: Literal["text", "json", "message", "triple"],
        data: str | None = None,
        user_id: str | None = None,
        graph_id: str | None = None,
        fact: str | None = None,
        fact_name: str | None = None,
        source_node_name: str | None = None,
        target_node_name: str | None = None,
        valid_at: str | None = None,
        invalid_at: str | None = None,
        source_node_attributes: str | None = None,
        edge_attributes: str | None = None,
        target_node_attributes: str | None = None,
    ):
        """Add data to a knowledge graph. Types: text, json, message, or triple.
        For triple: provide fact, fact_name, source_node_name, and target_node_name.
        source_node_attributes, edge_attributes, and target_node_attributes accept
        JSON strings (e.g. '{"key": "value"}')."""
        from utils import _require_one_of
        _require_one_of(user_id=user_id, graph_id=graph_id)
        if type == "triple":
            kwargs = dict(
                fact=fact, fact_name=fact_name,
                user_id=user_id, graph_id=graph_id,
            )
            if source_node_name is not None:
                kwargs["source_node_name"] = source_node_name
            if target_node_name is not None:
                kwargs["target_node_name"] = target_node_name
            if valid_at is not None:
                kwargs["valid_at"] = valid_at
            if invalid_at is not None:
                kwargs["invalid_at"] = invalid_at
            if source_node_attributes is not None:
                kwargs["source_node_attributes"] = json.loads(source_node_attributes)
            if edge_attributes is not None:
                kwargs["edge_attributes"] = json.loads(edge_attributes)
            if target_node_attributes is not None:
                kwargs["target_node_attributes"] = json.loads(target_node_attributes)
            return zep.graph.add_fact_triple(**kwargs)
        return zep.graph.add(
            user_id=user_id, graph_id=graph_id, type=type, data=data,
        )

    @mcp.tool(tags={"memory"})
    def create_graph(
        graph_id: str,
        name: str | None = None,
        description: str | None = None,
        time_zone: str | None = None,
    ):
        """Create a standalone knowledge graph.

        The graph must exist before add_graph_data or search_graph can use it —
        writing to a missing graph_id returns 404. graph_id is required.
        Optional name and description are routing metadata shown by list_graphs.
        """
        kwargs = dict(graph_id=graph_id)
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if time_zone is not None:
            kwargs["time_zone"] = time_zone
        return zep.graph.create(**kwargs)

    @mcp.tool(tags={"memory"}, annotations={"readOnlyHint": True})
    def list_graphs(
        search: str | None = None,
        page_number: int = 1,
        page_size: int = 20,
        order_by: Literal["created_at", "graph_id", "name"] | None = None,
        asc: bool | None = None,
    ):
        """List standalone graphs in this project (directory metadata only).

        Does not search graph contents. Optional search filters graph_id, name,
        and description. Use a returned graph_id with add_graph_data or search_graph.
        """
        kwargs = dict(page_number=page_number, page_size=page_size)
        if search is not None:
            kwargs["search"] = search
        if order_by is not None:
            kwargs["order_by"] = order_by
        if asc is not None:
            kwargs["asc"] = asc
        return zep.graph.list_all(**kwargs)
