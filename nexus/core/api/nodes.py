"""
Nodes API routes for Nexus Core.

Handles node management, status, and queries.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from nexus.shared import Node, NodeList, NodeStatus, NodeUpdate, NodeWithMetrics

router = APIRouter()


@router.get("", response_model=NodeList)
async def list_nodes(
    status_filter: Optional[NodeStatus] = Query(None, alias="status"),
    tag: Optional[str] = Query(None),
):
    """
    List all registered nodes.

    Query Parameters:
        status: Filter by node status (online, offline, error)
        tag: Filter by metadata tag

    Returns:
        List of nodes matching filters

    TODO: Implement database query
    TODO: Implement filtering logic
    """
    # TODO: Query database for nodes
    # TODO: Apply filters
    # TODO: Return actual nodes from database

    # Placeholder response
    return NodeList(nodes=[], total=0)


@router.get("/{node_id}", response_model=NodeWithMetrics)
async def get_node(node_id: UUID):
    """
    Get detailed status of a specific node.

    Args:
        node_id: UUID of the node

    Returns:
        Node details with current metrics and active job count

    Raises:
        404: Node not found

    TODO: Implement database query
    TODO: Fetch latest metrics
    TODO: Count active jobs
    """
    # TODO: Query database for node by ID
    # TODO: Get latest metrics for node
    # TODO: Count active jobs for node

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Node {node_id} not found",
    )


@router.put("/{node_id}", response_model=Node)
async def update_node(node_id: UUID, update: NodeUpdate):
    """
    Update node metadata.

    Args:
        node_id: UUID of the node
        update: Fields to update

    Returns:
        Updated node

    Raises:
        404: Node not found

    TODO: Implement database update
    """
    # TODO: Query database for node
    # TODO: Update fields
    # TODO: Save to database
    # TODO: Return updated node

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Node {node_id} not found",
    )


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_node(node_id: UUID):
    """
    Deregister a node.

    Args:
        node_id: UUID of the node

    Raises:
        404: Node not found

    TODO: Implement database deletion
    TODO: Clean up associated jobs and metrics
    """
    # TODO: Query database for node
    # TODO: Delete node
    # TODO: Clean up associated data

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Node {node_id} not found",
    )
