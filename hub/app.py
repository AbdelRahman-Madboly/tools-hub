"""Tools Hub window: one card per tool with its status, and buttons to open it, its folder and its backlog."""
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from . import collect, registry
from .registry import Registry, Tool
from .status import Status

COLUMNS = 3
LEVEL_COLOUR = {"ok": "#34d399", "warn": "#fbbf24", "fail": "#f87171", "off": "#94a3b8",
                "stale": "#a78bfa", "unknown": "#64748b"}

STYLE = """
QMainWindow, QScrollArea, QWidget#body { background: #12141c; }
QLabel { color: #e5e7eb; font-size: 13px; }
QLabel[role="title"] { font-size: 22px; font-weight: 700; }
QLabel[role="group"] { font-size: 15px; font-weight: 700; color: #c4b5fd; margin-top: 8px; }
QLabel[role="name"] { font-size: 16px; font-weight: 700; }
QLabel[role="muted"] { color: #9ca3af; font-size: 12px; }
QFrame[card="true"] { background: #1b1e2a; border: 1px solid #2a2f3f; border-radius: 12px; }
QPushButton { background: #262b3b; color: #e5e7eb; border: 1px solid #343a4f; border-radius: 7px;
              padding: 5px 12px; }
QPushButton:hover { background: #313852; }
QPushButton[primary="true"] { background: #6366f1; border-color: #6366f1; }
"""


def _label(text: str, role: str = "", wrap: bool = False) -> QLabel:
    lab = QLabel(text)
    if role:
        lab.setProperty("role", role)
    lab.setWordWrap(wrap)
    return lab


class ToolCard(QFrame):
    def __init__(self, tool: Tool, icon: Path, open_fn, folder_fn, backlog_fn):
        super().__init__()
        self.setProperty("card", True)
        self.tool = tool
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(12)
        pic = QLabel()
        if icon.exists():
            pic.setPixmap(QPixmap(str(icon)).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        pic.setFixedSize(56, 56)
        top.addWidget(pic, 0, Qt.AlignTop)
        names = QVBoxLayout()
        names.setSpacing(2)
        names.addWidget(_label(tool.name, "name"))
        names.addWidget(_label(tool.what, "muted", wrap=True))
        top.addLayout(names, 1)
        lay.addLayout(top)
        row = QHBoxLayout()
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        row.addWidget(self.dot, 0, Qt.AlignVCenter)
        self.headline = _label("Checking…", wrap=True)
        row.addWidget(self.headline, 1)
        lay.addLayout(row)
        self.details = _label("", "muted", wrap=True)
        lay.addWidget(self.details)
        lay.addStretch(1)
        buttons = QHBoxLayout()
        self.btn_open = QPushButton("Open")
        self.btn_open.setProperty("primary", True)
        self.btn_folder = QPushButton("Folder")
        self.btn_backlog = QPushButton("Backlog")
        self.btn_open.clicked.connect(lambda: open_fn(tool))
        self.btn_folder.clicked.connect(lambda: folder_fn(tool))
        self.btn_backlog.clicked.connect(lambda: backlog_fn(tool))
        for b in (self.btn_open, self.btn_folder, self.btn_backlog):
            buttons.addWidget(b)
        buttons.addStretch(1)
        lay.addLayout(buttons)

    def set_status(self, s: Status) -> None:
        self.dot.setStyleSheet(f"background: {LEVEL_COLOUR.get(s.level, '#64748b')}; border-radius: 5px;")
        self.headline.setText(s.headline)
        self.details.setText("\n".join(s.details))


class _Signals(QObject):
    done = Signal(object)


class _Collect(QRunnable):
    def __init__(self, reg: Registry):
        super().__init__()
        self.reg, self.signals = reg, _Signals()
        self.setAutoDelete(False)

    def run(self):
        self.signals.done.emit(collect.every(self.reg))


class HubWindow(QMainWindow):
    def __init__(self, reg: Registry, root: Path, launcher=None):
        super().__init__()
        self.reg, self.root = reg, Path(root)
        self.launch = launcher or (lambda argv: subprocess.Popen(argv, start_new_session=True,
                                                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.setWindowTitle("Tools Hub")
        self.setStyleSheet(STYLE)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("body")
        scroll.setWidget(body)
        self.setCentralWidget(scroll)
        root_lay = QVBoxLayout(body)
        root_lay.setContentsMargins(24, 18, 24, 24)
        root_lay.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(_label("Tools Hub", "title"))
        head.addStretch(1)
        self.updated = _label("", "muted")
        head.addWidget(self.updated)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        head.addWidget(self.btn_refresh)
        btn_md = QPushButton("TOOLS.md")
        btn_md.clicked.connect(lambda: self.launch(["xdg-open", str(self.root.parent / "TOOLS.md")]))
        head.addWidget(btn_md)
        root_lay.addLayout(head)
        self.cards: dict[str, ToolCard] = {}
        for group in dict.fromkeys(t.group for t in reg.tools):
            root_lay.addWidget(_label(group, "group"))
            grid = QGridLayout()
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(14)
            tools = [t for t in reg.tools if t.group == group]
            for i, t in enumerate(tools):
                card = ToolCard(t, self.root / "assets" / "icons" / f"{t.id}.png",
                                self.open_tool, self.open_folder, self.open_backlog)
                self.cards[t.id] = card
                grid.addWidget(card, i // COLUMNS, i % COLUMNS)
            for c in range(COLUMNS):
                grid.setColumnStretch(c, 1)
            root_lay.addLayout(grid)
        root_lay.addStretch(1)
        self._job = None
        self.timer = QTimer(self)
        self.timer.setInterval(10 * 60 * 1000)
        self.timer.timeout.connect(self.refresh)

    def start(self) -> None:
        """Checks run in the background: now, then every 10 minutes."""
        registry.write_tools_md(self.reg, self.root.parent / "TOOLS.md", self.root / "backlogs")
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        if self._job is not None:
            return
        self.btn_refresh.setEnabled(False)
        self._job = _Collect(self.reg)
        self._job.signals.done.connect(self._collected)
        QThreadPool.globalInstance().start(self._job)

    def _collected(self, statuses) -> None:
        self._job = None
        self.btn_refresh.setEnabled(True)
        self.show_statuses(statuses)

    def show_statuses(self, statuses: dict[str, Status]) -> None:
        for tool_id, s in statuses.items():
            if tool_id in self.cards:
                self.cards[tool_id].set_status(s)
        self.updated.setText(f"Updated {datetime.now():%H:%M}")

    def open_tool(self, tool: Tool) -> None:
        self.launch(tool.open)

    def open_folder(self, tool: Tool) -> None:
        self.launch(["xdg-open", str(tool.path)])

    def open_backlog(self, tool: Tool) -> None:
        self.launch(["xdg-open", str(self.root / "backlogs" / f"{tool.id}.md")])


def window_icon(root: Path) -> QIcon:
    return QIcon(str(Path(root) / "assets" / "icons" / "tools-hub.png"))
