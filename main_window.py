"""
Mission Control — Satellite Tracker
Interface graphique PySide6
"""
import sys
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSlider, QGroupBox, QTextEdit,
    QGraphicsScene, QGraphicsView
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QFont, QPainter

from models import Satellite
from simulation import Simulation


class RadarView(QGraphicsView):
    """Vue radar affichant les satellites et débris."""

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #0a0a2e; border: 2px solid #1a4a1a;")

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Dessine le fond radar avec grille."""
        painter.fillRect(rect, QColor("#0a0a2e"))
        pen = QPen(QColor(30, 60, 30, 80))
        pen.setWidth(1)
        painter.setPen(pen)
        for x in range(0, 801, 50):
            painter.drawLine(x, 0, x, 600)
        for y in range(0, 601, 50):
            painter.drawLine(0, y, 800, y)

        center_x, center_y = 400, 300
        pen_circle = QPen(QColor(30, 80, 30, 60))
        pen_circle.setWidth(1)
        painter.setPen(pen_circle)
        for r in range(50, 400, 75):
            painter.drawEllipse(QPointF(center_x, center_y), r, r)


class SpaceTrackerWindow(QMainWindow):
    """Fenêtre principale du simulateur de suivi spatial."""

    STATUS_COLORS = {
        "nominal": QColor(0, 200, 0),
        "warning": QColor(255, 165, 0),
        "critical": QColor(255, 0, 0),
        "deorbited": QColor(100, 100, 100),
    }

    DEBRIS_COLORS = {
        "small": QColor(150, 150, 150),
        "medium": QColor(200, 200, 100),
        "large": QColor(255, 100, 100),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mission Control - Satellite Tracker")
        self.setMinimumSize(1100, 700)

        self._simulation = Simulation()
        self._selected_satellite: str | None = None

        self._init_simulation()
        self._setup_ui()
        self._setup_timer()

    def _init_simulation(self):
        """Initialise la simulation avec des satellites de départ."""
        sats = [
            Satellite("ISS", 200, 300, 1.5, 45, fuel=80),
            Satellite("Hubble", 500, 150, 1.0, 180, fuel=60),
            Satellite("Sentinel", 350, 450, 2.0, 90, fuel=100),
            Satellite("GPS-VII", 600, 350, 0.8, 270, fuel=70),
        ]
        for s in sats:
            self._simulation.add_satellite(s)

    def _setup_ui(self):
        """Construit l'interface utilisateur."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Radar
        self._scene = QGraphicsScene(0, 0, 800, 600)
        self._radar = RadarView(self._scene)
        main_layout.addWidget(self._radar, stretch=3)

        # Panneau de contrôle
        control_panel = QVBoxLayout()
        main_layout.addLayout(control_panel, stretch=1)

        # Stats
        stats_group = QGroupBox("Statistiques")
        stats_layout = QVBoxLayout()
        self._score_label = QLabel("Score : 0")
        self._tick_label = QLabel("Tick : 0")
        self._collision_label = QLabel("Collisions : 0")
        self._deorbit_label = QLabel("Desorbites : 0")
        self._debris_label = QLabel("Debris en zone : 0")
        for lbl in [self._score_label, self._tick_label, self._collision_label,
                     self._deorbit_label, self._debris_label]:
            lbl.setStyleSheet("color: #00ff00; font-family: monospace; font-size: 13px;")
            stats_layout.addWidget(lbl)
        stats_group.setLayout(stats_layout)
        control_panel.addWidget(stats_group)

        # Sélection satellite
        sat_group = QGroupBox("Controle Satellite")
        sat_layout = QVBoxLayout()

        self._sat_combo = QComboBox()
        for sat in self._simulation.satellites:
            self._sat_combo.addItem(sat.name)
        self._sat_combo.currentTextChanged.connect(self._on_satellite_selected)
        sat_layout.addWidget(QLabel("Satellite :"))
        sat_layout.addWidget(self._sat_combo)

        self._sat_info = QLabel("Selectionnez un satellite")
        self._sat_info.setStyleSheet("color: #aaddaa; font-family: monospace; font-size: 12px;")
        self._sat_info.setWordWrap(True)
        sat_layout.addWidget(self._sat_info)

        # Cap
        sat_layout.addWidget(QLabel("Cap (degres) :"))
        self._angle_slider = QSlider(Qt.Orientation.Horizontal)
        self._angle_slider.setRange(0, 359)
        self._angle_slider.setValue(0)
        self._angle_label = QLabel("0")
        self._angle_slider.valueChanged.connect(
            lambda v: self._angle_label.setText(f"{v}")
        )
        sat_layout.addWidget(self._angle_slider)
        sat_layout.addWidget(self._angle_label)

        btn_angle = QPushButton("Changer le cap")
        btn_angle.clicked.connect(self._change_angle)
        sat_layout.addWidget(btn_angle)

        # Vitesse
        sat_layout.addWidget(QLabel("Vitesse :"))
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(5, 50)
        self._speed_slider.setValue(15)
        self._speed_label = QLabel("1.5")
        self._speed_slider.valueChanged.connect(
            lambda v: self._speed_label.setText(f"{v / 10:.1f}")
        )
        sat_layout.addWidget(self._speed_slider)
        sat_layout.addWidget(self._speed_label)

        btn_speed = QPushButton("Changer la vitesse")
        btn_speed.clicked.connect(self._change_speed)
        sat_layout.addWidget(btn_speed)

        btn_deorbit = QPushButton("Desorbiter")
        btn_deorbit.setStyleSheet("background-color: #aa3333; color: white; font-weight: bold;")
        btn_deorbit.clicked.connect(self._deorbit_selected)
        sat_layout.addWidget(btn_deorbit)

        sat_group.setLayout(sat_layout)
        control_panel.addWidget(sat_group)

        # Journal
        event_group = QGroupBox("Journal de bord")
        event_layout = QVBoxLayout()
        self._event_log = QTextEdit()
        self._event_log.setReadOnly(True)
        self._event_log.setMaximumHeight(150)
        self._event_log.setStyleSheet(
            "background-color: #0a0a1e; color: #00dd00; font-family: monospace; font-size: 11px;"
        )
        event_layout.addWidget(self._event_log)
        event_group.setLayout(event_layout)
        control_panel.addWidget(event_group)

        # Boutons
        btn_layout = QHBoxLayout()
        self._btn_pause = QPushButton("Pause")
        self._btn_pause.clicked.connect(self._toggle_pause)
        btn_layout.addWidget(self._btn_pause)

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self._reset)
        btn_layout.addWidget(btn_reset)
        control_panel.addLayout(btn_layout)

        control_panel.addStretch()

        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QGroupBox { color: #aaddaa; font-weight: bold; border: 1px solid #2a4a2a;
                        border-radius: 4px; margin-top: 8px; padding-top: 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { background-color: #2a4a2a; color: #aaddaa; border: 1px solid #3a6a3a;
                          border-radius: 4px; padding: 6px; font-size: 12px; }
            QPushButton:hover { background-color: #3a6a3a; }
            QComboBox { background-color: #1a2a1a; color: #aaddaa; border: 1px solid #2a4a2a; }
            QSlider::groove:horizontal { background: #2a4a2a; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #00dd00; width: 14px; margin: -4px 0;
                                          border-radius: 7px; }
            QLabel { color: #88aa88; font-size: 12px; }
        """)

    def _setup_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._game_loop)
        self._timer.start(100)
        self._paused = False

    def _game_loop(self):
        if self._paused or self._simulation.game_over:
            if self._simulation.game_over:
                self._event_log.append("GAME OVER - Tous les satellites perdus !")
                self._timer.stop()
            return
        self._simulation.tick()
        self._update_display()
        self._update_stats()
        for event in self._simulation.pop_events():
            self._event_log.append(event)

    def _update_display(self):
        self._scene.clear()

        for deb in self._simulation.debris_list:
            if not deb.active:
                continue
            color = self.DEBRIS_COLORS.get(deb.size, QColor(150, 150, 150))
            r = deb.danger_radius / 2
            self._scene.addEllipse(
                deb.x - r, deb.y - r, r * 2, r * 2,
                QPen(color, 1), QBrush(color.darker(150))
            )
            label = self._scene.addText(deb.name, QFont("Monospace", 7))
            label.setDefaultTextColor(color.lighter(120))
            label.setPos(deb.x + r + 2, deb.y - 8)

        for sat in self._simulation.satellites:
            if not sat.active:
                continue
            color = self.STATUS_COLORS.get(sat.status, QColor(200, 200, 200))
            is_selected = (sat.name == self._selected_satellite)

            r = 10
            pen = QPen(QColor(255, 255, 0), 2) if is_selected else QPen(color, 1)
            self._scene.addEllipse(
                sat.x - r, sat.y - r, r * 2, r * 2,
                pen, QBrush(color.darker(120))
            )

            rad = math.radians(sat.angle)
            line_len = 20
            self._scene.addLine(
                sat.x, sat.y,
                sat.x + line_len * math.cos(rad),
                sat.y + line_len * math.sin(rad),
                QPen(color, 2)
            )

            label_text = f"{sat.name}\nFuel:{sat.fuel:.0f}%"
            label = self._scene.addText(label_text, QFont("Monospace", 8))
            label.setDefaultTextColor(color)
            label.setPos(sat.x + 14, sat.y - 16)

            if sat.status in ("warning", "critical"):
                warn_pen = QPen(QColor(255, 0, 0, 100), 1, Qt.PenStyle.DashLine)
                self._scene.addEllipse(sat.x - 40, sat.y - 40, 80, 80, warn_pen)

        self._update_satellite_info()

    def _update_stats(self):
        stats = self._simulation.get_stats()
        self._score_label.setText(f"Score : {stats['score']}")
        self._tick_label.setText(f"Tick : {stats['tick']}")
        self._collision_label.setText(f"Collisions : {stats['collisions']}")
        self._deorbit_label.setText(f"Desorbites : {stats['desorbites']}")
        self._debris_label.setText(f"Debris en zone : {stats['debris_en_zone']}")

    def _update_satellite_info(self):
        if not self._selected_satellite:
            return
        for sat in self._simulation.satellites:
            if sat.name == self._selected_satellite:
                self._sat_info.setText(
                    f"Nom: {sat.name}\n"
                    f"Position: ({sat.x:.1f}, {sat.y:.1f})\n"
                    f"Vitesse: {sat.speed:.1f}\n"
                    f"Cap: {sat.angle:.0f}\n"
                    f"Fuel: {sat.fuel:.1f}%\n"
                    f"Status: {sat.status}"
                )
                return

    def _on_satellite_selected(self, name: str):
        self._selected_satellite = name

    def _change_angle(self):
        if not self._selected_satellite:
            return
        for sat in self._simulation.satellites:
            if sat.name == self._selected_satellite and sat.active:
                sat.change_angle(self._angle_slider.value())
                self._event_log.append(f"{sat.name} : nouveau cap {self._angle_slider.value()}")

    def _change_speed(self):
        if not self._selected_satellite:
            return
        for sat in self._simulation.satellites:
            if sat.name == self._selected_satellite and sat.active:
                sat.change_speed(self._speed_slider.value() / 10)
                self._event_log.append(
                    f"{sat.name} : nouvelle vitesse {self._speed_slider.value() / 10:.1f}"
                )

    def _deorbit_selected(self):
        if self._selected_satellite:
            self._simulation.deorbit_satellite(self._selected_satellite)

    def _toggle_pause(self):
        self._paused = not self._paused
        self._btn_pause.setText("Reprendre" if self._paused else "Pause")

    def _reset(self):
        self._timer.stop()
        self._simulation = Simulation()
        self._init_simulation()
        self._scene.clear()
        self._event_log.clear()
        self._paused = False
        self._btn_pause.setText("Pause")
        self._timer.start(100)


def main():
    app = QApplication(sys.argv)
    window = SpaceTrackerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
