import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import QPointF, Qt
from styles.base_style import BaseStyle

class MaterialStyle(BaseStyle):
    name = "Material"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        if num_items == 0:
            return

        current_inner = widget.radius_inner * max(0.01, center_scale)
        current_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        angle_per_item = 360 / num_items
        gap = 5.0 # В Material зазоры чуть больше

        # Палитра Material Design
        material_colors = [
            QColor(33, 150, 243),  # Blue
            QColor(156, 39, 176),  # Purple
            QColor(76, 175, 80),   # Green
            QColor(255, 152, 0),   # Orange
            QColor(233, 30, 99),   # Pink
            QColor(0, 188, 212),   # Cyan
        ]

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
                    base_color = material_colors[i % len(material_colors)]
                    fill_color = QColor(base_color.red(), base_color.green(), base_color.blue(), int(240 * sector_progress))
                    border_color = QColor(255, 255, 255, int(220 * sector_progress))
                else:
                    fill_color = QColor(28, 27, 31, int(230 * sector_progress)) # Material Dark Surface
                    border_color = QColor(73, 69, 79, int(150 * sector_progress))

                painter.setBrush(fill_color)
                painter.setPen(QPen(border_color, 1.5))
                painter.drawPath(path)

                if sector_progress > 0.2:
                    mid_angle = math.radians(start_angle + sweep_angle / 2)
                    text_r = (current_inner + current_outer) / 2
                    sector_center_x = center.x() + text_r * math.cos(mid_angle)
                    sector_center_y = center.y() + text_r * math.sin(mid_angle)

                    alpha = max(0, min(255, int(255 * sector_progress)))
                    painter.setPen(QPen(QColor(230, 225, 229, alpha)))

                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sector_center_x - 16), int(sector_center_y - 20), pixmap)
                        painter.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
                        painter.drawText(int(sector_center_x - 45), int(sector_center_y + 14), 90, 18, Qt.AlignmentFlag.AlignCenter, name)
                    else:
                        painter.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
                        painter.drawText(int(sector_center_x - 45), int(sector_center_y - 10), 90, 20, Qt.AlignmentFlag.AlignCenter, name)

        if center_scale > 0:
            center_path = QPainterPath()
            center_path.addEllipse(center, current_inner - 4, current_inner - 4)
            painter.setBrush(QColor(30, 29, 34, int(245 * center_scale)))
            painter.setPen(QPen(QColor(103, 80, 164, int(180 * center_scale)), 2)) # Material Primary Accent Border
            painter.drawPath(center_path)

            if center_scale > 0.5:
                painter.setPen(QPen(QColor(208, 188, 255, int(230 * center_scale))))
                painter.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
                painter.drawText(int(center.x() - 35), int(center.y() - 10), 70, 20, Qt.AlignmentFlag.AlignCenter, "Material")