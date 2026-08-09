import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt6.QtCore import QPointF, Qt
from styles.base_style import BaseStyle


class SolidStyle(BaseStyle):
    name = "Solid"

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        is_dark = (getattr(widget, "theme_mode", "dark") == "dark")

        current_inner = widget.radius_inner * max(0.01, center_scale)
        current_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        if num_items > 0 and sector_progress > 0.05:
            # 1. Continuous Seamless Solid Donut Ring (Unified ring without sector gap cuts)
            donut_outer = QPainterPath()
            donut_outer.addEllipse(center, current_outer, current_outer)
            donut_inner = QPainterPath()
            donut_inner.addEllipse(center, current_inner, current_inner)
            donut_ring = donut_outer.subtracted(donut_inner)

            if is_dark:
                ring_fill = QColor(26, 30, 40, int(235 * sector_progress))
                ring_border = QColor(255, 255, 255, int(45 * sector_progress))
            else:
                ring_fill = QColor(242, 245, 252, int(240 * sector_progress))
                ring_border = QColor(0, 0, 0, int(35 * sector_progress))

            painter.fillPath(donut_ring, ring_fill)
            painter.strokePath(donut_ring, QPen(ring_border, 1.4))

            angle_per_item = 360 / num_items

            # 2. Draw Hovered Sector Highlight Overlay
            if hovered_index >= 0 and hovered_index < num_items and sector_progress >= 0.85:
                start_angle = hovered_index * angle_per_item - 90
                sweep_angle = angle_per_item
                r_out = current_outer + 3.0

                h_path = QPainterPath()
                h_path.arcMoveTo(
                    center.x() - r_out, center.y() - r_out,
                    r_out * 2, r_out * 2, -start_angle
                )
                h_path.arcTo(
                    center.x() - r_out, center.y() - r_out,
                    r_out * 2, r_out * 2, -start_angle, -sweep_angle
                )
                h_path.arcTo(
                    center.x() - current_inner, center.y() - current_inner,
                    current_inner * 2, current_inner * 2, -start_angle - sweep_angle, sweep_angle
                )
                h_path.closeSubpath()

                hover_fill = QColor(0, 120, 215, int(230 * sector_progress))
                hover_border = QColor(255, 255, 255, int(220 * sector_progress))
                painter.fillPath(h_path, hover_fill)
                painter.strokePath(h_path, QPen(hover_border, 1.8))

            # 3. Draw App Icons & Text Labels
            if sector_progress > 0.2:
                for i, app_info in enumerate(widget.apps):
                    name = app_info.get("name", "")
                    hk = app_info.get("hotkey", "").strip().upper() if getattr(widget, "show_hotkeys", True) else ""
                    is_hovered = (i == hovered_index and sector_progress >= 0.85)

                    mid_angle = math.radians(i * angle_per_item - 90 + angle_per_item / 2)
                    text_r = (current_inner + current_outer) / 2
                    sec_cx = center.x() + text_r * math.cos(mid_angle)
                    sec_cy = center.y() + text_r * math.sin(mid_angle)

                    text_color = QColor(255, 255, 255) if (is_hovered or is_dark) else QColor(20, 20, 25)
                    disp_name = f"{name} [{hk}]" if hk else name

                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sec_cx - 16), int(sec_cy - 24), pixmap)
                        painter.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
                        sh_col = QColor(0, 0, 0, int(200 * sector_progress)) if is_dark else QColor(255, 255, 255, int(200 * sector_progress))
                        painter.setPen(sh_col)
                        painter.drawText(int(sec_cx - 59), int(sec_cy + 11), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                        painter.setPen(QPen(text_color))
                        painter.drawText(int(sec_cx - 60), int(sec_cy + 10), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                    else:
                        painter.setFont(QFont("Roboto", 11, QFont.Weight.Bold))
                        sh_col = QColor(0, 0, 0, int(200 * sector_progress)) if is_dark else QColor(255, 255, 255, int(200 * sector_progress))
                        painter.setPen(sh_col)
                        painter.drawText(int(sec_cx - 59), int(sec_cy - 10), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                        painter.setPen(QPen(text_color))
                        painter.drawText(int(sec_cx - 60), int(sec_cy - 11), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)

        # 4. Central Close Button Circle
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
