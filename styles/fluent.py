import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient
from PyQt6.QtCore import QPointF, Qt, QRectF
from styles.base_style import BaseStyle


class FluentStyle(BaseStyle):
    name = "Fluent"

    def create_sector_path(
        self,
        center: QPointF,
        r_in: float,
        r_out: float,
        start_deg: float,
        sweep_deg: float,
        corner_radius: float = 12.0
    ) -> QPainterPath:
        """
        Creates a sector path with rounded join corners on all 4 vertices.
        """
        path = QPainterPath()
        if sweep_deg <= 0 or r_out <= r_in:
            return path

        max_r_c = (r_out - r_in) * 0.28
        r_c = max(2.0, min(corner_radius, max_r_c))

        delta_out = math.degrees(r_c / r_out) if r_out > 0 else 0
        delta_in = math.degrees(r_c / r_in) if r_in > 0 else 0

        if sweep_deg <= (2 * delta_out) or sweep_deg <= (2 * delta_in):
            outer_rect = QRectF(center.x() - r_out, center.y() - r_out, r_out * 2, r_out * 2)
            inner_rect = QRectF(center.x() - r_in, center.y() - r_in, r_in * 2, r_in * 2)
            a2 = math.radians(start_deg + sweep_deg)
            path.arcMoveTo(outer_rect, -start_deg)
            path.arcTo(outer_rect, -start_deg, -sweep_deg)
            path.lineTo(QPointF(center.x() + r_in * math.cos(a2), center.y() + r_in * math.sin(a2)))
            path.arcTo(inner_rect, -start_deg - sweep_deg, sweep_deg)
            path.closeSubpath()
            return path

        a1 = math.radians(start_deg)
        a1_out = math.radians(start_deg + delta_out)
        a2_out = math.radians(start_deg + sweep_deg - delta_out)
        a2 = math.radians(start_deg + sweep_deg)
        a2_in = math.radians(start_deg + sweep_deg - delta_in)
        a1_in = math.radians(start_deg + delta_in)

        P_rad_out_1 = QPointF(center.x() + (r_out - r_c) * math.cos(a1), center.y() + (r_out - r_c) * math.sin(a1))
        V_out_1     = QPointF(center.x() + r_out * math.cos(a1), center.y() + r_out * math.sin(a1))
        P_out_1     = QPointF(center.x() + r_out * math.cos(a1_out), center.y() + r_out * math.sin(a1_out))

        P_out_2     = QPointF(center.x() + r_out * math.cos(a2_out), center.y() + r_out * math.sin(a2_out))
        V_out_2     = QPointF(center.x() + r_out * math.cos(a2), center.y() + r_out * math.sin(a2))
        P_rad_out_2 = QPointF(center.x() + (r_out - r_c) * math.cos(a2), center.y() + (r_out - r_c) * math.sin(a2))

        P_rad_in_2  = QPointF(center.x() + (r_in + r_c) * math.cos(a2), center.y() + (r_in + r_c) * math.sin(a2))
        V_in_2      = QPointF(center.x() + r_in * math.cos(a2), center.y() + r_in * math.sin(a2))
        P_in_2      = QPointF(center.x() + r_in * math.cos(a2_in), center.y() + r_in * math.sin(a2_in))

        P_in_1      = QPointF(center.x() + r_in * math.cos(a1_in), center.y() + r_in * math.sin(a1_in))
        V_in_1      = QPointF(center.x() + r_in * math.cos(a1), center.y() + r_in * math.sin(a1))
        P_rad_in_1  = QPointF(center.x() + (r_in + r_c) * math.cos(a1), center.y() + (r_in + r_c) * math.sin(a1))

        outer_rect = QRectF(center.x() - r_out, center.y() - r_out, r_out * 2, r_out * 2)
        inner_rect = QRectF(center.x() - r_in, center.y() - r_in, r_in * 2, r_in * 2)

        path.moveTo(P_rad_out_1)
        path.quadTo(V_out_1, P_out_1)

        sweep_out = sweep_deg - 2 * delta_out
        path.arcTo(outer_rect, -(start_deg + delta_out), -sweep_out)

        path.quadTo(V_out_2, P_rad_out_2)
        path.lineTo(P_rad_in_2)
        path.quadTo(V_in_2, P_in_2)

        sweep_in = sweep_deg - 2 * delta_in
        path.arcTo(inner_rect, -(start_deg + sweep_deg - delta_in), sweep_in)

        path.quadTo(V_in_1, P_rad_in_1)
        path.lineTo(P_rad_out_1)
        path.closeSubpath()

        return path

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        is_dark = (getattr(widget, "theme_mode", "dark") == "dark")

        base_inner = widget.radius_inner * max(0.01, center_scale) + 4
        base_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        if num_items > 0 and sector_progress > 0.05:
            angle_per_item = 360 / num_items
            gap = max(4.0, 360 / num_items * 0.08)

            for i, app_info in enumerate(widget.apps):
                name = app_info.get("name", "")
                is_hovered = (i == hovered_index and sector_progress >= 0.85)

                r_in = base_inner
                r_out = base_outer + (7.0 if is_hovered else 0.0)

                start_angle = i * angle_per_item - 90 + (gap / 2)
                sweep_angle = angle_per_item - gap

                c_rad = max(6.0, min(14.0, (r_out - r_in) * 0.22))

                # 1. Soft Drop Shadow under Sector
                shadow_offset = QPointF(0, 3.5 * sector_progress)
                shadow_path = self.create_sector_path(center + shadow_offset, r_in, r_out, start_angle, sweep_angle, c_rad)
                shadow_alpha = int((50 if is_dark else 28) * sector_progress)
                painter.setBrush(QColor(0, 10, 30, shadow_alpha))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(shadow_path)

                # 2. Ambient Glow for Hovered Sector
                if is_hovered:
                    glow_path = self.create_sector_path(center, r_in - 2, r_out + 4, start_angle, sweep_angle, c_rad + 2)
                    glow_alpha = int(90 * sector_progress) if is_dark else int(75 * sector_progress)
                    painter.setBrush(QColor(0, 120, 240, glow_alpha))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(glow_path)

                # 3. Main Sector Path & Gradient
                path = self.create_sector_path(center, r_in, r_out, start_angle, sweep_angle, c_rad)

                mid_angle_rad = math.radians(start_angle + sweep_angle / 2)
                mid_r = (r_in + r_out) / 2
                sec_cx = center.x() + mid_r * math.cos(mid_angle_rad)
                sec_cy = center.y() + mid_r * math.sin(mid_angle_rad)

                grad = QLinearGradient(
                    QPointF(center.x() + r_out * math.cos(mid_angle_rad - math.pi/4), center.y() + r_out * math.sin(mid_angle_rad - math.pi/4)),
                    QPointF(center.x() + r_out * math.cos(mid_angle_rad + math.pi/4), center.y() + r_out * math.sin(mid_angle_rad + math.pi/4))
                )

                if is_hovered:
                    grad.setColorAt(0.0, QColor(60, 155, 255, int(245 * sector_progress)))
                    grad.setColorAt(1.0, QColor(0, 110, 230, int(255 * sector_progress)))
                    border_color = QColor(255, 255, 255, int(245 * sector_progress))
                    text_color_val = QColor(255, 255, 255, int(255 * sector_progress))
                else:
                    if is_dark:
                        grad.setColorAt(0.0, QColor(44, 48, 58, int(230 * sector_progress)))
                        grad.setColorAt(1.0, QColor(24, 27, 34, int(245 * sector_progress)))
                        border_color = QColor(255, 255, 255, int(35 * sector_progress))
                        text_color_val = QColor(240, 244, 252, int(255 * sector_progress))
                    else:
                        grad.setColorAt(0.0, QColor(248, 252, 255, int(240 * sector_progress)))
                        grad.setColorAt(1.0, QColor(220, 232, 250, int(215 * sector_progress)))
                        border_color = QColor(255, 255, 255, int(245 * sector_progress))
                        text_color_val = QColor(20, 30, 48, int(255 * sector_progress))

                painter.setBrush(grad)
                painter.setPen(QPen(border_color, 1.8 if is_hovered else 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)

                if sector_progress > 0.25:
                    hk = app_info.get("hotkey", "").strip().upper() if getattr(widget, "show_hotkeys", True) else ""
                    disp_name = f"{name} [{hk}]" if hk else name
                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sec_cx - 16), int(sec_cy - 24), pixmap)
                        painter.setPen(text_color_val)
                        painter.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
                        painter.drawText(int(sec_cx - 60), int(sec_cy + 10), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)
                    else:
                        painter.setPen(text_color_val)
                        painter.setFont(QFont("Roboto", 11, QFont.Weight.Bold))
                        painter.drawText(int(sec_cx - 60), int(sec_cy - 11), 120, 22, Qt.AlignmentFlag.AlignCenter, disp_name)

        # Central Button Circle with Windows 11 Logo
        if center_scale > 0:
            is_center_hovered = (hovered_index == -2)
            c_radius = (base_inner - 2) + (2.5 if is_center_hovered else 0.0)

            # Central shadow
            shadow_c = QPainterPath()
            shadow_c.addEllipse(center + QPointF(0, 3.0), c_radius, c_radius)
            painter.setBrush(QColor(0, 0, 0, int(45 * center_scale)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(shadow_c)

            center_path = QPainterPath()
            center_path.addEllipse(center, c_radius, c_radius)

            center_grad = QLinearGradient(
                QPointF(center.x(), center.y() - c_radius),
                QPointF(center.x(), center.y() + c_radius)
            )

            if is_center_hovered:
                center_grad.setColorAt(0.0, QColor(225, 55, 55, int(245 * center_scale)))
                center_grad.setColorAt(1.0, QColor(190, 35, 35, int(255 * center_scale)))
                c_border = QColor(255, 255, 255, int(220 * center_scale))
                cross_color = QColor(255, 255, 255, int(255 * center_scale))
            else:
                if is_dark:
                    center_grad.setColorAt(0.0, QColor(44, 49, 60, int(235 * center_scale)))
                    center_grad.setColorAt(1.0, QColor(22, 25, 32, int(250 * center_scale)))
                    c_border = QColor(255, 255, 255, int(40 * center_scale))
                    cross_color = QColor(210, 215, 225, int(220 * center_scale))
                else:
                    center_grad.setColorAt(0.0, QColor(255, 255, 255, int(250 * center_scale)))
                    center_grad.setColorAt(1.0, QColor(228, 236, 248, int(235 * center_scale)))
                    c_border = QColor(180, 190, 205, int(200 * center_scale))
                    cross_color = QColor(40, 50, 70, int(220 * center_scale))

            painter.setBrush(center_grad)
            painter.setPen(QPen(c_border, 1.8 if is_center_hovered else 1.2))
            painter.drawPath(center_path)

            # Draw Close Cross (Крестик)
            if center_scale > 0.4:
                cross_size = 13.0 * center_scale
                half = cross_size / 2.0
                painter.setPen(QPen(cross_color, 2.2 * center_scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(center.x() - half, center.y() - half), QPointF(center.x() + half, center.y() + half))
                painter.drawLine(QPointF(center.x() - half, center.y() + half), QPointF(center.x() + half, center.y() - half))