"""Ordre partiel à partir de fenêtres d'horloge et de précédences attestées."""
import argparse
import json
import re
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


def event_windows(case):
    windows = {}
    for event in case["events"]:
        key = event["id"]
        clock, error = event["time_s"], event["uncertainty_s"]
        if not isinstance(key, str) or not key or key in windows:
            raise ValueError("identifiant absent ou dupliqué")
        if type(clock) is not int or type(error) is not int or error < 0:
            raise ValueError("temps entier et incertitude positive ou nulle requis")
        windows[key] = (clock - error, clock + error)
    return windows


def temporal_graph(windows, pairs):
    graph = {key: {} for key in windows}
    for a, b in pairs:
        if windows[a][1] < windows[b][0]:
            graph[a][b] = "bornes disjointes"
        elif windows[b][1] < windows[a][0]:
            graph[b][a] = "bornes disjointes"
    return graph


def add_anchors(graph, case):
    for edge in case.get("anchors", []):
        a, b, evidence = edge["before"], edge["after"], edge["evidence"]
        if a not in graph or b not in graph or a == b or not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("ancre invalide")
        graph[a][b] = evidence


def find_cycle(graph):
    for a, neighbors in graph.items():
        for b, evidence in neighbors.items():
            back = path_between(graph, b, a)
            if back is not None:
                return {"status": "contradiction", "cycle": [[a, b, evidence], *back]}
    return None


def check_bounds(graph, windows):
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
    return None


def analyze(case):
    windows = event_windows(case)
    pairs = list(combinations(windows, 2))
    graph = temporal_graph(windows, pairs)
    add_anchors(graph, case)
    conflict = find_cycle(graph) or check_bounds(graph, windows)
    if conflict:
        return conflict
    relations = []
    for a, b in pairs:
        path = path_between(graph, a, b) or path_between(graph, b, a)
        if path:
            relations.append({"before": path[0][0], "after": path[-1][1], "evidence": path})
        else:
            relations.append({"undetermined": [a, b]})
    return {"status": "consistent", "windows": windows, "relations": relations}


def packet_events(packet, kinds):
    source = packet["source"]
    for event in packet["events"]:
        if (not re.fullmatch(source + r"-[1-9][0-9]*", event["id"])
                or event["kind"] not in kinds or not isinstance(event["facts"], dict)):
            raise ValueError("observation incompatible")
        yield {**event, "source": source}


def same_case(current, previous):
    if not isinstance(current, str) or not current.strip():
        raise ValueError("identifiant d’exercice vide")
    if previous is not None and current != previous:
        raise ValueError("observations de deux exercices différents")
    return current


def join_evidence(packets):
    """Relier une observation de chaque producteur dans un unique exercice."""
    sources = {"mandoryve": {"access", "verified", "unavailable"}, "revaskel": {"document"}}
    received = set()
    case_id = None
    events = []
    for packet in packets:
        source = packet["source"]
        if packet["schema"] != "evidence.v1" or source not in sources or source in received:
            raise ValueError("version ou producteur inattendu")
        received.add(source)
        case_id = same_case(packet["case_id"], case_id)
        if not isinstance(packet["events"], list) or not packet["events"]:
            raise ValueError("lot vide")
        events.extend(packet_events(packet, sources[source]))
    if received != sources.keys():
        raise ValueError("lot Revaskel ou Mandoryve manquant")
    timeline = analyze({"events": events})
    return {"schema": "timeline.v1", "case_id": case_id, "events": events, "timeline": timeline}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, nargs="?")
    parser.add_argument("--join", type=Path, nargs=2, metavar=("LOT_A", "LOT_B"))
    args = parser.parse_args()
    if bool(args.case) == bool(args.join):
        parser.error("fournir un dossier ou deux lots avec --join")
    try:
        if args.join:
            report = join_evidence([json.loads(p.read_text()) for p in args.join])
        else:
            report = analyze(json.loads(args.case.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Dossier invalide ({exc})\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(int(report.get("timeline", report)["status"] == "contradiction"))


if __name__ == "__main__":
    main()
