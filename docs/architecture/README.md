# Architecture de Horvessane

Le moteur Python transforme des fenêtres temporelles et des ancres en contraintes de précédence. L’orchestrateur utilise des entrées, une horloge d’exercice et un budget de revue pour piloter les cinq CLI. Les révisions des quatre pairs sont enregistrées dans `integration/peers.lock.json`.

[Décisions d’architecture](../adr/README.md)
