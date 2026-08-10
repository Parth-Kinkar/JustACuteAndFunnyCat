import json
import math
import os
import random
import sys
import time
from datetime import datetime

from pynput import keyboard
from PyQt6.QtCore import QDateTime, QPoint, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygon,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # State & Physics
        self.pet_state = "IDLE"
        self.drag_position = QPoint()

        # Animation counters & Physics
        self.step_counter = 0.0
        self.drag_vx = 0.0
        self.drag_vy = 0.0

        # Typing Tracker
        self.last_type_time = 0.0
        self.kb_listener = keyboard.Listener(on_press=self.on_key_press)
        self.kb_listener.start()

        # Speech Bubble
        self.speech_text = ""

        # Speech & Memory Defaults
        self.fixed_speech = ""
        self.active_speech = ""
        self.user_name = "Parth"
        self.reminders = []
        self.cat_color = "Orange"

        # --- Load Saved Memory ---
        self.load_config()

        # Pomodoro Variables
        self.pomo_state = "OFF"
        self.pomo_focus_duration = 0
        self.pomo_break_duration = 0
        self.pomo_end_time = 0

        # --- NEW: Particle System ---
        self.particles = []

        self.init_ui()
        self.init_timers()

    def load_config(self):
        config_file = "cat_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    self.cat_color = data.get("cat_color", "Orange")
                    self.fixed_speech = data.get("fixed_speech", "")
                    self.active_speech = self.fixed_speech
                    self.user_name = data.get("user_name", "Parth")
            except Exception as e:
                print(f"Could not load config: {e}")

    def save_config(self):
        config_file = "cat_config.json"
        data = {
            "cat_color": self.cat_color,
            "fixed_speech": self.fixed_speech,
            "user_name": self.user_name,
        }
        try:
            with open(config_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Could not save config: {e}")

    def on_key_press(self, key):
        self.last_type_time = time.time()

    def init_ui(self):
        self.resize(250, 250)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 250, 250)
        self.update_sprite()

    def update_sprite(self):
        pixmap = QPixmap(250, 250)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(50, 100)

        color_themes = {
            "Orange": {
                "main": QColor(229, 134, 56),
                "dark": QColor(200, 110, 40),
                "belly": QColor(255, 235, 205),
            },
            "Black": {
                "main": QColor(45, 45, 45),
                "dark": QColor(25, 25, 25),
                "belly": QColor(80, 80, 80),
            },
            "White": {
                "main": QColor(245, 245, 245),
                "dark": QColor(210, 210, 210),
                "belly": QColor(255, 255, 255),
            },
            "Grey": {
                "main": QColor(140, 145, 150),
                "dark": QColor(110, 115, 120),
                "belly": QColor(200, 205, 210),
            },
        }

        theme = color_themes.get(self.cat_color, color_themes["Orange"])
        fur_main = theme["main"]
        fur_dark = theme["dark"]
        belly = theme["belly"]

        inner_ear = QColor(244, 164, 176)
        eye_bg = QColor(212, 225, 87)
        nose_col = QColor(255, 138, 152)

        painter.setPen(Qt.PenStyle.NoPen)

        paw_swing_l = 0
        paw_swing_r = 0
        scramble_l = 0  # NEW: Frantic drag legs
        scramble_r = 0  # NEW: Frantic drag legs
        body_y_offset = 0
        dangle = 0
        is_sitting = self.pet_state in ["IDLE", "PETTING"]

        if self.pet_state == "IDLE":
            body_y_offset = math.sin(self.step_counter * 0.5) * 1.5
        elif self.pet_state == "DRAG":
            dangle = 8
            body_y_offset = -5
            # Frantic up-and-down scrambling!
            scramble_l = math.sin(self.step_counter * 25) * 8
            scramble_r = math.cos(self.step_counter * 25) * 8
        elif self.pet_state == "JUMPING":
            body_y_offset = -abs(math.sin(self.step_counter * 3)) * 40
            dangle = 5

        painter.save()

        if self.pet_state == "DRAG":
            lean = max(-45.0, min(45.0, self.drag_vx))
            painter.translate(75, 75)
            painter.rotate(lean)
            painter.translate(-75, -75)

        # 1. Tail
        painter.save()
        if self.pet_state == "PETTING":
            # Smooth, happy tail wag!
            wag_angle = math.sin(self.step_counter * 8) * 15
            painter.translate(40, 110 + body_y_offset)
            painter.rotate(wag_angle)
            painter.translate(-40, -(110 + body_y_offset))

        path = QPainterPath()
        path.moveTo(40, 110 + body_y_offset)
        path.cubicTo(10, 110, 10, 70, 30, 60)
        pen = QPen(fur_dark, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.restore()

        # 2. Back Legs
        painter.setBrush(fur_dark)
        if self.pet_state == "DRAG":
            # Scrambling back paws
            painter.drawEllipse(QRectF(48, 115 + dangle + scramble_l, 14, 20))
            painter.drawEllipse(QRectF(88, 115 + dangle + scramble_r, 14, 20))
        elif not is_sitting and self.pet_state != "TYPING":
            painter.drawEllipse(
                QRectF(50 + paw_swing_r, 115 + dangle + body_y_offset, 16, 20)
            )
            painter.drawEllipse(
                QRectF(84 + paw_swing_l, 115 + dangle + body_y_offset, 16, 20)
            )
        elif is_sitting:
            painter.drawEllipse(QRectF(42, 112 + body_y_offset, 18, 14))
            painter.drawEllipse(QRectF(90, 112 + body_y_offset, 18, 14))

        # 3. Main Body & Chest
        painter.setBrush(fur_main)
        if is_sitting:
            painter.drawEllipse(QRectF(40, 95 + body_y_offset, 70, 30))
        painter.drawEllipse(QRectF(45, 65 + body_y_offset, 60, 60))

        painter.setBrush(belly)
        if is_sitting:
            painter.drawEllipse(QRectF(50, 95 + body_y_offset, 50, 25))
        painter.drawEllipse(QRectF(55, 75 + body_y_offset, 40, 45))

        # 4. Front Legs (Hands) & Typing Desk
        painter.setBrush(fur_main)
        if self.pet_state == "TYPING":
            painter.setBrush(QColor(60, 60, 60))
            painter.drawRoundedRect(QRectF(25, 130, 100, 25), 4, 4)
            left_pressed = math.sin(self.step_counter * 8) > 0

            painter.setBrush(QColor(100, 100, 100))
            painter.drawRoundedRect(QRectF(35, 120, 35, 25), 4, 4)
            l_offset = 5 if left_pressed else 0
            painter.setBrush(QColor(220, 220, 220))
            painter.drawRoundedRect(QRectF(35, 115 + l_offset, 35, 20), 4, 4)

            painter.setBrush(QColor(100, 100, 100))
            painter.drawRoundedRect(QRectF(80, 120, 35, 25), 4, 4)
            r_offset = 0 if left_pressed else 5
            painter.setBrush(QColor(220, 220, 220))
            painter.drawRoundedRect(QRectF(80, 115 + r_offset, 35, 20), 4, 4)

            painter.setBrush(fur_main)
            painter.drawEllipse(QRectF(44, 90 + int(l_offset / 2), 16, 35))
            painter.drawEllipse(QRectF(89, 90 + int(r_offset / 2), 16, 35))
            painter.drawEllipse(QRectF(42, 115 + l_offset, 20, 20))
            painter.drawEllipse(QRectF(87, 115 + r_offset, 20, 20))

        elif is_sitting:
            painter.drawEllipse(QRectF(58, 112 + body_y_offset, 14, 16))
            painter.drawEllipse(QRectF(78, 112 + body_y_offset, 14, 16))

        elif self.pet_state == "DRAG":
            # Scrambling front paws (opposite phase to back legs)
            painter.drawEllipse(QRectF(54, 115 + dangle + scramble_r, 12, 18))
            painter.drawEllipse(QRectF(84, 115 + dangle + scramble_l, 12, 18))

        else:
            painter.drawEllipse(
                QRectF(56 + paw_swing_l, 120 + dangle + body_y_offset, 14, 18)
            )
            painter.drawEllipse(
                QRectF(80 + paw_swing_r, 120 + dangle + body_y_offset, 14, 18)
            )

        # --- HEAD ROTATION (Nuzzle) ---
        painter.save()
        if self.pet_state == "PETTING":
            # Smooth, cute head tilt (nuzzle) instead of jittery horizontal vibration
            nuzzle_angle = math.sin(self.step_counter * 5) * 8
            painter.translate(75, 80)  # Pivot near the neck
            painter.rotate(nuzzle_angle)
            painter.translate(-75, -80)

        # 5. Ears
        painter.setBrush(fur_main)
        painter.drawPolygon(QPolygon([QPoint(45, 55), QPoint(35, 25), QPoint(65, 40)]))
        painter.drawPolygon(
            QPolygon([QPoint(105, 55), QPoint(115, 25), QPoint(85, 40)])
        )
        painter.setBrush(inner_ear)
        painter.drawPolygon(QPolygon([QPoint(48, 52), QPoint(42, 32), QPoint(60, 42)]))
        painter.drawPolygon(
            QPolygon([QPoint(102, 52), QPoint(108, 32), QPoint(90, 42)])
        )

        # 6. Head
        painter.setBrush(fur_main)
        painter.drawEllipse(QRectF(40, 35, 70, 55))

        # 7. Snout
        painter.setBrush(belly)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(55, 65, 40, 20))

        # Whiskers
        painter.setPen(
            QPen(QColor(0, 0, 0), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(50, 70, 30, 65)
        painter.drawLine(50, 75, 30, 75)
        painter.drawLine(50, 80, 30, 85)
        painter.drawLine(100, 70, 120, 65)
        painter.drawLine(100, 75, 120, 75)
        painter.drawLine(100, 80, 120, 85)

        # 8. Eyes & Mouth
        if self.pet_state == "PETTING":
            painter.setPen(
                QPen(
                    QColor(0, 0, 0),
                    3,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            painter.drawLine(55, 52, 65, 59)
            painter.drawLine(65, 59, 55, 66)
            painter.drawLine(95, 52, 85, 59)
            painter.drawLine(85, 59, 95, 66)
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawArc(66, 75, 9, 8, 180 * 16, 180 * 16)
            painter.drawArc(75, 75, 9, 8, 180 * 16, 180 * 16)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(eye_bg)
            painter.drawEllipse(QRectF(52, 50, 16, 18))
            painter.drawEllipse(QRectF(82, 50, 16, 18))

            mouse_pos = self.mapFromGlobal(QCursor.pos())
            mx, my = mouse_pos.x() - 50, mouse_pos.y() - 100

            def get_pupil_offset(eye_cx, eye_cy):
                dx, dy = mx - eye_cx, my - eye_cy
                dist = math.hypot(dx, dy)
                if dist == 0:
                    return 0, 0
                scale = min(dist / 25, 4)
                angle = math.atan2(dy, dx)
                return scale * math.cos(angle), scale * math.sin(angle)

            lx_off, ly_off = get_pupil_offset(60, 59)
            rx_off, ry_off = get_pupil_offset(90, 59)

            painter.setBrush(QColor(20, 20, 20))
            painter.drawEllipse(QRectF(56 + lx_off, 53 + ly_off, 8, 12))
            painter.drawEllipse(QRectF(86 + rx_off, 53 + ry_off, 8, 12))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QRectF(58 + lx_off, 54 + ly_off, 3, 4))
            painter.drawEllipse(QRectF(88 + rx_off, 54 + ry_off, 3, 4))

            if self.pet_state == "JUMPING":
                painter.setBrush(QColor(0, 0, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(72, 75, 6, 8))
            elif self.pet_state == "DRAG":
                painter.setBrush(QColor(150, 50, 50))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(70, 75, 10, 15))
            else:
                painter.setPen(
                    QPen(
                        QColor(0, 0, 0),
                        2,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                    )
                )
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawArc(66, 75, 9, 8, 180 * 16, 180 * 16)
                painter.drawArc(75, 75, 9, 8, 180 * 16, 180 * 16)

        # 9. Nose
        painter.setBrush(nose_col)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(70, 68, 10, 6))

        # Restore from the head translation/transformations
        painter.restore()

        # --- DRAW PARTICLES (Hearts & Sweat) ---
        for p in self.particles:
            painter.save()
            painter.translate(p["x"], p["y"])
            painter.scale(p["scale"], p["scale"])

            if p.get("type", "heart") == "heart":
                painter.setBrush(QColor(255, 50, 80))
                painter.setPen(Qt.PenStyle.NoPen)

                h_path = QPainterPath()
                h_path.moveTo(0, 2)
                h_path.cubicTo(-8, -6, -12, 4, 0, 12)
                h_path.cubicTo(12, 4, 8, -6, 0, 2)
                painter.drawPath(h_path)
            else:
                # SWEAT
                painter.setBrush(QColor(100, 200, 255))  # Cyan/Blue
                painter.setPen(Qt.PenStyle.NoPen)

                s_path = QPainterPath()
                s_path.moveTo(0, -6)
                s_path.cubicTo(4, 0, 4, 6, 0, 6)
                s_path.cubicTo(-4, 6, -4, 0, 0, -6)
                painter.drawPath(s_path)

            painter.restore()

        # Speech Bubble
        if hasattr(self, "active_speech") and self.active_speech != "":
            painter.save()
            font = painter.font()
            font.setFamily("Courier")
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            max_bubble_width = 140
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(
                QRect(0, 0, max_bubble_width, 500),
                Qt.TextFlag.TextWordWrap,
                self.active_speech,
            )

            padding = 8
            b_width = text_rect.width() + (padding * 2)
            b_height = text_rect.height() + (padding * 2)
            b_x = 75 - (b_width / 2)
            b_y = 25 - b_height

            bg_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)

            if hasattr(self, "pomo_state"):
                if self.pomo_state in ["FOCUS", "WORK_ALARM"]:
                    bg_color = QColor(220, 50, 50)
                    text_color = QColor(255, 255, 255)
                elif self.pomo_state in ["BREAK", "BREAK_ALARM"]:
                    bg_color = QColor(50, 100, 220)
                    text_color = QColor(255, 255, 255)

            painter.setBrush(bg_color)
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRoundedRect(
                int(b_x), int(b_y), int(b_width), int(b_height), 4, 4
            )

            tail_y = int(b_y + b_height)
            painter.drawPolygon(
                QPolygon(
                    [QPoint(70, tail_y), QPoint(80, tail_y), QPoint(75, tail_y + 6)]
                )
            )
            painter.setPen(QPen(bg_color, 2))
            painter.drawLine(71, tail_y, 79, tail_y)

            painter.setPen(text_color)
            painter.drawText(
                QRect(
                    int(b_x + padding),
                    int(b_y + padding),
                    text_rect.width(),
                    text_rect.height(),
                ),
                Qt.TextFlag.TextWordWrap,
                self.active_speech,
            )
            painter.restore()
        painter.restore()
        painter.end()
        self.label.setPixmap(pixmap)
        self.setMask(pixmap.mask())

    def init_timers(self):
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.change_state)
        self.state_timer.start(3000)

        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_behavior)
        self.move_timer.start(50)

    def change_state(self):
        if self.pet_state in ["DRAG", "TYPING", "JUMPING", "PETTING"]:
            return

        self.pet_state = "IDLE"
        self.state_timer.setInterval(random.randint(2000, 5000))
        self.step_counter = 0.0

    def update_behavior(self):
        self.step_counter += 0.2

        current_dt = datetime.now().strftime("%Y-%m-%d %H:%M")

        for r in self.reminders[:]:
            if current_dt == r["time"]:
                self.active_speech = f"Hey {self.user_name}, {r['message']}!"
                self.pet_state = "JUMPING"
                self.reminders.remove(r)
                self.update_sprite()

        if time.time() - self.last_type_time < 0.3:
            self.pet_state = "TYPING"
        elif self.pet_state == "TYPING":
            self.pet_state = "IDLE"

        if self.pet_state in ["IDLE", "PETTING"]:
            mouse_pos = self.mapFromGlobal(QCursor.pos())
            mx, my = mouse_pos.x() - 50, mouse_pos.y() - 100
            dist = math.hypot(mx - 75, my - 62)

            if dist < 35:
                self.pet_state = "PETTING"
            else:
                self.pet_state = "IDLE"

        # --- NEW: PARTICLE PHYSICS (Hearts & Sweat) ---
        for p in self.particles[:]:
            if p.get("type", "heart") == "heart":
                p["y"] -= p["speed"]
            else:
                # Sweat drops have gravity and horizontal momentum
                p["x"] += p["speed_x"]
                p["speed_y"] += 0.5  # Gravity pulling it down
                p["y"] += p["speed_y"]

            p["scale"] -= 0.03
            if p["scale"] <= 0:
                self.particles.remove(p)

        if self.pet_state == "PETTING":
            if random.random() < 0.3:
                self.particles.append(
                    {
                        "type": "heart",
                        "x": random.randint(55, 95),
                        "y": random.randint(10, 30),
                        "speed": random.uniform(1.0, 2.0),
                        "scale": random.uniform(0.8, 1.2),
                    }
                )

        elif self.pet_state == "DRAG":
            # Rapidly shoot sweat drops while being dragged
            if random.random() < 0.6:
                self.particles.append(
                    {
                        "type": "sweat",
                        "x": random.randint(40, 110),
                        "y": random.randint(20, 80),
                        "speed_x": random.uniform(-3.0, 3.0)
                        - (self.drag_vx * 0.05),  # Fly off opposite to movement
                        "speed_y": random.uniform(-4.0, 0.0),  # Shoot upwards initially
                        "scale": random.uniform(0.6, 1.0),
                    }
                )

        if self.pomo_state == "FOCUS":
            rem = int(self.pomo_end_time - time.time())
            if rem <= 0:
                self.pomo_state = "BREAK_ALARM"
                self.pet_state = "JUMPING"
                self.active_speech = "Time for a break!"
            else:
                mins, secs = divmod(rem, 60)
                self.active_speech = f"Focus {mins:02d}:{secs:02d}"

        elif self.pomo_state == "BREAK":
            rem = int(self.pomo_end_time - time.time())
            if rem <= 0:
                self.pomo_state = "WORK_ALARM"
                self.pet_state = "JUMPING"
                self.active_speech = "Break is over, time to work!"
            else:
                mins, secs = divmod(rem, 60)
                self.active_speech = f"Break {mins:02d}:{secs:02d}"

        self.update_sprite()

        if self.pet_state == "DRAG":
            self.drag_vx *= 0.7
            self.drag_vy *= 0.7

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.pet_state == "JUMPING":
                self.pet_state = "IDLE"

                if self.pomo_state == "BREAK_ALARM":
                    self.pomo_state = "BREAK"
                    self.pomo_end_time = time.time() + self.pomo_break_duration
                elif self.pomo_state == "WORK_ALARM":
                    self.pomo_state = "FOCUS"
                    self.pomo_end_time = time.time() + self.pomo_focus_duration
                else:
                    self.active_speech = self.fixed_speech

                self.update_sprite()
                event.accept()
                return

            self.pet_state = "DRAG"
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #1e1e1e;
                    color: white;
                    border: 1px solid #555555;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 6px 20px;
                }
                QMenu::item:selected {
                    background-color: #404040;
                    color: white;
                }
                QMenu::separator {
                    height: 1px;
                    background: #555555;
                    margin: 4px 0px;
                }
            """)

            msg_action = menu.addAction("Fixed message")
            clear_action = menu.addAction("Clear message")
            menu.addSeparator()
            name_action = menu.addAction("Tell my name")
            remind_action = menu.addAction("Set a reminder")
            menu.addSeparator()

            color_menu = menu.addMenu("Change Color")
            color_menu.setStyleSheet("""
                QMenu {
                    background-color: #1e1e1e;
                    color: white;
                    border: 1px solid #555555;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 6px 20px;
                }
                QMenu::item:selected {
                    background-color: #404040;
                    color: white;
                }
            """)
            color_actions = {
                color_menu.addAction("Orange"): "Orange",
                color_menu.addAction("Black"): "Black",
                color_menu.addAction("White"): "White",
                color_menu.addAction("Grey"): "Grey",
            }
            menu.addSeparator()

            pomo_action = menu.addAction("Start Pomodoro")
            stop_pomo_action = menu.addAction("Stop Pomodoro")
            menu.addSeparator()

            bye_action = menu.addAction("Bye bye")

            action = menu.exec(event.globalPosition().toPoint())

            if action == msg_action:
                text, ok = QInputDialog.getText(
                    self, "Cat Speech", "What should the cat say?"
                )
                if ok:
                    self.fixed_speech = text
                    self.active_speech = text
                    self.save_config()
                    self.update_sprite()
            elif action == clear_action:
                self.fixed_speech = ""
                self.active_speech = ""
                self.save_config()
                self.update_sprite()
            elif action == name_action:
                text, ok = QInputDialog.getText(
                    self, "Name", "What should I call you?", text=self.user_name
                )
                if ok and text:
                    self.user_name = text
                    self.save_config()
            elif action == remind_action:
                dialog = QDialog(self)
                dialog.setWindowTitle("Set Reminder")
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #1e1e1e;
                        color: white;
                    }
                    QLabel {
                        color: white;
                        font-weight: bold;
                    }
                    QCalendarWidget QWidget {
                        background-color: #2b2b2b;
                        color: white;
                    }
                    QCalendarWidget QToolButton {
                        color: white;
                        background-color: #3b3b3b;
                        border-radius: 3px;
                    }
                    QCalendarWidget QToolButton:hover {
                        background-color: #505050;
                    }
                    QCalendarWidget QMenu {
                        background-color: #1e1e1e;
                        color: white;
                    }
                    QCalendarWidget QSpinBox {
                        background-color: #2b2b2b;
                        color: white;
                    }
                    QCalendarWidget QAbstractItemView:enabled {
                        background-color: #1e1e1e;
                        color: white;
                        selection-background-color: #404040;
                        selection-color: white;
                    }
                    QTimeEdit {
                        background-color: #2b2b2b;
                        color: white;
                        border: 1px solid #555555;
                        padding: 4px;
                        border-radius: 3px;
                    }
                    QPushButton {
                        background-color: #3b3b3b;
                        color: white;
                        border: 1px solid #555555;
                        padding: 6px 12px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #505050;
                    }
                """)
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel("Select Date:"))

                calendar = QCalendarWidget(dialog)
                calendar.setGridVisible(True)
                layout.addWidget(calendar)

                time_layout = QHBoxLayout()
                time_layout.addWidget(QLabel("Select Time:"))
                time_edit = QTimeEdit(dialog)
                time_edit.setTime(QDateTime.currentDateTime().time())
                time_layout.addWidget(time_edit)
                layout.addLayout(time_layout)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok
                    | QDialogButtonBox.StandardButton.Cancel,
                    dialog,
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_date = calendar.selectedDate()
                    selected_time = time_edit.time()

                    time_str = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"

                    msg, ok2 = QInputDialog.getText(
                        self, "Reminder Message", "What should I remind you about?"
                    )
                    if ok2 and msg:
                        self.reminders.append({"time": time_str, "message": msg})

            elif action in color_actions:
                self.cat_color = color_actions[action]
                self.save_config()
                self.update_sprite()

            elif action == pomo_action:
                focus_mins, ok1 = QInputDialog.getInt(
                    self, "Pomodoro", "Focus time (minutes):", 25, 1, 120
                )
                if ok1:
                    break_mins, ok2 = QInputDialog.getInt(
                        self, "Pomodoro", "Break time (minutes):", 5, 1, 60
                    )
                    if ok2:
                        self.pomo_focus_duration = focus_mins * 60
                        self.pomo_break_duration = break_mins * 60
                        self.pomo_state = "FOCUS"
                        self.pomo_end_time = time.time() + self.pomo_focus_duration

            elif action == stop_pomo_action:
                self.pomo_state = "OFF"
                self.active_speech = self.fixed_speech
                self.update_sprite()

            elif action == bye_action:
                QApplication.quit()

            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.pet_state == "DRAG":
            new_pos = event.globalPosition().toPoint() - self.drag_position

            delta_x = new_pos.x() - self.x()
            delta_y = new_pos.y() - self.y()

            self.drag_vx += delta_x * 0.3
            self.drag_vy += delta_y * 0.3

            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pet_state = "IDLE"
            self.update_sprite()
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()

    screen_geo = app.primaryScreen().geometry()
    spawn_x = (screen_geo.width() - pet.width()) // 2
    spawn_y = screen_geo.height() - pet.height() - 50
    pet.move(spawn_x, spawn_y)

    pet.show()
    sys.exit(app.exec())
