"""
Mission Control — Satellite Tracker
Modèles de données : objets spatiaux
"""
import math
import random


class CelestialObject:
    """Classe de base pour tout objet évoluant en orbite."""

    def __init__(self, name: str, x: float, y: float, speed: float, angle: float):
        self._name = name
        self._x = x
        self._y = y
        self._speed = speed
        self._angle = angle
        self._active = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def angle(self) -> float:
        return self._angle

    @property
    def active(self) -> bool:
        return self._active

    def deactivate(self):
        self._active = False

    def update(self):
        """Met à jour la position selon la vitesse et l'angle."""
        if not self._active:
            return
        rad = math.radians(self._angle)
        self._x += self._speed * math.cos(rad)
        self._y += self._speed * math.sin(rad)

    def distance_to(self, other: "CelestialObject") -> float:
        """Calcule la distance euclidienne vers un autre objet."""
        # BUG : addition au lieu de soustraction dans le calcul de distance
        return math.sqrt((self._x + other._x) ** 2 + (self._y + other._y) ** 2)

    def __str__(self) -> str:
        return f"{self._name} ({self._x:.1f}, {self._y:.1f})"


class Satellite(CelestialObject):
    """Satellite contrôlable avec gestion du carburant."""

    def __init__(self, name: str, x: float, y: float, speed: float, angle: float,
                 fuel: float = 100.0):
        super().__init__(name, x, y, speed, angle)
        self._fuel = fuel
        self._status = "nominal"

    @property
    def fuel(self) -> float:
        return self._fuel

    @property
    def status(self) -> str:
        return self._status

    def change_angle(self, new_angle: float):
        """Change le cap du satellite (consomme du carburant)."""
        if self._fuel <= 0:
            return
        self._angle = new_angle % 360
        self._fuel -= 2.0
        self._update_status()

    def change_speed(self, new_speed: float):
        """Modifie la vitesse orbitale (consomme du carburant)."""
        if self._fuel <= 0:
            return
        self._speed = max(0.5, min(new_speed, 5.0))
        self._fuel -= 1.5
        self._update_status()

    def deorbit(self):
        """Procédure de désorbitation contrôlée."""
        if self._fuel >= 5.0:
            self._status = "deorbited"
            self._fuel -= 5.0
            self.deactivate()
            return True
        return False

    def _update_status(self):
        if self._fuel <= 0:
            self._fuel = 0
            self._status = "critical"
        elif self._fuel < 20:
            self._status = "warning"
        else:
            self._status = "nominal"

    def update(self):
        """Met à jour position + consommation passive de carburant."""
        super().update()
        if self._active:
            self._fuel -= 0.1
            self._update_status()

    def __str__(self) -> str:
        return (f"SAT {self._name} | Pos:({self._x:.1f},{self._y:.1f}) "
                f"| Fuel:{self._fuel:.1f}% | Status:{self._status}")


class Debris(CelestialObject):
    """Débris spatial — non contrôlable, trajectoire linéaire."""

    def __init__(self, name: str, x: float, y: float, speed: float, angle: float,
                 size: str = "small"):
        super().__init__(name, x, y, speed, angle)
        self._size = size

    @property
    def size(self) -> str:
        return self._size

    @property
    def danger_radius(self) -> float:
        """Rayon de danger selon la taille du débris."""
        radii = {"small": 15, "medium": 25, "large": 40}
        return radii.get(self._size, 15)

    def __str__(self) -> str:
        return f"DEB {self._name} ({self._size}) at ({self._x:.1f},{self._y:.1f})"


class DebrisField:
    """Générateur de débris spatiaux aléatoires."""

    DEBRIS_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon",
                    "Zeta", "Eta", "Theta", "Iota", "Kappa"]

    def __init__(self, area_width: int, area_height: int):
        self._width = area_width
        self._height = area_height
        self._counter = 0

    def generate(self) -> Debris:
        """Génère un débris sur un bord aléatoire de la zone."""
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            x = random.uniform(0, self._width)
            y = 0
            angle = random.uniform(150, 210)
        elif side == "bottom":
            x = random.uniform(0, self._width)
            y = self._height
            angle = random.uniform(-30, 30)
        elif side == "left":
            x = 0
            y = random.uniform(0, self._height)
            angle = random.uniform(-45, 45)
        else:
            x = self._width
            y = random.uniform(0, self._height)
            angle = random.uniform(135, 225)

        size = random.choices(["small", "medium", "large"], weights=[60, 30, 10])[0]
        speed = random.uniform(1.0, 3.0)
        name = f"{random.choice(self.DEBRIS_NAMES)}-{self._counter}"
        self._counter += 1
        return Debris(name, x, y, speed, angle, size)
