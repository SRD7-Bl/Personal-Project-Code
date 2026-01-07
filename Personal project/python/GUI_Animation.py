import sys
import argparse
import json,os,re
from dataclasses import dataclass,field
from typing import Dict, Tuple, Optional

from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QSignalBlocker, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFrame, QSpinBox, QMessageBox, QSplitter
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
    ORANGE: QColor = field(default_factory=lambda: QColor(255, 165, 0, 160))


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
        
        self.cur_path = []   # list[(x,y)]
        self.cur_path_set = set()
        
        self.parent = {}            # (x,y) -> (px,py)
        self.best_path = []         # list[(x,y)]
        self.best_path_set = set()

    def reset_states(self):
        # reset rendering/search state
        self.frontier = set()
        self.visited = set()
        self.current = None

        # reset path reconstruction state (clears orange path too)
        self.parent = {}
        self.best_path = []
        self.best_path_set = set()

        # reset DFS live-stack path (if used)
        self.cur_path = []
        self.cur_path_set = set()

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
    def __init__(self, model: MazeModel, parent=None, editable_walls: bool = False):
        super().__init__(parent)
        self.model = model
        self.editable_walls = editable_walls
        self.setMinimumSize(QSize(260, 260))
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
        
        if self.model.best_path_set:
            for (x, y) in self.model.best_path_set:
                if (x, y) == self.model.start or (x, y) == self.model.end:
                    continue
                rect = QRect(ox + y*cell, oy + x*cell, cell, cell)
                painter.fillRect(rect, COL.ORANGE)

        # draw legend text (simple)
        painter.setPen(QPen(QColor(60, 60, 60)))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 20, f"Grid: {n}x{m}")

    def mousePressEvent(self, event):
        """
        Optional: click to toggle walls (handy for quick testing).
        Not required for MVP, but useful.
        """
        if not self.editable_walls:
            return
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
        self.status_changed.emit()

