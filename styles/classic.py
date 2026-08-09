import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import QPointF, Qt
from styles.base_style import BaseStyle

class ClassicStyle(BaseStyle):
    name = "Classic"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        is_dark = (getattr(widget, "theme_mode", "dark") == "dark")

        current_inner = widget.radius_inner * max(0.01, center_scale)
        current_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        if num_items > 0 and sector_progress > 0.05:
            angle_per_item = 360 / num_items
            gap = 3.0

            for i, app_info in enumerate(widget.apps):
                name = app_info.get("name", "")
                is_hovered = (i == hovered_index and sector_progress >= 0.85)

                r_out = current_outer + (4.0 if is_hovered else 0.0)
                start_angle = i * angle_per_item - 90 + (gap / 2)
                sweep_angle = angle_per_item - gap

                path = QPainterPath()
                path.arcMoveTo(
                    center.x() - r_out, center.y() - r_out,
                    r_out * 2, r_out * 2, -start_angle
                )
                path.arcTo(
                    center.x() - r_out, center.y() - r_out,
                    r_out * 2, r_out * 2, -start_angle, -sweep_angle
                )
                path.arcTo(
                    center.x() - current_inner, center.y() - current_inner,
                    current_inner * 2, current_inner * 2, -start_angle - sweep_angle, sweep_angle
                )
                path.closeSubpath()

                if is_hovered:
                    fill_color = QColor(0, 103, 192, int(225 * sector_progress))
                    border_color = QColor(255, 255, 255, int(220 * sector_progress))
                    text_color = QColor(255, 255, 255, int(255 * sector_progress))
                else:
                    if is_dark:
                        fill_color = QColor(22, 24, 30, int(204 * sector_progress))
                        border_color = QColor(255, 255, 255, int(55 * sector_progress))
                        text_color = QColor(245, 245, 250, int(255 * sector_progress))
                    else:
                        fill_color = QColor(245, 247, 252, int(204 * sector_progress))
                        border_color = QColor(0, 0, 0, int(50 * sector_progress))
                        text_color = QColor(20, 20, 25, int(255 * sector_progress))

                painter.setBrush(fill_color)
                painter.setPen(QPen(border_color, 1.5))
                painter.drawPath(path)

                if sector_progress > 0.2:
                    mid_angle = math.radians(start_angle + sweep_angle / 2)
                    text_r = (current_inner + r_out) / 2
                    sector_center_x = center.x() + text_r * math.cos(mid_angle)
                    sector_center_y = center.y() + text_r * math.sin(mid_angle)

                    hk = app_info.get("hotkey", "").strip().upper() if getattr(widget, "show_hotkeys", True) else ""
                    disp_name = f"{name} [{hk}]" if hk else name

                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sector_center_x - 16), int(sector_center_y - 24), pixmap)
                        painter.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
                        # Text shadow
                        sh_col = QColor(0, 0, 0, int(200 * sector_progress)) if is_dark else QColor(255, 255, 255, int(200 * sector_progress))
                        painter.setPen(sh_col)
                        painter.drawText(int(sector_center_x - 59), int(sector_center_y + 11), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                        # Text main
                        painter.setPen(QPen(text_color))
                        painter.drawText(int(sector_center_x - 60), int(sector_center_y + 10), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                    else:
                        painter.setFont(QFont("Roboto", 11, QFont.Weight.Bold))
                        sh_col = QColor(0, 0, 0, int(200 * sector_progress)) if is_dark else QColor(255, 255, 255, int(200 * sector_progress))
                        painter.setPen(sh_col)
                        painter.drawText(int(sector_center_x - 59), int(sector_center_y - 10), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                        painter.setPen(QPen(text_color))
                        painter.drawText(int(sector_center_x - 60), int(sector_center_y - 11), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)

        # Central Close Button Circle
        if center_scale > 0:
            is_center_hovered = (hovered_index == -2)
            c_radius = (current_inner - 4) + (2.0 if is_center_hovered else 0.0)

            center_path = QPainterPath()
            center_path.addEllipse(center, c_radius, c_radius)

            if is_center_hovered:
                c_fill = QColor(210, 45, 45, int(240 * center_scale))
                c_border = QColor(255, 255, 255, int(220 * center_scale))
                cross_color = QColor(255, 255, 255, int(255 * center_scale))
            else:
                if is_dark:
                    c_fill = QColor(24, 24, 28, int(240 * center_scale))
                    c_border = QColor(255, 255, 255, int(45 * center_scale))
                    cross_color = QColor(220, 220, 225, int(220 * center_scale))
                else:
                    c_fill = QColor(255, 255, 255, int(250 * center_scale))
                    c_border = QColor(190, 195, 205, int(200 * center_scale))
                    cross_color = QColor(40, 40, 50, int(220 * center_scale))

            painter.setBrush(c_fill)
            painter.setPen(QPen(c_border, 1.4))
            painter.drawPath(center_path)

            # Draw Close Cross (Крестик)
            if center_scale > 0.4:
                cross_size = 14 * center_scale
                half = cross_size / 2.0
                painter.setPen(QPen(cross_color, 2.4 * center_scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(center.x() - half, center.y() - half), QPointF(center.x() + half, center.y() + half))
                painter.drawLine(QPointF(center.x() - half, center.y() + half), QPointF(center.x() + half, center.y() - half))