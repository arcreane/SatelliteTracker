# Mission Control — Satellite Tracker


Simulateur de suivi de satellites en orbite.
Gérez vos satellites, évitez les débris spatiaux et désorbiter en sécurité.

## Lancement
pip install PySide6 python main_window.py

## Structure
- `models.py` : Classes de données (CelestialObject, Satellite, Debris)
- `simulation.py` : Moteur de simulation (collisions, score, events)
- `main_window.py` : Interface graphique PySide6