# ---------------------------
# Main window: player skeleton
# ---------------------------
class PlayerPane(QWidget):
    def __init__(self, title:str, parent = None, editable_walls = False):
        super().__init__(parent)
        self.title = title

        self.model = MazeModel()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

        self.events = []
        self.event_idx = 0

        self._build_ui(editable_walls)
        self._wire_signals()

    def _build_ui(self, editable_walls: bool):
        root = QVBoxLayout(self)

        self.lbl_title = QLabel(self.title)
        root.addWidget(self.lbl_title)

        self.grid = GridWidget(self.model, parent=self, editable_walls=editable_walls)
        root.addWidget(self.grid, stretch=1)

        # Controls panel
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel_layout = QHBoxLayout(panel)

        self.btn_play = QPushButton("Play")
        self.btn_play.setVisible(False)
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setVisible(False)
        self.btn_step = QPushButton("Step")
        self.btn_step.setVisible(False)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setVisible(False)

        panel_layout.addWidget(self.btn_play)
        panel_layout.addWidget(self.btn_pause)
        panel_layout.addWidget(self.btn_step)
        panel_layout.addWidget(self.btn_reset)

        panel_layout.addSpacing(20)

        #panel_layout.addWidget(QLabel("Speed(ms):"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setVisible(False)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(80)
        self.speed_slider.setFixedWidth(180)
        panel_layout.addWidget(self.speed_slider)

        self.speed_value = QLabel("80")
        self.speed_value.setVisible(False)
        self.speed_value.setFixedWidth(40)
        panel_layout.addWidget(self.speed_value)

        panel_layout.addSpacing(20)

        # Optional: step-per-tick (for fast playback)
        #panel_layout.addWidget(QLabel("Batch:"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setVisible(False)
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

        #self.setCentralWidget(central)
        #self.resize(820, 860)
        
        #self.grid.status_changed.connect(self.update_status_labels)

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
            
        if op == "done":
            self.timer.stop()
            self.model.message = "Done"
            return

        # DFS: explicit best-path stream
        if op == "best_clear":
            self.model.best_path = []
            self.model.best_path_set = set()
            self.model.message = "Best path cleared"
            return
            
        x = ev.get("x",None)
        y = ev.get("y",None)
        if x is None or y is None:
            return
            
        pos = (x, y)
        px = ev.get("px", None)
        py = ev.get("py", None)
        if px is not None and py is not None and px >= 0 and py >= 0:
            self.model.parent[pos] = (px, py)

        if op == "best_add":
            # DFS best-path stream
            self.model.best_path.append(pos)
            self.model.best_path_set.add(pos)
            self.model.message = f"Best path add {pos}"
            return
            
        if op in ("frontier_add", "relax"):
            # A*: relax == (re)insert/update in open-set; show it as frontier
            self.model.frontier.add(pos)
            px = ev.get("px"); py = ev.get("py")
            if px is not None and py is not None and px >= 0 and py >= 0:
                self.model.parent[pos] = (px, py)
        
        elif op == "set_current":
            self.model.current = (x, y)
            # popped from frontier
            self.model.frontier.discard(pos)
            # BFS/A*: reconstruct best path from parent chain
            # (DFS uses best_clear/best_add; its parent map is empty.)
            if self.model.parent:
                self.rebuild_best_path(pos)
            self.model.message = f"Current = {(x, y)}"
                
        elif op == "path_push":
            self.model.cur_path.append(pos)
            self.model.cur_path_set.add(pos)

        elif op == "path_pop":
            # 理论上 pop 的就是栈顶；保险起见按 pos 移除也行
            if self.model.cur_path and self.model.cur_path[-1] == pos:
                self.model.cur_path.pop()
                self.model.cur_path_set.discard(pos)
            else:
                # fallback：乱序也能删
                if pos in self.model.cur_path_set:
                    self.model.cur_path_set.remove(pos)
                    self.model.cur_path = [p for p in self.model.cur_path if p != pos]

        elif op == "best_add":
            # DFS best path cell
            self.model.best_path.append(pos)
            self.model.best_path_set.add(pos)
            self.model.message = f"Best add {pos}"
        

        elif op == "visited_add":
            self.model.visited.add((x, y))
            self.model.frontier.discard((x, y))
            self.model.message = f"Visited add {(x, y)}"

        elif op == "frontier_add":
            self.model.frontier.add((x, y))
            self.model.message = f"Frontier add {(x, y)}"
                
        elif op in ("wall", "set_wall"):
            is_wall = ev.get("is_wall", True)
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
            self.model.current = (x, y) if x is not None and y is not None else self.model.current
            # Ensure final shortest path is shown for BFS/A*
            if self.model.parent:
                self.rebuild_best_path(pos)
            self.model.message = "Found end!"

            
        

    def update_status_labels(self):
        self.lbl_step.setText(f"step: {self.model.step}")
        self.lbl_op.setText(f"op: {self.model.last_op}")
        self.lbl_msg.setText(self.model.message)
        
    def rebuild_best_path(self, end_pos):
        start = self.model.start
        parent = self.model.parent

        path = []
        cur = end_pos
        seen = set()  # 防止 parent 链出环导致死循环

        while cur is not None and cur not in seen:
            seen.add(cur)
            path.append(cur)
            if cur == start:
                break
            cur = parent.get(cur, None)

        if not path or path[-1] != start:
            # 说明 parent 链还不完整（比如 current 还没被 parent 记录）
            self.model.best_path = []
            self.model.best_path_set = set()
            return

        path.reverse()
        self.model.best_path = path
        self.model.best_path_set = set(path)


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
        
    def set_speed_ms(self, ms: int):
        ms = max(1, int(ms))
        # 如果你保留了 speed_slider，就同步 UI；如果之后要隐藏本地控件，也没问题
        if hasattr(self, "speed_slider"):
            with QSignalBlocker(self.speed_slider):
                self.speed_slider.setValue(ms)
        self.timer.setInterval(ms)
        self.update_status_labels()

    def set_batch(self, k: int):
        k = max(1, int(k))
        if hasattr(self, "batch_spin"):
            with QSignalBlocker(self.batch_spin):
                self.batch_spin.setValue(k)
        self.update_status_labels()

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

