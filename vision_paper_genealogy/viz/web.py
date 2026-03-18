"""Web visualization using pyvis."""

from __future__ import annotations

from pathlib import Path

from pyvis.network import Network

from vision_paper_genealogy.graph.builder import GenealogyGraph
from vision_paper_genealogy.models import RelationType

RELATION_COLORS = {
    RelationType.extends: "#22c55e",   # green
    RelationType.combines: "#06b6d4",  # cyan
    RelationType.replaces: "#ef4444",  # red
    RelationType.inspires: "#eab308",  # yellow
}

RELATION_DASHES = {
    RelationType.extends: False,
    RelationType.combines: False,
    RelationType.replaces: False,
    RelationType.inspires: True,  # dashed line for indirect influence
}


def build_pyvis_network(graph: GenealogyGraph, height: str = "700px") -> Network:
    """Build a pyvis Network from a GenealogyGraph."""
    net = Network(
        height=height,
        width="100%",
        directed=True,
        bgcolor="#0e1117",
        font_color="white",
        notebook=False,
    )
    net.barnes_hut(
        gravity=-3000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.05,
    )

    for name, node in graph.nodes.items():
        m = node.method
        size = 15
        if m.stars:
            if m.stars > 10000:
                size = 40
            elif m.stars > 5000:
                size = 30
            elif m.stars > 1000:
                size = 22

        stars_str = f"\n★ {m.stars:,}" if m.stars else ""
        code_str = f"\n📦 github.com/{m.code}" if m.code else ""
        arxiv_str = f"\n📄 arxiv.org/abs/{m.arxiv}" if m.arxiv else ""
        tags_str = f"\nTags: {', '.join(m.tags)}" if m.tags else ""
        desc_str = f"\n{m.description}" if m.description else ""

        title = f"{m.name} [{m.year}]{stars_str}{desc_str}{code_str}{arxiv_str}{tags_str}"

        color = "#3b82f6"  # default blue
        if not node.parent_nodes:
            color = "#f97316"  # orange for roots

        net.add_node(
            name,
            label=f"{m.name}\n[{m.year}]",
            title=title,
            size=size,
            color=color,
            font={"size": 12, "color": "white"},
        )

    for name, node in graph.nodes.items():
        for parent_ref in node.method.parents:
            if parent_ref.name in graph.nodes:
                edge_color = RELATION_COLORS[parent_ref.relation]
                dashes = RELATION_DASHES[parent_ref.relation]
                net.add_edge(
                    parent_ref.name,
                    name,
                    color=edge_color,
                    title=parent_ref.relation.value,
                    dashes=dashes,
                    arrows="to",
                    width=2,
                )

    return net


def export_html(graph: GenealogyGraph, output_path: str | Path, height: str = "700px") -> Path:
    """Export the genealogy graph as an interactive HTML file."""
    output_path = Path(output_path)
    net = build_pyvis_network(graph, height=height)
    net.save_graph(str(output_path))
    return output_path
