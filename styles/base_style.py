from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPointF

class BaseStyle:
    name = "Base"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        """
        Base drawing method to be overridden by each style plugin.
        """
        raise NotImplementedError("Each style plugin must implement the draw method.")