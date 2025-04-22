from PyQt5 import QtWidgets, QtCore, QtGui
import sys

# 定义常量
BACKGROUND_STYLE = "background-color: rgba(50, 50, 50, 180); border-radius: 5px; heigh: 18px"
LABEL_STYLE = "font-size: 24px; color: white; padding: 0px; margin: 0px; height: 24px;"  # 控制行高

class Clock(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口属性：无边框、置顶、透明背景
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(50, 20)  # 减小最小宽度到 20 像素
        self.resize(200, 100)
        self.resize_margin = 15  # 缩放区域 15 像素
        self.resizing = False
        self.opacity = 1.0
        self.setContentsMargins(0, 0, 0, 0)  # 消除窗口内容边距

        # 加载保存的设置
        self.settings = QtCore.QSettings("MyCompany", "MiniClock")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.setWindowOpacity(float(self.settings.value("opacity", 1.0)))

        # 设置主窗口背景
        self.setStyleSheet(BACKGROUND_STYLE)

        # 创建时间显示标签
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # 强制水平和垂直居中
        self.label.setStyleSheet(LABEL_STYLE)
        self.label.setGeometry(self.rect())
        self.label.setMouseTracking(False)  # 禁用 QLabel 鼠标跟踪
        self.label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)  # 使 QLabel 透明于鼠标事件
        self.label.setContentsMargins(0, 0, 0, 0)  # 消除内容边距

        # 创建定时器用于更新时间
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)
        self.last_time = ""
        self.updateTime()

        # 鼠标拖动相关
        self.oldPos = None

        # 创建系统托盘图标
        self.tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon.fromTheme("clock"), self)
        self.tray.setToolTip("迷你时钟")
        menu = QtWidgets.QMenu()
        menu.addAction("显示窗口").triggered.connect(self.showNormal)
        menu.addAction("退出").triggered.connect(self.quitApplication)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.trayClicked)
        self.tray.show()

    def updateTime(self):
        """仅在时间变化时更新时间显示"""
        current_time = QtCore.QTime.currentTime().toString("HH:mm:ss")
        if current_time != self.last_time:
            self.label.setText(current_time)
            self.last_time = current_time

    def updateLayout(self):
        """更新标签布局"""
        self.label.setGeometry(self.rect())

    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于拖动或调整大小"""
        if event.button() == QtCore.Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.resizing = self.isNearBottomRight(event.pos())
            print(f"鼠标位置: {event.pos()}, 缩放: {self.resizing}, 窗口大小: {self.size()}")

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，支持拖动窗口或调整大小"""
        if event.buttons() == QtCore.Qt.LeftButton and self.oldPos:
            delta = event.globalPos() - self.oldPos
            if self.resizing:
                new_width = max(self.minimumWidth(), self.width() + delta.x())
                new_height = max(self.minimumHeight(), self.height() + delta.y())
                self.resize(new_width, new_height)
                print(f"调整大小: {new_width}x{new_height}")
            else:
                self.move(self.pos() + delta)
            self.oldPos = event.globalPos()
            self.updateLayout()
        elif self.isNearBottomRight(event.pos()):
            self.setCursor(QtCore.Qt.SizeFDiagCursor)  # 右下角显示缩放光标
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)  # 其他区域恢复默认光标

    def mouseDoubleClickEvent(self, event):
        """双击窗口退出程序"""
        if event.button() == QtCore.Qt.LeftButton:
            self.quitApplication()

    def wheelEvent(self, event):
        """处理鼠标滚轮事件，调整窗口透明度"""
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            delta = event.angleDelta().y() / 1200.0
            self.opacity = min(max(0.2, self.opacity + delta), 1.0)
            self.setWindowOpacity(self.opacity)

    def isNearBottomRight(self, pos):
        """判断鼠标是否在右下角调整大小区域"""
        near = (self.width() - pos.x() < self.resize_margin) and (self.height() - pos.y() < self.resize_margin)
        return near

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.quitApplication()
        event.accept()

    def quitApplication(self):
        """清理资源并退出程序"""
        if self.timer.isActive():
            self.timer.stop()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("opacity", self.windowOpacity())
        self.tray.hide()
        self.tray.deleteLater()
        QtWidgets.qApp.quit()

    def trayClicked(self, reason):
        """处理托盘图标点击事件"""
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.isHidden():
                self.showNormal()
            else:
                self.hide()

    def showNormal(self):
        """显示窗口并置于前台"""
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    clock = Clock()
    clock.show()
    sys.exit(app.exec_())