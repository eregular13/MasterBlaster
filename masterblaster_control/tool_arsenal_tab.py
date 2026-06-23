"""Tool Arsenal tab — dozens of Kali tools with one-click Unleash presets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .engagement_picker import resolve_engagement
from .kali_tool_wrappers import KALI_TOOL_REGISTRY, list_tools, tool_arsenal_markdown, unleash_tool
from .runner_simulator import RunnerSimulator


class ToolArsenalTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "<b>⚔ KALI TOOL ARSENAL</b><br>"
                "Every blade routed through its MCP governor — scoped, approved, evidence-captured. "
                "Select a tool, pick a preset, unleash."
            )
        )

        controls = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "")
        for category in sorted({tool.category for tool in KALI_TOOL_REGISTRY.values()}):
            self.category_combo.addItem(category, category)
        self.category_combo.currentIndexChanged.connect(self._rebuild_grid)
        controls.addWidget(QLabel("Filter:"))
        controls.addWidget(self.category_combo)

        self.unleash_all_btn = QPushButton("UNLEASH ENTIRE ARSENAL")
        self.unleash_all_btn.setStyleSheet(
            "background: #8b0000; color: #ffd700; font-weight: bold; padding: 8px 16px;"
        )
        self.unleash_all_btn.clicked.connect(self._unleash_all_visible)
        controls.addWidget(self.unleash_all_btn)
        root.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.grid_layout.setSpacing(8)
        scroll.setWidget(self.grid_host)
        root.addWidget(scroll, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(160)
        root.addWidget(QLabel("Strike Log"))
        root.addWidget(self.output)

        self._rebuild_grid()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        category = self.category_combo.currentData()
        tools = list_tools(category=category or None)
        for index, tool in enumerate(tools):
            box = QGroupBox(f"{tool.display_name} [{tool.danger_level}]")
            box.setStyleSheet("QGroupBox { border: 1px solid #8b0000; margin-top: 8px; }")
            lay = QVBoxLayout(box)
            lay.addWidget(QLabel(f"<code>{tool.binary}</code> → <code>{tool.mcp_adapter_id}</code>"))

            preset_combo = QComboBox()
            for preset in tool.presets:
                preset_combo.addItem(f"{preset.label} — {preset.flags}", preset.preset_id)
            lay.addWidget(preset_combo)

            row = QHBoxLayout()
            unleash_btn = QPushButton("UNLEASH")
            unleash_btn.setStyleSheet("background: #5a0000; color: #ffcccc; font-weight: bold;")
            unleash_btn.clicked.connect(
                lambda _checked=False, tid=tool.tool_id, combo=preset_combo: self._unleash_one(tid, combo)
            )
            row.addWidget(unleash_btn)
            lay.addLayout(row)

            self.grid_layout.addWidget(box, index // 3, index % 3)

    def _target(self) -> str:
        return getattr(self.main, "global_target", "") or "example.com"

    def _runner(self) -> RunnerSimulator:
        return getattr(self.main, "runner", RunnerSimulator())

    def _engagement(self, target: str):
        return resolve_engagement(
            self.main.storage,
            getattr(self.main, "selected_engagement_id", "") or None,
            target,
        )

    def _log_strike(self, message: str):
        self.output.append(message)
        if hasattr(self.main, "log_message"):
            self.main.log_message(message)
        if hasattr(self.main, "increment_strike_counter"):
            self.main.increment_strike_counter()

    def _unleash_one(self, tool_id: str, preset_combo: QComboBox):
        target = self._target()
        preset_id = preset_combo.currentData()
        result = unleash_tool(self._runner(), self._engagement(target), target, tool_id, preset_id=preset_id)
        self._log_strike(
            f"[UNLEASH] {result.display_name} ({preset_id}) → {result.status} "
            f"via {result.mcp_adapter_id} | `{result.command}`"
        )
        if result.status == "completed" and hasattr(self.main, "flash_strike_success"):
            self.main.flash_strike_success(result.display_name)

    def _unleash_all_visible(self):
        category = self.category_combo.currentData()
        tools = list_tools(category=category or None)
        target = self._target()
        engagement = self._engagement(target)
        runner = self._runner()
        self.output.append(f"=== Unleashing {len(tools)} tools against {target} ===")
        for tool in tools:
            preset_id = tool.presets[0].preset_id if tool.presets else None
            result = unleash_tool(runner, engagement, target, tool.tool_id, preset_id=preset_id)
            self._log_strike(f"[BARRAGE] {result.display_name} → {result.status}")
        self.output.append(tool_arsenal_markdown())
        if hasattr(self.main, "flash_strike_success"):
            self.main.flash_strike_success("ARSENAL BARRAGE")