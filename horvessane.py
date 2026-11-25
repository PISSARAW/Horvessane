"""Ordre partiel à partir de fenêtres d'horloge et de précédences attestées."""
import argparse
import json
from collections import deque
from graphlib import TopologicalSorter
from itertools import combinations
from pathlib import Path


def path_between(graph, source, target):
    parents = {source: None}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        if node == target:
            path = []
            while parents[node] is not None:
                previous = parents[node]
                path.append([previous, node, graph[previous][node]])
                node = previous
            return path[::-1]
        for neighbor in graph[node]:
            if neighbor not in parents:
                parents[neighbor] = node
                queue.append(neighbor)
    return None


def analyze(case):
    """Les bornes inclusives sont des secondes sur une même échelle."""
    windows = {}
    for event in case["events"]:
        key = event["id"]
        clock, error = event["time_s"], event["uncertainty_s"]
        if not isinstance(key, str) or not key or key in windows:
            raise ValueError("identifiant absent ou dupliqué")
        if type(clock) is not int or type(error) is not int or error < 0:
            raise ValueError("temps entier et incertitude positive ou nulle requis")
        windows[key] = (clock - error, clock + error)

    graph = {key: {} for key in windows}
    pairs = list(combinations(windows, 2))
    for a, b in pairs:
        if windows[a][1] < windows[b][0]:
            graph[a][b] = "bornes disjointes"
        elif windows[b][1] < windows[a][0]:
            graph[b][a] = "bornes disjointes"
    for edge in case.get("anchors", []):
        a, b, evidence = edge["before"], edge["after"], edge["evidence"]
        if a not in graph or b not in graph or a == b or not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("ancre invalide")
        graph[a][b] = evidence

    for a, neighbors in graph.items():
        for b, evidence in neighbors.items():
            back = path_between(graph, b, a)
            if back is not None:
                return {"status": "contradiction", "cycle": [[a, b, evidence], *back]}

    # Une ancre impose un ordre strict, même lorsque deux bornes se touchent.
    ordering = TopologicalSorter()
    for a, neighbors in graph.items():
        ordering.add(a)
        for b in neighbors:
            ordering.add(b, a)
    earliest = {key: (bounds[0], False) for key, bounds in windows.items()}
    witness = {key: [] for key in windows}
    for a in ordering.static_order():
        for b, evidence in graph[a].items():
            bound = (earliest[a][0], True)
            if bound > earliest[b]:
                earliest[b] = bound
                witness[b] = [*witness[a], [a, b, evidence]]
            if earliest[b] > (windows[b][1], False):
                return {"status": "contradiction", "bounds": windows, "path": witness[b]}

    relations = []
    for a, b in pairs:
        path = path_between(graph, a, b) or path_between(graph, b, a)
        if path:
            relations.append({"before": path[0][0], "after": path[-1][1], "evidence": path})
        else:
            relations.append({"undetermined": [a, b]})
    return {"status": "consistent", "windows": windows, "relations": relations}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    try:
        report = analyze(json.loads(args.case.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Dossier invalide ({exc})\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(int(report["status"] == "contradiction"))
