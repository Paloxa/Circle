import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import QPointF, Qt
from styles.base_style import BaseStyle

class ClassicStyle(BaseStyle):
    name = "Classic"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        if num_items == 0:
            return

        current_inner = widget.radius_inner * max(0.01, center_scale)
        current_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        angle_per_item = 360 / num_items
        gap = 3

        if sector_progress > 0.05:
            for i, app_info in enumerate(widget.apps):
                name = app_info.get("name", "")
                start_angle = i * angle_per_item - 90 + (gap / 2)
                sweep_angle = angle_per_item - gap

                path = QPainterPath()
                path.arcMoveTo(
                    center.x() - current_outer, center.y() - current_outer,
                    current_outer * 2, current_outer * 2, -start_angle
                )
                path.arcTo(
                    center.x() - current_outer, center.y() - current_outer,
                    current_outer * 2, current_outer * 2, -start_angle, -sweep_angle
                )
                path.arcTo(
                    center.x() - current_inner, center.y() - current_inner,
                    current_inner * 2, current_inner * 2, -start_angle - sweep_angle, sweep_angle
                )
                path.closeSubpath()

                if i == hovered_index and sector_progress >= 0.9:
                    fill_color = QColor(0, 103, 192, int(220 * sector_progress))
                    border_color = QColor(255, 255, 255, int(140 * sector_progress))
                else:
                    fill_color = QColor(32, 32, 32, int(190 * sector_progress))
                    border_color = QColor(255, 255, 255, int(35 * sector_progress))

                painter.setBrush(fill_color)
                painter.setPen(QPen(border_color, 1.5))
                painter.drawPath(path)

                if sector_progress > 0.2:
                    mid_angle = math.radians(start_angle + sweep_angle / 2)
                    text_r = (current_inner + current_outer) / 2
                    sector_center_x = center.x() + text_r * math.cos(mid_angle)
                    sector_center_y = center.y() + text_r * math.sin(mid_angle)

                    alpha = max(0, min(255, int(255 * sector_progress)))
                    painter.setPen(QPen(QColor(255, 255, 255, alpha)))

                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sector_center_x - 16), int(sector_center_y - 20), pixmap)
                        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
                        painter.drawText(int(sector_center_x - 45), int(sector_center_y + 14), 90, 18, Qt.AlignmentFlag.AlignCenter, name)
                    else:
                        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
                        painter.drawText(int(sector_center_x - 45), int(sector_center_y - 10), 90, 20, Qt.AlignmentFlag.AlignCenter, name)

        if center_scale > 0:
            center_path = QPainterPath()
            center_path.addEllipse(center, current_inner - 4, current_inner - 4)
            painter.setBrush(QColor(24, 24, 24, int(235 * center_scale)))
            painter.setPen(QPen(QColor(255, 255, 255, int(40 * center_scale)), 1))
            painter.drawPath(center_path)

            if center_scale > 0.5:
                painter.setPen(QPen(QColor(200, 200, 200, int(180 * center_scale))))
                painter.setFont(QFont("Segoe UI Variable Display", 9, QFont.Weight.Bold))
                painter.drawText(int(center.x() - 35), int(center.y() - 10), 70, 20, Qt.AlignmentFlag.AlignCenter, "CIRCLE")