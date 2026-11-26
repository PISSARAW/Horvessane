"""Exécuter les cinq CLI sur un même exercice de reprise."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from typing import NamedTuple
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME_REPO = HERE.parent


def prepare_peers(work, siblings=None):
    pins = json.loads((HERE / "peers.lock.json").read_text())
    peers = {"Horvessane": HOME_REPO}
    for name, revision in pins.items():
        if siblings:
            repo = siblings.resolve() / name
            if not (repo / "README.md").is_file():
                raise ValueError(f"Dépôt local absent : {repo}")
        else:
            repo = work / name
            subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
            url = f"https://github.com/PISSARAW/{name}.git"
            subprocess.run(["git", "fetch", "--quiet", "--depth=1", url, revision], cwd=repo, check=True)
            subprocess.run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=repo, check=True)
        peers[name] = repo
    return peers


def build_revaskel(peers, work):
    binary = work / ("revaskel-cli.exe" if os.name == "nt" else "revaskel-cli")
    subprocess.run(["go", "build", "-o", str(binary), "."], cwd=peers["Revaskel"], check=True)
    return binary


class Inputs(NamedTuple):
    snapshot: Path
    mandate: Path


class Clock(NamedTuple):
    case_id: str
    restore_time: int
    uncertainty: int


class Review(NamedTuple):
    budget: int
    seed: int


class Scenario(NamedTuple):
    inputs: Inputs
    clock: Clock
    review: Review


class Tools(NamedTuple):
    peers: dict
    binary: Path


def exercise(tools, out, scenario):
    peers, binary = tools
    snapshot, mandate = scenario.inputs
    case_id, restore_time, uncertainty = scenario.clock
    budget, seed = scenario.review
    # Répertoire neuf par exercice. Les fichiers 01, 02 et 03 gardent des données privées.
    out.mkdir(mode=0o700)
    def stage(repo, filename, command):
        data = subprocess.run(command, cwd=peers[repo], stdout=subprocess.PIPE, check=True).stdout
        json.loads(data)
        target = out / filename
        target.write_bytes(data)
        return target

    py = sys.executable
    recovery = stage("Revaskel", "01-restauration.json", [
        str(binary), "evidence", "--case-id", case_id, "--observed-at", str(restore_time),
        "--uncertainty-s", str(uncertainty), str(snapshot.resolve())])
    access = stage("Mandoryve", "02-droits.json", [
        py, "-m", "mandoryve", str(mandate.resolve()), "--evidence", case_id,
        "--uncertainty-s", str(uncertainty)])
    timeline = stage("Horvessane", "03-chronologie.json", [
        py, "-m", "horvessane", "--join", str(recovery), str(access)])
    bundle = stage("Calquory", "04-dossier.json", [
        py, "-m", "calquory", "pack-timeline", str(timeline)])
    replay = stage("Calquory", "05-constats.json", [
        py, "-m", "calquory", "replay", str(bundle)])
    queue = stage("Sorvelune", "06-revue.json", [
        py, "-m", "sorvelune", "--review", "--budget", str(budget), "--seed", str(seed), str(replay)])
    return json.loads(queue.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos", type=Path, help="répertoire contenant les quatre dépôts pairs déjà clonés")
    parser.add_argument("--snapshot", type=Path, help="répertoire d’instantané au format Revaskel")
    parser.add_argument("--mandate", type=Path, help="dossier JSON au format Mandoryve")
    parser.add_argument("--case-id", default="reprise-demo")
    parser.add_argument("--restore-time", type=int, default=6, help="heure de l’observation sur l’horloge de l’exercice")
    parser.add_argument("--uncertainty", type=int, default=1)
    parser.add_argument("--budget", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-under", type=Path, help="créer un sous-dossier privé avec les six fichiers JSON")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp).resolve()
        peers = prepare_peers(work, args.repos)
        binary = build_revaskel(peers, work)
        parent = work
        if args.save_under:
            parent = args.save_under.resolve()
            parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent, prefix=".exercise-") as staging:
            out = Path(staging) / "result"
            inputs = Inputs(args.snapshot or peers["Revaskel"] / "examples/partial",
                           args.mandate or peers["Mandoryve"] / "examples/group.json")
            scenario = Scenario(inputs, Clock(args.case_id, args.restore_time, args.uncertainty),
                                Review(args.budget, args.seed))
            result = exercise(Tools(peers, binary), out, scenario)
            if args.save_under:
                # Le nom unique empêche deux exécutions concurrentes de partager leurs traces.
                dest = parent / Path(staging).name.removeprefix(".")
                out.rename(dest)
                print(f"Exercice enregistré dans {dest}", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"Échec de l’exercice : {exc}")
