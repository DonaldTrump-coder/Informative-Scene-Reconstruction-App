from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QPixmap
import cv2

class GLWidget(QOpenGLWidget):
    def __init__(self, parent, mainwindow):
        super().__init__(parent=parent)
        self.image = None
        self.texture_id = None
        self.main_window = mainwindow

    def initialize(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)  # 背景色
        glEnable(GL_TEXTURE_2D)
    
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def set_image(self, img:np.ndarray):
        self.image = img
        self.update()

    def paintGL(self):
        self.makeCurrent()  # 确保当前上下文
        painter = QPainter(self)
        # 背景填充黑色
        painter.fillRect(0, 0, self.width(), self.height(), 0x000000)
        if self.image is None:
            return
        # 转为 QImage，RGB 顺序
        #img = np.transpose(self.image, (1, 2, 0))  # 转为 (H,W,C)

        img = np.ascontiguousarray(self.image.astype(np.uint8))
        if img.shape[2] == 4:  # 如果图像是 RGBA 格式
            img = img[..., :3]  # 只保留 RGB 通道
        elif img.shape[2] == 3:  # 如果图像是 RGB 格式
            pass
        h, w, c = img.shape
        qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)

        # 计算居中显示位置
        scale = min(self.width() / w, self.height() / h)
        disp_w = int(w * scale)
        disp_h = int(h * scale)
        x0 = (self.width() - disp_w) // 2
        y0 = (self.height() - disp_h) // 2

        #painter.drawImage(x0, y0, qimg.scaled(disp_w, disp_h))

        pixmap = QPixmap.fromImage(qimg)
        painter.drawPixmap(x0, y0, disp_w, disp_h, pixmap)
        painter.end()

    def mousePressEvent(self, event):
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.main_window.renderthread.move_right()
        if event.key() == Qt.Key_W:
            self.main_window.renderthread.move_forward()
        if event.key() == Qt.Key_S:
            self.main_window.renderthread.move_back()
        if event.key() == Qt.Key_A:
            self.main_window.renderthread.move_left()