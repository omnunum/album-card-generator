"""Genre hierarchy utilities for building ASCII trees from genre relationships."""

import json
from pathlib import Path
from typing import Any


def load_genre_hierarchy() -> dict[str, Any]:
    """
    Load genre hierarchy from JSON file.

    Returns:
        Dictionary mapping genre names to their metadata (parents, depth, etc).
    """
    hierarchy_path = Path(__file__).parent.parent.parent / "genre_hierarchy.json"

    with open(hierarchy_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_genre_tree(genres: list[str]) -> str:
    """
    Build an ASCII tree representation of genre hierarchies.

    Args:
        genres: List of genre names to visualize.

    Returns:
        ASCII art string showing genre relationships.

    Example:
        >>> build_genre_tree(["Indie Rock", "Post-Rock"])
        Rock
        ├─ Alternative Rock
        │  └─ Indie Rock
        └─ Post-Rock
    """
    if not genres:
        return ""

    hierarchy = load_genre_hierarchy()

    # Build ALL paths for each genre (including all parent chains)
    all_paths: list[list[str]] = []

    for genre in genres:
        if genre not in hierarchy:
            # Genre not in hierarchy, add it as standalone
            all_paths.append([genre])
            continue

        # Get all parent paths for this genre
        genre_data = hierarchy[genre]
        paths = _get_all_parent_paths(genre, genre_data, hierarchy)
        all_paths.extend(paths)

    # Build tree structure
    tree = _build_tree_structure(all_paths)

    # Render as ASCII
    return _render_tree(tree)


def get_leaf_genres(genres: list[str]) -> list[str]:
    """
    Extract only the leaf genres (most specific genres with no children).

    Args:
        genres: List of genre names.

    Returns:
        List of leaf genre names (genres that have no children in the tree).

    Example:
        >>> get_leaf_genres(["Indie Rock", "Post-Rock"])
        ["Indie Rock", "Post-Rock"]
    """
    if not genres:
        return []

    hierarchy = load_genre_hierarchy()

    # Build ALL paths for each genre (including all parent chains)
    all_paths: list[list[str]] = []

    for genre in genres:
        if genre not in hierarchy:
            # Genre not in hierarchy, add it as standalone
            all_paths.append([genre])
            continue

        # Get all parent paths for this genre
        genre_data = hierarchy[genre]
        paths = _get_all_parent_paths(genre, genre_data, hierarchy)
        all_paths.extend(paths)

    # Build tree structure
    tree = _build_tree_structure(all_paths)

    # Extract leaf nodes (genres with no children)
    return _extract_leaves(tree)


def _get_all_parent_paths(genre: str, genre_data: dict[str, Any], hierarchy: dict[str, Any]) -> list[list[str]]:
    """
    Get all paths from root to this genre, following parent chains.

    The hierarchy includes ALL ancestors in the parents list, but we only want
    immediate parents (those with depth = current_depth - 1).

    Args:
        genre: Genre name.
        genre_data: Genre metadata from hierarchy.
        hierarchy: Full genre hierarchy.

    Returns:
        List of paths, where each path is a list from root to genre.
    """
    parents = genre_data.get("parents", [])
    current_depth = genre_data.get("depth", 0)

    if not parents or current_depth == 0:
        # Root genre - return single path with just this genre
        return [[genre]]

    all_paths: list[list[str]] = []

    # Filter to only immediate parents (depth = current_depth - 1)
    immediate_parents = [
        p for p in parents
        if p in hierarchy and hierarchy[p].get("depth", 0) == current_depth - 1
    ]

    # If no immediate parents found, use all parents (fallback)
    if not immediate_parents:
        immediate_parents = parents

    # For each immediate parent, get all paths to that parent, then append this genre
    for parent in immediate_parents:
        if parent in hierarchy:
            parent_paths = _get_all_parent_paths(parent, hierarchy[parent], hierarchy)
            for parent_path in parent_paths:
                # Append this genre to the parent path
                all_paths.append(parent_path + [genre])
        else:
            # Parent not in hierarchy, create path with just parent and genre
            all_paths.append([parent, genre])

    return all_paths


def _build_tree_structure(paths: list[list[str]]) -> dict[str, Any]:
    """
    Convert list of paths into a nested tree structure.

    Args:
        paths: List of paths, where each path is a list of genre names from root to leaf.

    Returns:
        Nested dictionary representing the tree.
    """
    tree: dict[str, Any] = {}

    for path in paths:
        current = tree
        for genre in path:
            if genre not in current:
                current[genre] = {}
            current = current[genre]

    return tree


def _extract_leaves(tree: dict[str, Any]) -> list[str]:
    """
    Extract all leaf nodes from the tree.

    Args:
        tree: Nested dictionary representing the tree.

    Returns:
        List of leaf genre names (genres with no children).
    """
    leaves: list[str] = []

    for genre, children in tree.items():
        if not children:
            # No children - this is a leaf
            leaves.append(genre)
        else:
            # Has children - recurse
            leaves.extend(_extract_leaves(children))

    return leaves


def _render_tree(tree: dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """
    Render tree structure as ASCII art.

    Args:
        tree: Nested dictionary representing the tree.
        prefix: Current line prefix for indentation.
        is_last: Whether this is the last child in its parent.

    Returns:
        ASCII art string.
    """
    lines: list[str] = []
    items = list(tree.items())

    for idx, (genre, children) in enumerate(items):
        is_last_item = (idx == len(items) - 1)

        # Add the genre to lines
        if prefix == "":
            # Root level - no connector
            lines.append(genre)
        else:
            # Child level - use tree connectors
            connector = "└─ " if is_last_item else "├─ "
            lines.append(f"{prefix}{connector}{genre}")

        # Recursively render children
        if children:
            new_prefix = prefix + ("   " if is_last_item else "│  ")
            child_output = _render_tree(children, new_prefix, is_last_item)
            if child_output:
                lines.append(child_output)

    return "\n".join(lines)
