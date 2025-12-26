import sys
import argparse
import json,os,re
from dataclasses import dataclass,field
from typing import Dict, Tuple, Optional

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFrame, QSpinBox, QMessageBox
)

# ---------------------------
# Visual config (colors)
# ---------------------------
@dataclass(frozen=True)
class CellColors:
    WALL: QColor = field(default_factory=lambda: QColor(0, 0, 0))
    EMPTY: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    FRONTIER: QColor = field(default_factory=lambda: QColor(70, 130, 180))   # steel blue
    VISITED: QColor = field(default_factory=lambda: QColor(180, 180, 180))
    CURRENT: QColor = field(default_factory=lambda: QColor(255, 215, 0))     # gold
    START: QColor = field(default_factory=lambda: QColor(50, 205, 50))       # lime green
    END: QColor = field(default_factory=lambda: QColor(220, 20, 60))         # crimson
    GRID_LINE: QColor = field(default_factory=lambda: QColor(220, 220, 220))


COL = CellColors()

# ---------------------------
# Maze model (in-memory only)
# ---------------------------
class MazeModel:
    """
    In-memory maze state for GUI rendering.
    No file I/O here.
    """
    def __init__(self):
        self.n = 10
        self.m = 10
        self.start = (0, 0)
        self.end = (9, 9)

        # wall set: {(x, y), ...}
        self.walls = set()

        # rendering states
        self.frontier = set()
        self.visited = set()
        self.current: Optional[Tuple[int, int]] = None

        self.step = 0
        self.last_op = "-"
        self.message = "Ready"

    def reset_states(self):
        self.frontier.clear()
        self.visited.clear()
        self.current = None
        self.step = 0
        self.last_op = "-"
        self.message = "Reset"

    def apply_meta(self, n: int, m: int, sx: int, sy: int, ex: int, ey: int):
        self.n, self.m = n, m
        self.start = (sx, sy)
        self.end = (ex, ey)
        #self.walls.clear()
        self.reset_states()
        self.message = f"Meta loaded: {n}x{m}, start={self.start}, end={self.end}"

    def set_wall(self, x: int, y: int, is_wall: bool = True):
        if is_wall:
            self.walls.add((x, y))
        else:
            self.walls.discard((x, y))


# ---------------------------
# Grid widget
# ---------------------------
class GridWidget(QWidget):
    def __init__(self, model: MazeModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setMinimumSize(QSize(520, 520))
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        n, m = self.model.n, self.model.m
        if n <= 0 or m <= 0:
            return

        # compute cell size
        w, h = self.width(), self.height()
        cell = int(min(w / m, h / n))
        ox = (w - cell * m) // 2
        oy = (h - cell * n) // 2

        # background
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        # draw cells
        for x in range(n):
            for y in range(m):
                rect_x = ox + y * cell
                rect_y = oy + x * cell

                pos = (x, y)
                color = COL.EMPTY
                if pos in self.model.walls:
                    color = COL.WALL
                elif pos == self.model.start:
                    color = COL.START
                elif pos == self.model.end:
                    color = COL.END
                elif self.model.current == pos:
                    color = COL.CURRENT
                elif pos in self.model.frontier:
                    color = COL.FRONTIER
                elif pos in self.model.visited:
                    color = COL.VISITED

                painter.fillRect(rect_x, rect_y, cell, cell, QBrush(color))

                # grid line
                painter.setPen(QPen(COL.GRID_LINE, 1))
                painter.drawRect(rect_x, rect_y, cell, cell)

        # draw legend text (simple)
        painter.setPen(QPen(QColor(60, 60, 60)))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 20, f"Grid: {n}x{m}")

    def mousePressEvent(self, event):
        """
        Optional: click to toggle walls (handy for quick testing).
        Not required for MVP, but useful.
        """
        if event.button() != Qt.LeftButton:
            return

        n, m = self.model.n, self.model.m
        w, h = self.width(), self.height()
        cell = int(min(w / m, h / n))
        ox = (w - cell * m) // 2
        oy = (h - cell * n) // 2

        px, py = event.x(), event.y()
        if px < ox or py < oy:
            return
        y = (px - ox) // cell
        x = (py - oy) // cell
        if not (0 <= x < n and 0 <= y < m):
            return

        pos = (x, y)
        # don't allow overwriting start/end
        if pos == self.model.start or pos == self.model.end:
            return

        if pos in self.model.walls:
            self.model.set_wall(x, y, False)
            self.model.message = f"Wall removed at {pos}"
        else:
            self.model.set_wall(x, y, True)
            self.model.message = f"Wall added at {pos}"

        self.update()
        self.parent().update_status_labels()


