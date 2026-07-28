import math
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient
from PyQt6.QtCore import QPointF, Qt, QRectF
from styles.base_style import BaseStyle

class FluentStyle(BaseStyle):
    name = "Fluent"

    def create_rounded_sector_path(self, center: QPointF, r_in: float, r_out: float, start_deg: float, sweep_deg: float) -> QPainterPath:
        """
        Строит сектор с мягкими скруглёнными фасками по углам (как подушечки на макете)
        """
        path = QPainterPath()
        if sweep_deg <= 0 or r_out <= r_in:
            return path

        a1 = math.radians(start_deg)
        a2 = math.radians(start_deg + sweep_deg)

        # Вычисляем радиусы скругляющих дуг
        corner_r = 6.0
        
        # Точки внешних и внутренних дуг
        outer_rect = QRectF(center.x() - r_out, center.y() - r_out, r_out * 2, r_out * 2)
        inner_rect = QRectF(center.x() - r_in, center.y() - r_in, r_in * 2, r_in * 2)

        p_in1 = QPointF(center.x() + r_in * math.cos(a1), center.y() + r_in * math.sin(a1))
        p_out1 = QPointF(center.x() + r_out * math.cos(a1), center.y() + r_out * math.sin(a1))
        p_in2 = QPointF(center.x() + r_in * math.cos(a2), center.y() + r_in * math.sin(a2))
        p_out2 = QPointF(center.x() + r_out * math.cos(a2), center.y() + r_out * math.sin(a2))

        # Формируем путь со сглаженными стыками
        path.arcMoveTo(outer_rect, -start_deg)
        path.arcTo(outer_rect, -start_deg, -sweep_deg)
        path.lineTo(p_in2)
        path.arcTo(inner_rect, -start_deg - sweep_deg, sweep_deg)
        path.lineTo(p_out1)
        path.closeSubpath()

        return path

    def draw(self, painter: QPainter, widget, center: QPointF, hovered_index: int, sector_progress: float, center_scale: float):
        num_items = len(widget.apps)
        if num_items == 0:
            return

        is_dark = (getattr(widget, "theme_mode", "light") == "dark")

        current_inner = widget.radius_inner * max(0.01, center_scale) + 4
        current_outer = widget.radius_inner + (widget.radius_outer - widget.radius_inner) * sector_progress

        angle_per_item = 360 / num_items
        gap = 5.5  # Отступ между секторами для эффекта парящих плашек

        if sector_progress > 0.05:
            for i, app_info in enumerate(widget.apps):
                name = app_info.get("name", "")
                start_angle = i * angle_per_item - 90 + (gap / 2)
                sweep_angle = angle_per_item - gap

                # Рисуем контур плашки
                path = self.create_rounded_sector_path(center, current_inner, current_outer, start_angle, sweep_angle)

                # Вычисляем геометрический центр текущего сектора
                mid_angle_rad = math.radians(start_angle + sweep_angle / 2)
                mid_r = (current_inner + current_outer) / 2
                sec_cx = center.x() + mid_r * math.cos(mid_angle_rad)
                sec_cy = center.y() + mid_r * math.sin(mid_angle_rad)

                # Вертикальный объемный градиент (создает 3D блик сверху плашки)
                grad = QLinearGradient(
                    QPointF(sec_cx, center.y() - current_outer),
                    QPointF(sec_cx, center.y() + current_outer)
                )

                if i == hovered_index and sector_progress >= 0.85:
                    # Hover состояние (Яркий синий Fluent Accent из концепта)
                    grad.setColorAt(0.0, QColor(0, 130, 240, int(240 * sector_progress)))
                    grad.setColorAt(1.0, QColor(0, 80, 180, int(250 * sector_progress)))
                    border_color = QColor(220, 240, 255, int(230 * sector_progress))
                    text_color_val = QColor(255, 255, 255, int(255 * sector_progress))
                else:
                    if is_dark:
                        # Dark Mode (Глубокий угольно-акриловый градиент из макета)
                        grad.setColorAt(0.0, QColor(50, 54, 65, int(210 * sector_progress)))
                        grad.setColorAt(1.0, QColor(22, 24, 30, int(230 * sector_progress)))
                        border_color = QColor(255, 255, 255, int(35 * sector_progress))
                        text_color_val = QColor(235, 240, 250, int(255 * sector_progress))
                    else:
                        # Light Mode (Полупрозрачный белый с бликом из макета)
                        grad.setColorAt(0.0, QColor(255, 255, 255, int(245 * sector_progress)))
                        grad.setColorAt(1.0, QColor(220, 230, 245, int(220 * sector_progress)))
                        border_color = QColor(255, 255, 255, int(255 * sector_progress))
                        text_color_val = QColor(30, 41, 59, int(255 * sector_progress))

                # Отрисовка плашки с тонкой полупрозрачной обводкой
                painter.setBrush(grad)
                painter.setPen(QPen(border_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)

                # Отрисовка иконки и подписи
                if sector_progress > 0.25:
                    pixmap = widget.icons[i] if i < len(widget.icons) else None
                    if pixmap and not pixmap.isNull():
                        painter.drawPixmap(int(sec_cx - 16), int(sec_cy - 22), pixmap)
                        painter.setPen(text_color_val)
                        painter.setFont(QFont("Segoe UI Variable Text", 9, QFont.Weight.DemiBold))
                        painter.drawText(int(sec_cx - 50), int(sec_cy + 12), 100, 18, Qt.AlignmentFlag.AlignCenter, name)
                    else:
                        painter.setPen(text_color_val)
                        painter.setFont(QFont("Segoe UI Variable Text", 10, QFont.Weight.DemiBold))
                        painter.drawText(int(sec_cx - 50), int(sec_cy - 10), 100, 20, Qt.AlignmentFlag.AlignCenter, name)

        # Центральный круг с логотипом Windows 11
        if center_scale > 0:
            center_path = QPainterPath()
            center_path.addEllipse(center, current_inner - 2, current_inner - 2)

            center_grad = QLinearGradient(
                QPointF(center.x(), center.y() - current_inner),
                QPointF(center.x(), center.y() + current_inner)
            )

            if is_dark:
                center_grad.setColorAt(0.0, QColor(48, 52, 62, int(220 * center_scale)))
                center_grad.setColorAt(1.0, QColor(20, 22, 28, int(240 * center_scale)))
                c_border = QColor(255, 255, 255, int(40 * center_scale))
            else:
                center_grad.setColorAt(0.0, QColor(255, 255, 255, int(255 * center_scale)))
                center_grad.setColorAt(1.0, QColor(215, 225, 242, int(245 * center_scale)))
                c_border = QColor(255, 255, 255, int(255 * center_scale))

            painter.setBrush(center_grad)
            painter.setPen(QPen(c_border, 1.8))
            painter.drawPath(center_path)

            # Иконка Windows 11 по центру
            if center_scale > 0.4:
                win_blue = QColor(0, 120, 212, int(255 * center_scale))
                painter.setBrush(win_blue)
                painter.setPen(Qt.PenStyle.NoPen)

                icon_size = 18 * center_scale
                gap_win = 2.5 * center_scale
                half = (icon_size - gap_win) / 2

                cx, cy = center.x(), center.y()

                painter.drawRect(QRectF(cx - half - gap_win/2, cy - half - gap_win/2, half, half))
                painter.drawRect(QRectF(cx + gap_win/2, cy - half - gap_win/2, half, half))
                painter.drawRect(QRectF(cx - half - gap_win/2, cy + gap_win/2, half, half))
                painter.drawRect(QRectF(cx + gap_win/2, cy + gap_win/2, half, half))