#!/usr/bin/env python3

import argparse
import ast
import csv
import math
import random
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets


def parse_csi_line(line):
    start = line.find("CSI_DATA")
    if start < 0:
        return None

    row = next(csv.reader([line[start:].strip()]))
    values = ast.literal_eval(row[-1])
    amps = [
        math.hypot(values[i + 1], values[i])
        for i in range(0, len(values) - 1, 2)
    ]
    if not amps:
        return None

    return {
        "rssi": int(row[3]),
        "timestamp": int(row[18]),
        "mean_amp": sum(amps) / len(amps),
        "amps": amps,
    }


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def vector_distance(a, b):
    count = min(len(a), len(b))
    if count == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) for i in range(count)) / count


class CsiWorker(QtCore.QThread):
    values = QtCore.pyqtSignal(dict)
    status = QtCore.pyqtSignal(str)

    def __init__(self, port, baud, calibration_frames, motion_scale, presence_scale):
        super().__init__()
        self.port = port
        self.baud = baud
        self.calibration_frames = calibration_frames
        self.motion_scale = motion_scale
        self.presence_scale = presence_scale
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        import serial

        self.status.emit("opening serial")
        baseline_frames = []
        baseline = None
        previous = None
        motion_smooth = 0.0
        presence_smooth = 0.0
        frame = 0
        last_emit = 0.0

        try:
            with serial.Serial(self.port, self.baud, timeout=1) as stream:
                while self.running:
                    raw = stream.readline().decode("utf-8", "replace")
                    parsed = parse_csi_line(raw)
                    if not parsed:
                        continue

                    frame += 1
                    amps = parsed["amps"]

                    if baseline is None:
                        baseline_frames.append(amps)
                        progress = len(baseline_frames) / self.calibration_frames
                        self.values.emit(
                            {
                                "calibrating": True,
                                "progress": clamp(progress),
                                "frame": frame,
                                "rssi": parsed["rssi"],
                            }
                        )
                        if len(baseline_frames) >= self.calibration_frames:
                            width = min(len(item) for item in baseline_frames)
                            baseline = [
                                sum(item[i] for item in baseline_frames)
                                / len(baseline_frames)
                                for i in range(width)
                            ]
                            self.status.emit("calibrated")
                        continue

                    motion_raw = vector_distance(amps, previous) if previous else 0.0
                    presence_raw = vector_distance(amps, baseline)
                    previous = amps

                    motion = clamp(motion_raw / self.motion_scale)
                    presence = clamp(presence_raw / self.presence_scale)

                    motion_smooth = 0.78 * motion_smooth + 0.22 * motion
                    presence_smooth = 0.92 * presence_smooth + 0.08 * presence

                    now = time.monotonic()
                    if now - last_emit < 0.05:
                        continue
                    last_emit = now

                    self.values.emit(
                        {
                            "calibrating": False,
                            "frame": frame,
                            "rssi": parsed["rssi"],
                            "mean_amp": parsed["mean_amp"],
                            "motion_energy": motion_smooth,
                            "presence_confidence": presence_smooth,
                            "motion_raw": motion_raw,
                            "presence_raw": presence_raw,
                        }
                    )
        except Exception as exc:
            self.status.emit(f"error: {exc}")


