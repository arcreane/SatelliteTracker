"""
Mission Control — Satellite Tracker
Moteur de simulation
"""
import random
from models import CelestialObject, Satellite, Debris, DebrisField


class CollisionDetector:
    """Détecte les collisions entre objets spatiaux."""

    SATELLITE_RADIUS = 20

    @staticmethod
    def check_collision(obj1: CelestialObject, obj2: CelestialObject) -> bool:
        """Vérifie si deux objets sont en collision."""
        distance = obj1.distance_to(obj2)

        if isinstance(obj1, Satellite) and isinstance(obj2, Debris):
            return distance < (CollisionDetector.SATELLITE_RADIUS + obj2.danger_radius)
        elif isinstance(obj1, Debris) and isinstance(obj2, Satellite):
            return distance < (CollisionDetector.SATELLITE_RADIUS + obj1.danger_radius)
        elif isinstance(obj1, Satellite) and isinstance(obj2, Satellite):
            return distance < (CollisionDetector.SATELLITE_RADIUS * 2)
        return False

    @staticmethod
    def check_proximity_warning(sat: Satellite, obj: CelestialObject,
                                 warning_distance: float = 80.0) -> bool:
        """Vérifie si un objet est dangereusement proche d'un satellite."""
        return sat.distance_to(obj) < warning_distance


class Simulation:
    """Gère la boucle de simulation : satellites, débris, collisions, score."""

    AREA_WIDTH = 800
    AREA_HEIGHT = 600

    def __init__(self):
        self._satellites: list[Satellite] = []
        self._debris_list: list[Debris] = []
        self._debris_field = DebrisField(self.AREA_WIDTH, self.AREA_HEIGHT)
        self._collision_detector = CollisionDetector()
        self._tick_count = 0
        self._score = 0
        self._collisions = 0
        self._deorbited = 0
        self._game_over = False
        self._events: list[str] = []

    @property
    def satellites(self) -> list[Satellite]:
        return self._satellites

    @property
    def debris_list(self) -> list[Debris]:
        return self._debris_list

    @property
    def score(self) -> int:
        return self._score

    @property
    def collisions(self) -> int:
        return self._collisions

    @property
    def deorbited(self) -> int:
        return self._deorbited

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def game_over(self) -> bool:
        return self._game_over

    def pop_events(self) -> list[str]:
        """Récupère et vide la liste des événements récents."""
        events = self._events.copy()
        self._events.clear()
        return events

    def add_satellite(self, sat: Satellite):
        self._satellites.append(sat)

    def tick(self):
        """Avance la simulation d'un pas de temps."""
        if self._game_over:
            return

        self._tick_count += 1

        # Mise à jour des positions
        for sat in self._satellites:
            sat.update()
        for deb in self._debris_list:
            deb.update()

        # Génération de débris (difficulté croissante)
        spawn_chance = min(0.05 + self._tick_count * 0.0005, 0.3)
        if random.random() < spawn_chance:
            self._debris_list.append(self._debris_field.generate())

        # Détection de collisions
        self._check_all_collisions()

        # Nettoyage des objets hors zone
        self._cleanup_out_of_bounds()

        # Score : +1 par satellite actif par tick
        active_sats = [s for s in self._satellites if s.active]
        self._score += len(active_sats)

        # Game over si plus de satellites actifs
        if len(active_sats) == 0 and self._tick_count > 10:
            self._game_over = True

    def _check_all_collisions(self):
        """Vérifie toutes les paires satellite-débris et satellite-satellite."""
        active_sats = [s for s in self._satellites if s.active]
        active_debris = [d for d in self._debris_list if d.active]

        for sat in active_sats:
            for deb in active_debris:
                if self._collision_detector.check_collision(sat, deb):
                    sat.deactivate()
                    deb.deactivate()
                    self._collisions += 1
                    self._events.append(f"COLLISION : {sat.name} touché par {deb.name} !")

                elif self._collision_detector.check_proximity_warning(sat, deb):
                    self._events.append(f"ALERTE : {deb.name} proche de {sat.name}")

        for i in range(len(active_sats)):
            for j in range(i + 1, len(active_sats)):
                if self._collision_detector.check_collision(active_sats[i], active_sats[j]):
                    active_sats[i].deactivate()
                    active_sats[j].deactivate()
                    self._collisions += 2
                    self._events.append(
                        f"COLLISION : {active_sats[i].name} et {active_sats[j].name} !"
                    )

    def _cleanup_out_of_bounds(self):
        """Supprime les débris sortis de la zone."""
        margin = 50
        self._debris_list = [
            d for d in self._debris_list
            if d.active and -margin < d.x < self.AREA_WIDTH + margin
            and -margin < d.y < self.AREA_HEIGHT + margin
        ]

    def deorbit_satellite(self, satellite_name: str) -> bool:
        """Tente de désorbiter un satellite par son nom."""
        for sat in self._satellites:
            if sat.name == satellite_name and sat.active:
                if sat.deorbit():
                    # BUG : incrémente _collisions au lieu de _deorbited
                    self._collisions += 1
                    self._events.append(f"{sat.name} désorbité avec succès !")
                    return True
                else:
                    self._events.append(f"{sat.name} : carburant insuffisant pour désorbiter")
                    return False
        return False

    def get_stats(self) -> dict:
        """Retourne les statistiques de la simulation."""
        active = [s for s in self._satellites if s.active]
        return {
            "tick": self._tick_count,
            "score": self._score,
            "satellites_actifs": len(active),
            "collisions": self._collisions,
            "desorbites": self._deorbited,
            "debris_en_zone": len(self._debris_list),
        }
