import math
import random
import sys
import time
from datetime import datetime  # <-- NEW

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
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QMenu,
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

        # Typing Tracker
        self.last_type_time = 0.0
        self.kb_listener = keyboard.Listener(on_press=self.on_key_press)
        self.kb_listener.start()

        # Speech Bubble
        self.speech_text = ""

        # Speech & Memory
        self.fixed_speech = ""
        self.active_speech = ""
        self.user_name = "Parth"
        self.reminders = []

        # --- NEW: Pomodoro Variables ---
        self.pomo_state = (
            "OFF"  # Can be 'OFF', 'FOCUS', 'BREAK_ALARM', 'BREAK', 'WORK_ALARM'
        )
        self.pomo_focus_duration = 0
        self.pomo_break_duration = 0
        self.pomo_end_time = 0

        self.init_ui()
        self.init_timers()

    def on_key_press(self, key):
        # Every time you hit a key, update the timestamp
        self.last_type_time = time.time()

    def init_ui(self):
        # Increased canvas size to 150x150 for more detailed drawing
        self.resize(250, 250)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 250, 250)
        self.update_sprite()

    def update_sprite(self):
        pixmap = QPixmap(250, 250)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- SHIFT CAT TO BOTTOM OF NEW CANVAS ---
        # This moves the 0,0 drawing coordinate 50px right and 100px down
        painter.translate(50, 100)

        # --- CAT COLORS ---
        fur_main = QColor(229, 134, 56)
        fur_dark = QColor(200, 110, 40)
        belly = QColor(255, 235, 205)
        inner_ear = QColor(244, 164, 176)
        eye_bg = QColor(212, 225, 87)
        nose_col = QColor(255, 138, 152)

        painter.setPen(Qt.PenStyle.NoPen)

        # --- ANIMATION MATH ---
        paw_swing_l = 0
        paw_swing_r = 0
        body_y_offset = 0
        dangle = 0

        if self.pet_state == "IDLE":
            body_y_offset = math.sin(self.step_counter * 0.5) * 1.5
        elif self.pet_state == "DRAG":
            dangle = 8
            body_y_offset = -5
        elif self.pet_state == "JUMPING":
            # Fast, high bounce! (Negative Y moves the cat UP)
            body_y_offset = -abs(math.sin(self.step_counter * 3)) * 40
            dangle = 5  # Paws dangle a bit when airborne

        painter.save()

        if self.pet_state == "DRAG":
            lean = max(-45.0, min(45.0, self.drag_vx))
            painter.translate(75, 75)
            painter.rotate(lean)
            stretch = abs(lean) / 100.0
            painter.scale(1.0 - (stretch * 0.5), 1.0 + stretch)
            painter.translate(-75, -75)

        # 1. Tail
        path = QPainterPath()
        path.moveTo(40, 110 + body_y_offset)
        path.cubicTo(10, 110, 10, 70, 30, 60)
        pen = QPen(fur_dark, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)

        # 2. Back Legs
        painter.setBrush(fur_dark)
        painter.drawEllipse(
            QRectF(50 + paw_swing_r, 115 + dangle + body_y_offset, 16, 20)
        )
        painter.drawEllipse(
            QRectF(84 + paw_swing_l, 115 + dangle + body_y_offset, 16, 20)
        )

        # 3. Main Body & Chest
        painter.setBrush(fur_main)
        painter.drawEllipse(QRectF(45, 65 + body_y_offset, 60, 60))
        painter.setBrush(belly)
        painter.drawEllipse(QRectF(55, 75 + body_y_offset, 40, 45))

        # 4. Front Legs (Hands) & Typing Desk
        painter.setBrush(fur_main)
        if self.pet_state == "TYPING":
            painter.setBrush(QColor(80, 80, 80))
            painter.drawRect(QRectF(30, 130, 90, 20))
            left_pressed = math.sin(self.step_counter * 8) > 0
            painter.setBrush(
                QColor(255, 80, 80) if left_pressed else QColor(180, 50, 50)
            )
            painter.drawRect(QRectF(40, 125 if left_pressed else 120, 30, 10))
            painter.setBrush(
                QColor(80, 150, 255) if not left_pressed else QColor(50, 100, 180)
            )
            painter.drawRect(QRectF(80, 120 if left_pressed else 125, 30, 10))
            painter.setBrush(fur_main)
            painter.drawEllipse(QRectF(45, 120 if left_pressed else 110, 20, 20))
            painter.drawEllipse(QRectF(85, 110 if left_pressed else 120, 20, 20))
        else:
            painter.drawEllipse(
                QRectF(56 + paw_swing_l, 120 + dangle + body_y_offset, 14, 18)
            )
            painter.drawEllipse(
                QRectF(80 + paw_swing_r, 120 + dangle + body_y_offset, 14, 18)
            )

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

        # --- NEW: WHISKERS ---
        painter.setPen(
            QPen(QColor(0, 0, 0), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        # Left Whiskers
        painter.drawLine(50, 70, 30, 65)
        painter.drawLine(50, 75, 30, 75)
        painter.drawLine(50, 80, 30, 85)
        # Right Whiskers
        painter.drawLine(100, 70, 120, 65)
        painter.drawLine(100, 75, 120, 75)
        painter.drawLine(100, 80, 120, 85)

        # 8. Eyes & Mouth (Dynamic based on state)
        if self.pet_state == "PETTING":
            # Happy > < Eyes
            painter.setPen(
                QPen(QColor(0, 0, 0), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawLine(55, 52, 65, 59)  # > top
            painter.drawLine(65, 59, 55, 66)  # > bottom
            painter.drawLine(95, 52, 85, 59)  # < top
            painter.drawLine(85, 59, 95, 66)  # < bottom

            # Happy Smile
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawArc(66, 75, 9, 8, 180 * 16, 180 * 16)
            painter.drawArc(75, 75, 9, 8, 180 * 16, 180 * 16)

        else:
            # Normal Background Eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(eye_bg)
            painter.drawEllipse(QRectF(52, 50, 16, 18))
            painter.drawEllipse(QRectF(82, 50, 16, 18))

            # Cursor Tracking Math
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

            # Draw Pupils
            painter.setBrush(QColor(20, 20, 20))
            painter.drawEllipse(QRectF(56 + lx_off, 53 + ly_off, 8, 12))
            painter.drawEllipse(QRectF(86 + rx_off, 53 + ry_off, 8, 12))

            # Eye Highlights
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QRectF(58 + lx_off, 54 + ly_off, 3, 4))
            painter.drawEllipse(QRectF(88 + rx_off, 54 + ry_off, 3, 4))

            # --- NEW: DYNAMIC MOUTH ---
            if self.pet_state == "JUMPING":
                # Cute 'o' mouth
                painter.setBrush(QColor(0, 0, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(72, 75, 6, 8))
            elif self.pet_state == "DRAG":
                # Screaming wide mouth
                painter.setBrush(QColor(150, 50, 50))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(70, 75, 10, 15))
            else:
                # Normal 'w' smile
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

        # 9. Nose (Drawn last so it sits on top of the mouth lines)
        painter.setBrush(nose_col)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(70, 68, 10, 6))

        painter.restore()

        # --- NEW: WORD-WRAPPED SPEECH BUBBLE ---
        if hasattr(self, "active_speech") and self.active_speech != "":
            painter.save()
            font = painter.font()
            font.setFamily("Courier")
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            # Max bubble width limits how wide it gets before wrapping to a new line
            max_bubble_width = 140
            metrics = painter.fontMetrics()

            # Use QRect and Qt.TextFlag.TextWordWrap to calculate wrapped height
            text_rect = metrics.boundingRect(
                QRect(0, 0, max_bubble_width, 500),
                Qt.TextFlag.TextWordWrap,
                self.active_speech,
            )

            padding = 8
            b_width = text_rect.width() + (padding * 2)
            b_height = text_rect.height() + (padding * 2)

            b_x = 75 - (b_width / 2)
            b_y = 25 - b_height  # Starts right above the head

            # --- POMODORO COLORS ---
            bg_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)

            if hasattr(self, "pomo_state"):
                if self.pomo_state in ["FOCUS", "WORK_ALARM"]:
                    bg_color = QColor(220, 50, 50)  # Red
                    text_color = QColor(255, 255, 255)  # White
                elif self.pomo_state in ["BREAK", "BREAK_ALARM"]:
                    bg_color = QColor(50, 100, 220)  # Blue
                    text_color = QColor(255, 255, 255)  # White

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

            # Erase top line of tail using the background color
            painter.setPen(QPen(bg_color, 2))
            painter.drawLine(71, tail_y, 79, tail_y)

            # Draw text using our dynamic text color
            painter.setPen(text_color)
            # Draw the wrapped text inside our calculated box
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

        painter.end()
        self.label.setPixmap(pixmap)
        self.setMask(pixmap.mask())

    def init_timers(self):
        # AI Timer (Changes state every 3 to 6 seconds randomly)
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.change_state)
        self.state_timer.start(3000)

        # Main Game Loop / Physics Timer (Runs at ~30 FPS)
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_behavior)
        self.move_timer.start(30)

    def change_state(self):
        # Don't let random AI interrupt dragging, typing, or jumping
        if self.pet_state in ["DRAG", "TYPING", "JUMPING", "PETTING"]:
            return

        self.pet_state = "IDLE"
        self.state_timer.setInterval(random.randint(2000, 5000))
        self.step_counter = 0.0

    def update_behavior(self):
        self.step_counter += 0.2

        # --- Check Active Reminders ---
        current_dt = datetime.now().strftime("%Y-%m-%d %H:%M")

        for r in self.reminders[:]:
            if current_dt == r["time"]:
                self.active_speech = f"Hey {self.user_name}, {r['message']}!"
                self.pet_state = "JUMPING"
                self.reminders.remove(r)
                self.update_sprite()

        # --- Check if typing ---
        if time.time() - self.last_type_time < 0.3:
            self.pet_state = "TYPING"
        elif self.pet_state == "TYPING":
            self.pet_state = "IDLE"

        # --- NEW: Hover / Petting Detection ---
        if self.pet_state in ["IDLE", "PETTING"]:
            # Get the mouse position relative to our drawing grid
            mouse_pos = self.mapFromGlobal(QCursor.pos())
            mx, my = mouse_pos.x() - 50, mouse_pos.y() - 100

            # Use distance math to check if the cursor is near the center of the head (approx 75, 62)
            dist = math.hypot(mx - 75, my - 62)

            if dist < 35:  # If cursor is within 35 pixels of the head center
                self.pet_state = "PETTING"
            else:
                self.pet_state = "IDLE"

        # --- NEW: POMODORO LOGIC ---
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

        # --- Drag Physics (Friction) ---
        if self.pet_state == "DRAG":
            self.drag_vx *= 0.7

    # --- Mouse Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Acknowledge the reminder/alarm and calm the cat down
            if self.pet_state == "JUMPING":
                self.pet_state = "IDLE"

                # --- NEW: Pomodoro Alarm Logic ---
                if self.pomo_state == "BREAK_ALARM":
                    self.pomo_state = "BREAK"
                    self.pomo_end_time = time.time() + self.pomo_break_duration
                elif self.pomo_state == "WORK_ALARM":
                    self.pomo_state = "FOCUS"
                    self.pomo_end_time = time.time() + self.pomo_focus_duration
                else:
                    self.active_speech = self.fixed_speech  # Regular reminder

                self.update_sprite()
                event.accept()
                return

            # Normal drag behavior
            self.pet_state = "DRAG"
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            menu.setStyleSheet(
                "QMenu { background-color: white; border: 1px solid black; }"
            )

            msg_action = menu.addAction("Fixed message")
            clear_action = menu.addAction("Clear message")
            menu.addSeparator()
            name_action = menu.addAction("Tell my name")
            remind_action = menu.addAction("Set a reminder")
            menu.addSeparator()

            # --- NEW: Pomodoro Menu ---
            pomo_action = menu.addAction("Start Pomodoro")
            stop_pomo_action = menu.addAction("Stop Pomodoro")

            action = menu.exec(event.globalPosition().toPoint())

            if action == msg_action:
                text, ok = QInputDialog.getText(
                    self, "Cat Speech", "What should the cat say?"
                )
                if ok:
                    self.fixed_speech = text
                    self.active_speech = text
                    self.update_sprite()
            elif action == clear_action:
                self.fixed_speech = ""
                self.active_speech = ""
                self.update_sprite()
            elif action == name_action:
                text, ok = QInputDialog.getText(
                    self, "Name", "What should I call you?", text=self.user_name
                )
                if ok and text:
                    self.user_name = text
            elif action == remind_action:
                dialog = QDialog(self)
                dialog.setWindowTitle("Set Reminder")
                dialog.setStyleSheet("background-color: white; color: black;")
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel("Select Date and Time:"))

                dt_edit = QDateTimeEdit(dialog)
                dt_edit.setDateTime(QDateTime.currentDateTime())
                dt_edit.setCalendarPopup(True)
                layout.addWidget(dt_edit)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok
                    | QDialogButtonBox.StandardButton.Cancel,
                    dialog,
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_dt = dt_edit.dateTime().toPyDateTime()
                    time_str = selected_dt.strftime("%Y-%m-%d %H:%M")
                    msg, ok2 = QInputDialog.getText(
                        self, "Reminder Message", "What should I remind you about?"
                    )
                    if ok2 and msg:
                        self.reminders.append({"time": time_str, "message": msg})

            # --- NEW: Start Pomodoro ---
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

            # --- NEW: Stop Pomodoro ---
            elif action == stop_pomo_action:
                self.pomo_state = "OFF"
                self.active_speech = self.fixed_speech
                self.update_sprite()

            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.pet_state == "DRAG":
            new_pos = event.globalPosition().toPoint() - self.drag_position

            # Calculate how far we moved on the X axis this frame
            delta_x = new_pos.x() - self.x()

            # Add that movement to our velocity (creates momentum)
            self.drag_vx += delta_x * 0.3

            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Force the state back to IDLE the second you let go
            self.pet_state = "IDLE"
            # Redraw the cat immediately so the mouth snaps back to normal
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