class CompareWindow(QMainWindow):
    def __init__(self, panes: list[tuple[str, str]], maze_path: str = ""):
        super().__init__()
        self.setWindowTitle("PP Maze Visualizer - Compare Mode")

        central = QWidget()
        root = QVBoxLayout(central)
        
        ctrl = QWidget()
        ctrl_layout = QHBoxLayout(ctrl)

        btn_play  = QPushButton("Play All")
        btn_pause = QPushButton("Pause All")
        btn_step  = QPushButton("Step All")
        btn_reset = QPushButton("Reset All")

        ctrl_layout.addWidget(btn_play)
        ctrl_layout.addWidget(btn_pause)
        ctrl_layout.addWidget(btn_step)
        ctrl_layout.addWidget(btn_reset)

        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(QLabel("Speed(ms):"))
        speed = QSlider(Qt.Horizontal)
        speed.setMinimum(10)
        speed.setMaximum(500)
        speed.setValue(80)
        speed.setFixedWidth(200)
        ctrl_layout.addWidget(speed)

        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(QLabel("Batch:"))
        batch = QSpinBox()
        batch.setMinimum(1)
        batch.setMaximum(50)
        batch.setValue(1)
        ctrl_layout.addWidget(batch)

        root.addWidget(ctrl, stretch=0)      # 放在 splitter 上面
        
        self.splitter = QSplitter(Qt.Horizontal)
        root.addWidget(self.splitter, stretch=1)
        
        btn_play.clicked.connect(lambda:  self._foreach_pane(lambda p: p.play()))
        btn_pause.clicked.connect(lambda: self._foreach_pane(lambda p: p.pause()))
        btn_step.clicked.connect(lambda:  self._foreach_pane(lambda p: p.step_once()))
        btn_reset.clicked.connect(lambda: self._foreach_pane(lambda p: p.reset()))

        speed.valueChanged.connect(lambda v: self._foreach_pane(lambda p: p.set_speed_ms(v)))
        batch.valueChanged.connect(lambda v: self._foreach_pane(lambda p: p.set_batch(v)))


        self.setCentralWidget(central)

        # 可选：先读一次 maze，然后给每个 pane 复用同一份墙体/起终点
        self.maze_path = maze_path

        self.panes: list[PlayerPane] = []
        for title, events_path in panes:
            self.add_pane(title, events_path)

    def add_pane(self, title: str, events_path: str):
        pane = PlayerPane(title=title, editable_walls=False)

        if self.maze_path:
            pane.load_maze_txt(self.maze_path)

        if events_path:
            pane.load_events_from_jsonl(events_path)

        self.panes.append(pane)
        self.splitter.addWidget(pane)
        
    def _foreach_pane(self, fn):
        for p in self.panes:
            fn(p)



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=str, default="")
    parser.add_argument("--maze", type=str, default="")
    parser.add_argument("--pane",action="append",default=[],help='repeatable: "Title:path/to/events.jsonl"')
    args = parser.parse_args()
    
    print("Events path =", args.events)
    print("Maze path   =", args.maze)
    
    panes=[]
    for item in args.pane:
        if ":" in item:
            title,path = item.split(":",1)
        else:
            title,path = item,""
        panes.append((title.strip(),path.strip()))
    
    app = QApplication(sys.argv)
    if len(panes) <= 1:
        # 单栏模式：你可以继续用原来的 MainWindow，或者也用 CompareWindow 但只放一个 pane
        w = CompareWindow(panes=panes or [("Single", args.events if hasattr(args, "events") else "")],
                          maze_path=args.maze)
    else:
        w = CompareWindow(panes=panes, maze_path=args.maze)

    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    