class BlobView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invisible Waves - Live CSI Blob")
        self.resize(980, 640)
        self.setMinimumSize(720, 420)
        self.values = {
            "calibrating": True,
            "progress": 0.0,
            "motion_energy": 0.0,
            "presence_confidence": 0.0,
            "rssi": 0,
            "mean_amp": 0.0,
            "motion_raw": 0.0,
            "presence_raw": 0.0,
        }
        self.status = "starting"
        self.phase = 0.0
        self.noise = [random.random() * math.tau for _ in range(42)]

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def set_values(self, values):
        self.values.update(values)
        self.update()

    def set_status(self, status):
        self.status = status
        self.update()

    def tick(self):
        self.phase += 0.035 + self.values.get("motion_energy", 0.0) * 0.12
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()

        bg = QtGui.QLinearGradient(0, 0, rect.width(), rect.height())
        bg.setColorAt(0.0, QtGui.QColor(9, 10, 12))
        bg.setColorAt(0.55, QtGui.QColor(16, 18, 21))
        bg.setColorAt(1.0, QtGui.QColor(7, 13, 15))
        painter.fillRect(rect, bg)

        calibrating = self.values.get("calibrating", False)
        presence = self.values.get("presence_confidence", 0.0)
        motion = self.values.get("motion_energy", 0.0)
        visible = 0.2 + 0.8 * presence
        if calibrating:
            visible = 0.25 + 0.35 * self.values.get("progress", 0.0)

        center_x = rect.width() * (0.5 + math.sin(self.phase * 0.45) * motion * 0.08)
        center_y = rect.height() * (0.52 + math.cos(self.phase * 0.36) * motion * 0.05)
        base_radius = min(rect.width(), rect.height()) * (0.14 + 0.22 * visible)
        wobble = 0.08 + motion * 0.34

        painter.setPen(QtCore.Qt.NoPen)
        for layer in range(10, 0, -1):
            scale = layer / 10
            alpha = int((18 + 55 * visible) * scale)
            color = QtGui.QColor(90, 210, 205, alpha)
            if layer < 5:
                color = QtGui.QColor(235, 205, 110, alpha)
            painter.setBrush(color)
            radius = base_radius * (0.7 + scale * 0.9)
            path = self.make_blob_path(center_x, center_y, radius, wobble, layer)
            painter.drawPath(path)

        core_alpha = int(45 + 135 * visible)
        glow = QtGui.QRadialGradient(
            QtCore.QPointF(center_x, center_y),
            base_radius * (0.75 + motion),
        )
        glow.setColorAt(0.0, QtGui.QColor(245, 236, 180, core_alpha))
        glow.setColorAt(0.45, QtGui.QColor(80, 210, 205, int(core_alpha * 0.5)))
        glow.setColorAt(1.0, QtGui.QColor(80, 210, 205, 0))
        painter.setBrush(glow)
        painter.drawEllipse(
            QtCore.QPointF(center_x, center_y),
            base_radius * 1.4,
            base_radius * 1.4,
        )

        self.draw_hud(painter, rect)

    def make_blob_path(self, center_x, center_y, radius, wobble, layer):
        path = QtGui.QPainterPath()
        points = []
        count = 42
        for i in range(count):
            angle = math.tau * i / count
            n1 = math.sin(angle * 3.0 + self.phase + self.noise[i])
            n2 = math.cos(angle * 5.0 - self.phase * 0.7 + self.noise[-i])
            r = radius * (1.0 + wobble * 0.22 * n1 + wobble * 0.13 * n2)
            r *= 1.0 + 0.018 * layer * math.sin(self.phase * 0.5 + layer)
            points.append(
                QtCore.QPointF(
                    center_x + math.cos(angle) * r,
                    center_y + math.sin(angle) * r,
                )
            )

        path.moveTo(points[0])
        for i in range(count):
            current = points[i]
            nxt = points[(i + 1) % count]
            mid = QtCore.QPointF((current.x() + nxt.x()) / 2, (current.y() + nxt.y()) / 2)
            path.quadTo(current, mid)
        path.closeSubpath()
        return path

    def draw_hud(self, painter, rect):
        painter.setPen(QtGui.QColor(218, 224, 220, 220))
        font = QtGui.QFont("Menlo")
        font.setPointSize(13)
        painter.setFont(font)

        if self.values.get("calibrating", False):
            text = f"calibrating baseline {self.values.get('progress', 0.0) * 100:05.1f}%"
        else:
            text = (
                f"presence {self.values.get('presence_confidence', 0.0):0.3f}   "
                f"motion {self.values.get('motion_energy', 0.0):0.3f}   "
                f"rssi {self.values.get('rssi', 0)} dBm"
            )
        painter.drawText(28, 40, text)

        painter.setPen(QtGui.QColor(180, 188, 184, 150))
        small = QtGui.QFont("Menlo")
        small.setPointSize(10)
        painter.setFont(small)
        painter.drawText(
            28,
            rect.height() - 28,
            (
                f"{self.status}   "
                f"mean_amp {self.values.get('mean_amp', 0.0):0.2f}   "
                f"raw {self.values.get('presence_raw', 0.0):0.2f}/"
                f"{self.values.get('motion_raw', 0.0):0.2f}"
            ),
        )


def main():
    parser = argparse.ArgumentParser(description="Live CSI blob visualization")
    parser.add_argument("-p", "--port", default="/dev/cu.usbmodem2101")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--calibration-frames", type=int, default=250)
    parser.add_argument("--motion-scale", type=float, default=18.0)
    parser.add_argument("--presence-scale", type=float, default=16.0)
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    widget = BlobView()
    worker = CsiWorker(
        args.port,
        args.baud,
        args.calibration_frames,
        args.motion_scale,
        args.presence_scale,
    )
    worker.values.connect(widget.set_values)
    worker.status.connect(widget.set_status)
    app.aboutToQuit.connect(worker.stop)
    worker.start()
    widget.show()
    code = app.exec()
    worker.stop()
    worker.wait(1500)
    sys.exit(code)


if __name__ == "__main__":
    main()
