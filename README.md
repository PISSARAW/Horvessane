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
