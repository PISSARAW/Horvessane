# Horvessane
Un analyste voit une ouverture de session à 10:03:12 sur Windows et une requête à 10:03:09 sur un serveur. Une timeline classique affiche la requête en premier. Si les horloges divergent de cinq secondes, cette présentation peut conduire l’enquête dans la mauvaise direction.

Le moteur Python lit un dossier JSON et calcule les relations démontrables entre événements. Chaque précédence porte une chaîne de justifications. Une contradiction fournit un cycle ou une chaîne incompatible avec les bornes.

## Démarrage

Depuis la racine du dépôt avec Python 3.10 ou ultérieur et Make :

```sh
make demo
make test
```

Commande directe :

```sh
python3 -m horvessane examples/incident.json
```

`auth` précède `receipt` grâce à `trace-42`. L’ordre entre `auth` et `request` reste indéterminé malgré leurs heures différentes.

Codes de sortie : 0 pour un graphe cohérent, 1 pour un cycle, 2 pour une entrée invalide.

## Organisation

- `horvessane.py` contient le moteur et son interface en ligne de commande.
- `examples/` contient les entrées fictives et reproductibles.
- `tests/` couvre le comportement nominal et les cas limites.

## Périmètre du socle

Les temps entiers sont des secondes sur une origine commune. Chaque fenêtre est inclusive. Une ancre décrit une précédence stricte attestée. Le moteur traite de petits dossiers en mémoire. Son modèle utilise les précédences imposées par les fenêtres disjointes et les ancres. Il ne calibre pas les horloges et ne lit pas encore les EVTX.

## Premier chantier à reprendre

Ajouter un adaptateur Sysmon JSON et un journal applicatif. Préparer un scénario avec une horloge décalée et un observateur indépendant. Le test doit comparer les précédences affirmées à l’ordre observé et compter séparément les abstentions.

## Exercice commun aux cinq projets

Depuis ce dépôt, avec Git, Make, Python 3.10+ et Go 1.22+ :

```sh
make demo-suite
make test-suite
```

La démo télécharge les révisions exactes des quatre dépôts indiquées dans `integration/peers.lock.json`, compile Revaskel et exécute les cinq CLI. Le scénario utilise deux expéditions, un document manquant et un accès hérité hors mandat. La file de revue finale contient deux des trois observations. Les fichiers intermédiaires sont temporaires par défaut.

| Étape | Fichier JSON | Contenu |
|---|---|---|
| Revaskel | `01-restauration.json` | Contrôles de présence et d’intégrité des documents, avec références locales. |
| Mandoryve | `02-droits.json` | Comparaison des droits ou état de vérification indisponible. |
| Horvessane | `03-chronologie.json` | Observations des deux producteurs et précédences compatibles avec les horloges. |
| Calquory | `04-dossier.json` | Dossier réduit aux comparaisons et aux relations temporelles. |
| Calquory | `05-constats.json` | Résultats du rejeu des comparaisons et identifiants à examiner. |
| Sorvelune | `06-revue.json` | Échantillon à budget fixé, contexte temporel et probabilités d’inclusion. |

Pour conserver les six fichiers dans un nouveau sous-dossier :

```sh
python3 integration/run.py --save-under ./exercices
```

Les fichiers 01 à 03 sont privés. Le profil d’export du fichier 04 retire sujets, dossiers, heures absolues et empreintes. Les références numérotées restent corrélables à la chronologie privée du même exercice. Le rejeu porte sur les constats enregistrés. Le dossier réduit ne restaure aucun objet et ne modifie aucun droit.

Pour travailler hors ligne sur les cinq dépôts clonés côte à côte, y compris tes modifications locales :

```sh
python3 integration/run.py --repos .. --budget 2 --seed 42
SUITE_REPOS=.. make test-suite
```

Avec tes propres données, fournis `--snapshot CHEMIN`, `--mandate FICHIER`, `--case-id ID`, `--restore-time SECONDES` et `--uncertainty SECONDES`. Les heures des deux observations doivent partager la même origine. Le budget est compris entre 1 et le nombre de constats. La démo utilise une priorité fixe et un tirage aléatoire reproductible. L’ordre temporel documente le contexte du contrôle et ne suffit pas à établir la cause de l’écart.
