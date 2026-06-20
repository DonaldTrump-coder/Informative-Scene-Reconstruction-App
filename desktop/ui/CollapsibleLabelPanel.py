from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QPushButton, QMenu, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt

from PyQt5.QtGui import QIcon

class CollapsibleLabelPanel(QWidget):
    navigate_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = True
        self.setMinimumWidth(24)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(6)
        
        title = QLabel("场景标注")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        content_layout.addWidget(title)
        
        self.label_list = QListWidget()
        self.label_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label_list.customContextMenuRequested.connect(self._on_context_menu)
        content_layout.addWidget(self.label_list)
        layout.addWidget(self.content)
        
        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setFixedWidth(22)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle)
        self.toggle_btn.setStyleSheet(
            "QPushButton { background: #e0e5ec; border: none; "
            "border-radius: 4px; font-size: 12px; color: #5a5f7a; } "
            "QPushButton:hover { background: #d0d5dc; }"
        )
        layout.addWidget(self.toggle_btn)
        self.setFixedWidth(220)
        
    def _toggle(self):
        if self._expanded:
            self.content.hide()
            self.toggle_btn.setText("▶")
            self.setFixedWidth(28)
        else:
            self.content.show()
            self.toggle_btn.setText("◀")
            self.setFixedWidth(220)
        self._expanded = not self._expanded
        
    def _on_context_menu(self, pos):
        item = self.label_list.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        nav_action = menu.addAction("导航到此标注")
        action = menu.exec_(self.label_list.mapToGlobal(pos))
        if action == nav_action:
            index = item.data(Qt.UserRole)
            self.navigate_requested.emit(index)
            
    def update_labels(self, labels):
        self.label_list.clear()
        for index, label in enumerate(labels):
            item = QListWidgetItem(f"[{index}] {label.name}")
            item.setData(Qt.UserRole, index)
            self.label_list.addItem(item)