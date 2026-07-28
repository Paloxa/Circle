from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPointF

class BaseStyle:
    name = "Base"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        """
        Метод отрисовки, который вызывается из paintEvent приложения.
        """
        raise NotImplementedError("Каждый стиль должен реализовывать метод draw")