# ---------------------------
# Main window: player skeleton
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PP Maze Visualizer (Skeleton)")
        self.model = MazeModel()

        # Timer for playback
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

        # event stream (in-memory placeholder)
        self.events = []
        self.event_idx = 0

        self._build_ui()
        self._wire_signals()

        # For now, load a fake meta so you see something
        self.model.apply_meta(10, 10, 0, 0, 9, 9)
        self.update_status_labels()
        self.grid.update()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        # Grid
        self.grid = GridWidget(self.model, parent=self)
        root.addWidget(self.grid, stretch=1)

        # Controls panel
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel_layout = QHBoxLayout(panel)

        self.btn_play = QPushButton("Play")
        self.btn_pause = QPushButton("Pause")
        self.btn_step = QPushButton("Step")
        self.btn_reset = QPushButton("Reset")

        panel_layout.addWidget(self.btn_play)
        panel_layout.addWidget(self.btn_pause)
        panel_layout.addWidget(self.btn_step)
        panel_layout.addWidget(self.btn_reset)

        panel_layout.addSpacing(20)

        panel_layout.addWidget(QLabel("Speed(ms):"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(80)
        self.speed_slider.setFixedWidth(180)
        panel_layout.addWidget(self.speed_slider)

        self.speed_value = QLabel("80")
        self.speed_value.setFixedWidth(40)
        panel_layout.addWidget(self.speed_value)

        panel_layout.addSpacing(20)

        # Optional: step-per-tick (for fast playback)
        panel_layout.addWidget(QLabel("Batch:"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setMinimum(1)
        self.batch_spin.setMaximum(50)
        self.batch_spin.setValue(1)
        self.batch_spin.setFixedWidth(60)
        panel_layout.addWidget(self.batch_spin)

        panel_layout.addStretch(1)
        root.addWidget(panel, stretch=0)

        # Status bar area
        status = QFrame()
        status.setFrameShape(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status)

        self.lbl_step = QLabel("step: 0")
        self.lbl_op = QLabel("op: -")
        self.lbl_msg = QLabel("Ready")

        status_layout.addWidget(self.lbl_step)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_op)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.lbl_msg, stretch=1)

        root.addWidget(status, stretch=0)

        self.setCentralWidget(central)
        self.resize(820, 860)

    def _wire_signals(self):
        self.btn_play.clicked.connect(self.play)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_step.clicked.connect(self.step_once)
        self.btn_reset.clicked.connect(self.reset)

        self.speed_slider.valueChanged.connect(self.on_speed_change)

    # ---------------------------
    # Playback controls
    # ---------------------------
    def play(self):
        interval = self.speed_slider.value()
        self.timer.start(interval)
        self.model.message = "Playing"
        self.update_status_labels()

    def pause(self):
        self.timer.stop()
        self.model.message = "Paused"
        self.update_status_labels()

    def reset(self):
        self.timer.stop()
        self.model.reset_states()
        self.event_idx = 0
        self.model.message = "Reset (no file loaded)"
        self.update_status_labels()
        self.grid.update()

    def step_once(self):
        self.timer.stop()
        self.consume_events(batch=self.batch_spin.value())
        self.grid.update()
        self.update_status_labels()

    def on_tick(self):
        self.consume_events(batch=self.batch_spin.value())
        self.grid.update()
        self.update_status_labels()

    def on_speed_change(self, v: int):
        self.speed_value.setText(str(v))
        if self.timer.isActive():
            self.timer.start(v)

    # ---------------------------
    # Event handling (core hook)
    # ---------------------------
    def consume_events(self, batch: int = 1):
        """
        Later: if you load JSONL -> self.events becomes a list[dict].
        Now: if no events, we just do nothing.
        """
        if not self.events:
            # For skeleton demo, you can optionally generate fake events here.
            self.model.message = "No events loaded yet"
            return

        for _ in range(batch):
            if self.event_idx >= len(self.events):
                self.timer.stop()
                self.model.last_op = "EOF"
                self.model.message = "Reached end of event stream"
                break

            ev = self.events[self.event_idx]
            self.event_idx += 1
            self.apply_event(ev)

    def apply_event(self, ev: Dict):
        """
        Event protocol hook.
        Expected keys based on your design:
        - op: meta / set_current / visited_add / frontier_add / found / done
        - t, x, y, dist, (and meta fields: n, m, sx, sy, ex, ey)
        """
        op = ev.get("op", "")
        self.model.last_op = op
        self.model.step = ev.get("t", self.model.step)

        if op == "meta":
            self.model.apply_meta(
                ev.get("n", self.model.n),
                ev.get("m", self.model.m),
                ev.get("sx", self.model.start[0]),
                ev.get("sy", self.model.start[1]),
                ev.get("ex", self.model.end[0]),
                ev.get("ey", self.model.end[1]),
            )

        elif op == "set_current":
            x, y = ev.get("x"), ev.get("y")
            if x is not None and y is not None:
                self.model.current = (x, y)
                self.model.message = f"Current = {(x, y)}"

        elif op == "visited_add":
            x, y = ev.get("x"), ev.get("y")
            if x is not None and y is not None:
                self.model.visited.add((x, y))
                self.model.frontier.discard((x, y))
                self.model.message = f"Visited add {(x, y)}"

        elif op == "frontier_add":
            x, y = ev.get("x"), ev.get("y")
            if x is not None and y is not None:
                self.model.frontier.add((x, y))
                self.model.message = f"Frontier add {(x, y)}"
                
        elif op in ("wall", "set_wall"):
            x, y = ev.get("x"), ev.get("y")
            is_wall = ev.get("is_wall", True)
            if x is not None and y is not None:
                if is_wall:
                    self.model.walls.add((x, y))
                else:
                    self.model.walls.discard((x, y))
                self.model.message = f"Wall {'add' if is_wall else 'remove'} {(x, y)}"

        elif op == "walls":
            # 支持一次性传一堆墙： {"op":"walls","cells":[[x,y],...]}
            cells = ev.get("cells", [])
            cnt = 0
            for c in cells:
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    self.model.walls.add((int(c[0]), int(c[1])))
                    cnt += 1
                elif isinstance(c, dict) and "x" in c and "y" in c:
                    self.model.walls.add((int(c["x"]), int(c["y"])))
                    cnt += 1
            self.model.message = f"Walls loaded: {cnt}"

        elif op in ("frontier_remove", "frontier_pop"):
            x, y = ev.get("x"), ev.get("y")
            if x is not None and y is not None:
                self.model.frontier.discard((x, y))
                self.model.message = f"Frontier remove {(x, y)}"

        elif op == "path":
            # 最终路径： {"op":"path","cells":[[x,y],...]}
            # 这里先把 path 画成 visited（简单 MVP）。你也可以单独加一个 self.model.path 来上色。
            cells = ev.get("cells", [])
            for c in cells:
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    self.model.visited.add((int(c[0]), int(c[1])))
            self.model.message = f"Path cells: {len(cells)}"

        elif op == "found":
            x, y = ev.get("x"), ev.get("y")
            self.model.current = (x, y) if x is not None and y is not None else self.model.current
            self.model.message = "Found end!"

        elif op == "done":
            self.timer.stop()
            self.model.message = "Done"
        else:
            self.model.message = f"Unknown op: {op}"

    def update_status_labels(self):
        self.lbl_step.setText(f"step: {self.model.step}")
        self.lbl_op.setText(f"op: {self.model.last_op}")
        self.lbl_msg.setText(self.model.message)

    # ---------------------------
    # Later: loading API (placeholder)
    # ---------------------------
    
    def load_maze_txt(self, maze_path: str):
        n, m, walls, s, e = self.load_walls_from_txt(maze_path)

        self.model.walls = walls

        # 如果 txt 里有 4/3，就用它覆盖（这样绿/红格就和 txt 一致）
        if s is not None:
            self.model.start = s
        if e is not None:
            self.model.end = e
    
    def load_events_from_jsonl(self, path: str):
        if not path:
            QMessageBox.warning(self, "No file", "Empty --events path.")
            return

        if not os.path.exists(path):
            QMessageBox.critical(self, "Not found", f"File does not exist:\n{path}")
            return

        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for ln, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise ValueError(f"JSON decode error at line {ln}: {e}\nLine={line[:200]}") from e
        except Exception as e:
            QMessageBox.critical(self, "Load failed", str(e))
            return

        self.timer.stop()
        self.events = events
        self.event_idx = 0

        # 清空当前状态
        self.model.reset_states()
        #self.model.walls.clear()

        # 预处理：把 meta + 墙体类事件先应用掉，这样一加载就能看到正确迷宫
        while self.event_idx < len(self.events):
            op = self.events[self.event_idx].get("op", "")
            if op in ("meta", "wall", "set_wall", "walls"):
                self.apply_event(self.events[self.event_idx])
                self.event_idx += 1
                continue
            break

        self.model.message = f"Loaded {len(self.events)} events from {path}"
        self.update_status_labels()
        self.grid.update()

    @staticmethod
    def load_walls_from_txt(path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw_lines = [ln.strip() for ln in f if ln.strip()]

        if not raw_lines:
            raise ValueError(f"Empty maze file: {path}")

        # 读第一行 n m
        header = [int(x) for x in re.findall(r"-?\d+", raw_lines[0])]
        if len(header) < 2:
            raise ValueError(f"First line must contain n m, got: {raw_lines[0]!r}")
        n, m = header[0], header[1]

        if len(raw_lines) < 1 + n:
            raise ValueError(f"Expected {n} rows after header, but got {len(raw_lines)-1}")

        walls = set()
        start = None
        end = None

        for x in range(n):
            nums = [int(x) for x in re.findall(r"-?\d+", raw_lines[1 + x])]
            if len(nums) != m:
                raise ValueError(f"Row {x} length {len(nums)} != {m}. Line={raw_lines[1+x]!r}")

            for y, v in enumerate(nums):
                if v == 1:
                    walls.add((x, y))
                elif v == 4:
                    start = (x, y)
                elif v == 3:
                    end = (x, y)
                # 0 以及其他值默认当空地

        return n, m, walls, start, end


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=str, default="")
    parser.add_argument("--maze", type=str, default="")
    args = parser.parse_args()
    print("Events path =", args.events)
    print("Maze path   =", args.maze)
    
    app = QApplication(sys.argv)
    w = MainWindow()
    
    if args.maze:
        w.load_maze_txt(args.maze)
    if args.events:
        w.load_events_from_jsonl(args.events)

    w.show()
    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
    

