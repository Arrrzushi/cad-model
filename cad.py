"""
Dynamic 2D CAD Model of a Steel Girder Bridge
Author: Arushi 
"""

import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
                               QPushButton, QComboBox, QGroupBox, QGridLayout,
                               QScrollArea, QFileDialog, QSplitter, QMessageBox,
                               QTextEdit)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPixmap, QPainterPath


class BridgeCADWidget(QWidget):
    """widget for drawing bridge CAD views """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 600)
        self.view_type = 'cross-section'
        self.setMouseTracking(True)  # enable mouse tracking for hover
        
        # storingg hover label regions: list of (QRectF, text, bg_color, text_color)
        self.hover_labels = []
        self.hovered_label_index = -1
        
        # top view hover tracking 
        self.top_view_hover_zones = []  # list of (QRectF, element_type)
        self.hovered_top_view_element = None
        
        # bridge parameters with default values (all in mm)
        self.params = {
            'span_length': 35000,
            'num_girders': 4,
            'girder_spacing': 2750,
            'cross_bracing_spacing': 3500,
            'carriageway_width': 10500,
            'skew_angle': 0,
            'deck_thickness': 200,
            'footpath_width': 1500,
            'footpath_thickness': 200,
            'crash_barrier_width': 500,
            'railing_height': 1000,
            'footpath_config': 'both',
            'deck_overhang': 1000,
            'railing_width': 100,
            'median_present': False,
            'median_width': 1200,
        }
        
        # girder dimensions (mm)
        self.girder = {
            'depth': 500,
            'flange_width': 180,
            'flange_thickness': 17.2,
            'web_thickness': 10.2,
        }
        
        # stiffener dimensions
        self.stiffener = {
            'width': 84.9,
            'height': 465.6,
        }

        self.girder_visual_scale = {
            'depth': 3.0,
            'flange_width': 3.75,
            'flange_thickness': 4.05,
            'web_thickness': 3.75,
        }
        
        # crash barrier dimensions (mm) 
        self.crash_barrier = {
            'width': 500,
            'height': 800,
            'base_width': 300,
        }
        
        # railing dimensions
        self.railing = {
            'post_dia': 50,
            'height': 1000,
            'rail_count': 3,
            'width': 100,
        }
        
    def set_view_type(self, view_type):
        self.view_type = view_type
        self.update()
        
    def update_params(self, params):
        self.params.update(params)
        self.update()
    
    def mouseMoveEvent(self, event):
        """mouse moving text showing"""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        if self.view_type == 'cross-section':
            # Cross-section hover logic
            new_hovered = -1
            for i, (rect, text, bg_color, text_color) in enumerate(self.hover_labels):
                if rect.contains(pos):
                    new_hovered = i
                    break
            
            if new_hovered != self.hovered_label_index:
                self.hovered_label_index = new_hovered
                self.update()
        else:
            # top view hover logic
            new_hovered = None
            for rect, element_type in self.top_view_hover_zones:
                if rect.contains(pos):
                    new_hovered = element_type
                    break
            
            if new_hovered != self.hovered_top_view_element:
                self.hovered_top_view_element = new_hovered
                self.update()

    def register_hover_label(self, x, y, text, bg_color, text_color, font_size=7):
        """lables for catching hover hovering"""
        font = QFont('Arial', font_size, QFont.Bold)
        metrics = self.fontMetrics()
        text_rect = metrics.boundingRect(text)
        
        padding = 5
        hover_rect = QRectF(x - padding, y - text_rect.height() - padding,
                            text_rect.width() + 2*padding + 20, text_rect.height() + 2*padding + 10)
        
        self.hover_labels.append((hover_rect, text, bg_color, text_color))
        return len(self.hover_labels) - 1

    def draw_hover_label_if_active(self, painter, label_index, x, y, text, bg_color, text_color, font_size=7):
        """label only if its being hovered"""
        if self.hovered_label_index == label_index:
            self.draw_text_with_background(painter, x, y, text, bg_color, text_color, font_size, True)
        
    def paintEvent(self, event):
        # clear hover labels at start of each paint
        self.hover_labels = []
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if self.view_type == 'cross-section':
            self.draw_cross_section(painter)
        else:
            self.draw_top_view(painter)
    def draw_text_with_background(self, painter, x, y, text,
                              bg_color=QColor(255, 255, 255, 230), 
                              text_color=QColor(0, 0, 0), font_size=7, bold=False):

        font_weight = QFont.Bold if bold else QFont.Normal
        font = QFont('Arial', font_size, font_weight)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        # breaking text in 2 to space be space
        lines = text.split("\n")

        line_height = metrics.height()
        max_width = max(metrics.boundingRect(line).width() for line in lines)
        total_height = line_height * len(lines)

        padding = 2

        # background rectangle
        bg_rect = QRectF(
            x - padding,
            y - total_height - padding,
            max_width + 2 * padding,
            total_height + 2 * padding
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(bg_rect)

        # Draw each text line
        painter.setPen(QPen(text_color, 0.8))
        first_line_y = y - total_height + metrics.ascent()

        for i, line in enumerate(lines):
            painter.drawText(int(x), int(first_line_y + i * line_height), line)

    
    def draw_dimension_arrow(self, painter, x1, y1, x2, y2, text, horizontal=True, offset=0, text_offset=0, draw_extensions=True, extension_direction='down', extension_end_y=None):
        """dimension line with arrows and text with extension lines"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
        
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_size, y1 - arrow_size/2),
                QPointF(x1 + arrow_size, y1 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - arrow_size/2),
                QPointF(x2 - arrow_size, y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow))
            
            if draw_extensions:
                painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
                
                if extension_end_y is not None:
                    # Draw extension lines to specified y coordinate
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                else:
                    extension_length = 40
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 - extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 - extension_length))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 + extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 + extension_length))
                
                painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            
            text_x = (x1 + x2) / 2
            text_y = y1 - 8 + text_offset if offset >= 0 else y1 + 15 + text_offset
            
            font = QFont('Arial', 7, QFont.Bold)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)
        else:
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_size/2, y1 + arrow_size),
                QPointF(x1 + arrow_size/2, y1 + arrow_size)
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size/2, y2 - arrow_size),
                QPointF(x2 + arrow_size/2, y2 - arrow_size)
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            if draw_extensions:
                painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
                extension_length = 20
                
                if extension_direction == 'left':
                    painter.drawLine(QPointF(x1, y1), QPointF(x1 - extension_length, y1))
                    painter.drawLine(QPointF(x2, y2), QPointF(x2 - extension_length, y2))
                else:
                    painter.drawLine(QPointF(x1, y1), QPointF(x1 + extension_length, y1))
                    painter.drawLine(QPointF(x2, y2), QPointF(x2 + extension_length, y2))
                
                painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            
            text_x = x1 + (12 if offset >= 0 else -45) + text_offset
            text_y = (y1 + y2) / 2 + 3
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)
    
    def draw_dimension_arrow_text_outside(self, painter, x1, y1, x2, y2, text, horizontal=True, 
                                          text_side='right', text_offset=15):
        """Dimension line with arrows"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
            
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_size, y1 - arrow_size/2),
                QPointF(x1 + arrow_size, y1 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - arrow_size/2),
                QPointF(x2 - arrow_size, y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow))
            
            if text_side == 'top':
                text_x = (x1 + x2) / 2
                text_y = y1 - text_offset
            else:
                text_x = (x1 + x2) / 2
                text_y = y1 + text_offset + 10
                
            font = QFont('Arial', 7, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
            
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_size/2, y1 + arrow_size),
                QPointF(x1 + arrow_size/2, y1 + arrow_size)
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size/2, y2 - arrow_size),
                QPointF(x2 + arrow_size/2, y2 - arrow_size)
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            text_y = (y1 + y2) / 2 + 3
            if text_side == 'left':
                text_x = x1 - text_offset - 35
            else:
                text_x = x1 + text_offset
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)
        
    def draw_leader_arrow(self, painter, from_x, from_y, to_x, to_y, text, bg_color=QColor(255, 255, 255, 250), text_color=QColor(0, 0, 0)):
        """a leader line with arrow pointing to component"""
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawLine(QPointF(from_x, from_y), QPointF(to_x, to_y))
        
        arrow_size = 5
        angle = math.atan2(to_y - from_y, to_x - from_x)
        
        arrow_points = [
            QPointF(to_x, to_y),
            QPointF(to_x - arrow_size * math.cos(angle - math.pi/6), 
                   to_y - arrow_size * math.sin(angle - math.pi/6)),
            QPointF(to_x - arrow_size * math.cos(angle + math.pi/6), 
                   to_y - arrow_size * math.sin(angle + math.pi/6))
        ]
        
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(QPolygonF(arrow_points))
        
        self.draw_text_with_background(painter, from_x - 5, from_y - 5, text, bg_color, text_color, 7, True)
    
    def draw_clean_leader_line(self, painter, target_x, target_y, label_x, label_y, text, 
                                text_color=QColor(0, 0, 0), line_color=QColor(100, 100, 100)):
        """draw a clean leader line from target point to label with dotted line"""
        # Draw dotted line from target to label
        pen = QPen(line_color, 1.0, Qt.DotLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(target_x, target_y), QPointF(label_x, label_y))
        
        # Draw small circle at target point
        painter.setPen(QPen(line_color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
        
        # Draw text at label position
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        text_height = metrics.height()
        
        # Determine text alignment based on relative position
        if label_x > target_x:
            text_x = label_x + 5
        else:
            text_x = label_x - text_width - 5
        
        text_y = label_y + text_height / 4
        
        # Draw text with background
        self.draw_text_with_background(painter, text_x, text_y, text,
                                       QColor(255, 255, 255, 240), text_color, 7, True)
    
    def compute_deck_total_width(self):
        """Compute total deck width including median if present"""
        carriageway = self.params.get('carriageway_width', 10500)
        crash_barrier = self.params.get('crash_barrier_width', 500)
        footpath_width = self.params.get('footpath_width', 1500)
        fp_config = self.params.get('footpath_config', 'both')
        median_present = self.params.get('median_present', False)
        median_width = self.params.get('median_width', 1200)
        
        if fp_config == 'both':
            num_fp = 2
        elif fp_config in ['left', 'right']:
            num_fp = 1
        else:
            num_fp = 0
        
        # If median is present, we have full carriageway on each side
        if median_present:
            deck_total = (carriageway * 2 +  # Full carriageway on each side
                          median_width +
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        else:
            deck_total = (carriageway + 
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        
        return deck_total, num_fp

    def draw_median_crash_barriers(self, painter, median_start_x, median_end_x, deck_top_y, scale):
        """Draw two crash barriers for median, facing outward"""
        
        # Dimensions
        TOTAL_HEIGHT = 900.0
        TOP_WIDTH = 175.0
        BOTTOM_WIDTH = 350.0
        BASE_VERTICAL = 100.0
        
        h = TOTAL_HEIGHT * scale
        top_w = TOP_WIDTH * scale
        bottom_w = BOTTOM_WIDTH * scale
        base_v = BASE_VERTICAL * scale
        
        median_width_px = median_end_x - median_start_x
        
        # Check if barriers fit
        if bottom_w * 2 > median_width_px:
            fit_scale = median_width_px / (bottom_w * 2) * 0.9
            h *= fit_scale
            top_w *= fit_scale
            bottom_w *= fit_scale
            base_v *= fit_scale
        
        gap = median_width_px - 2 * bottom_w
        if gap < 5:
            gap = 5
            bottom_w = (median_width_px - gap) / 2
            ratio = bottom_w / (BOTTOM_WIDTH * scale)
            h *= ratio
            top_w *= ratio
            base_v *= ratio
        
        y = deck_top_y
        y_base_top = y - base_v
        y_mid = y - (350 * scale * (h / (TOTAL_HEIGHT * scale)))  # proportional
        y_top = y - h
        
        # Offsets 
        scale_ratio = bottom_w / (BOTTOM_WIDTH * scale) if BOTTOM_WIDTH * scale > 0 else 1
        right_at_mid = 250 * scale * scale_ratio
        left_at_top = 50 * scale * scale_ratio
        right_at_top = 225 * scale * scale_ratio
        
        # LEFT barrier - front faces LEFT (toward left carriageway)
        # This is the mirrored version
        x_left = median_start_x
        
        points_left = [
            QPointF(x_left, y),                                      # bottom-left
            QPointF(x_left + bottom_w, y),                           # bottom-right
            QPointF(x_left + bottom_w, y_base_top),                  # right after base
            QPointF(x_left + bottom_w - left_at_top, y_top),         # top-right
            QPointF(x_left + bottom_w - right_at_top, y_top),        # top-left
            QPointF(x_left + bottom_w - right_at_mid, y_mid),        # left at middle
            QPointF(x_left, y_base_top),                             # left after base
        ]
        
        painter.setBrush(QBrush(QColor(255, 210, 160)))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points_left))
        
        # RIGHT barrier - front faces RIGHT (toward right carriageway)
        # This is the original orientation
        x_right = median_end_x - bottom_w
        
        points_right = [
            QPointF(x_right, y),                           # bottom-left
            QPointF(x_right + bottom_w, y),                # bottom-right
            QPointF(x_right + bottom_w, y_base_top),       # right after base
            QPointF(x_right + right_at_mid, y_mid),        # right at middle
            QPointF(x_right + right_at_top, y_top),        # top-right
            QPointF(x_right + left_at_top, y_top),         # top-left
            QPointF(x_right, y_base_top),                  # left after base
        ]
        
        painter.setBrush(QBrush(QColor(255, 210, 160)))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points_right))

    def draw_cross_section(self, painter):
        """Draw cross-section with median support and hover highlighting"""
        GIRDER_COLOR = QColor(40, 40, 40)
        STIFFENER_COLOR = QColor(180, 230, 180)
        CROSS_BRACING_COLOR = QColor(255, 140, 0)
        MEDIAN_COLOR = QColor(255, 200, 100)
        
        width = self.width()
        height = self.height()

        fp_config = self.params.get('footpath_config', 'both')
        left_fp_width = self.params['footpath_width'] if fp_config in ['left', 'both'] else 0
        right_fp_width = self.params['footpath_width'] if fp_config in ['right', 'both'] else 0

        total_deck_width, num_fp = self.compute_deck_total_width()

        margin = 140
        scale = min((width - 2*margin) / total_deck_width,
                (height - 2*margin - 250) / (self.girder['depth'] * self.girder_visual_scale['depth'] +
                                                self.params['deck_thickness'] +
                                                self.params['footpath_thickness'] + 1500))

        center_x = width / 2
        base_y = height - margin - 240

        painter.setFont(QFont('Arial', 11, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        title_text = "CROSS-SECTION VIEW"
        self.draw_text_with_background(painter, 30, 35, title_text, 
                                    QColor(230, 240, 255, 250), QColor(0, 0, 100), 11, True)

        girder_depth_visual = self.girder['depth'] * scale * self.girder_visual_scale['depth']
        girder_top_y = base_y - girder_depth_visual
        deck_thick_px = self.params['deck_thickness'] * scale
        fp_thick_px = self.params['footpath_thickness'] * scale
        deck_bottom_y = girder_top_y
        deck_top_y = deck_bottom_y - deck_thick_px
        fp_bottom_y = deck_bottom_y
        fp_top_y = fp_bottom_y - fp_thick_px

        deck_start_x = center_x - (total_deck_width * scale) / 2
        deck_left_x = deck_start_x
        deck_right_x = deck_start_x + total_deck_width * scale
        
        # Calculate all widths in pixels
        crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        left_fp_width_px = left_fp_width * scale
        right_fp_width_px = right_fp_width * scale
        
        # LAYOUT FROM LEFT TO RIGHT
        # 1. Left footpath starts at deck_left_x
        left_fp_x = deck_left_x
        
        # 2. Left crash barrier starts after left footpath
        left_barrier_x = left_fp_x + left_fp_width_px
        left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        
        # 3. Right footpath ends at deck_right_x
        right_fp_x = deck_right_x - right_fp_width_px
        
        # 4. Right crash barrier ENDS where right footpath STARTS
        right_barrier_end_x = right_fp_x
        right_barrier_x = right_barrier_end_x - crash_barrier_width_px
        
        # 5. Carriageway
        carriageway_start_x = left_barrier_end_x
        carriageway_end_x = right_barrier_x
        
        median_present = self.params.get('median_present', False)
        median_width = self.params.get('median_width', 1200)
        
        if median_present:
            cw_full = self.params['carriageway_width']
            cw_width_px = cw_full * scale
            median_width_px = median_width * scale
            
            cw1_start_x = left_barrier_end_x
            cw1_end_x = cw1_start_x + cw_width_px
            median_start_x = cw1_end_x
            median_end_x = median_start_x + median_width_px
            cw2_start_x = median_end_x
            cw2_end_x = cw2_start_x + cw_width_px
            
            carriageway_start_x = cw1_start_x
            carriageway_end_x = cw2_end_x
        else:
            median_start_x = None
            median_end_x = None

        n = max(1, int(self.params['num_girders']))
        deck_overhang_px = self.params.get('deck_overhang', 1000) * scale
        
        if n > 1:
            first_girder_x = deck_left_x + deck_overhang_px
            last_girder_x = deck_right_x - deck_overhang_px
            available_for_spacing = last_girder_x - first_girder_x
            actual_spacing_px = available_for_spacing / (n - 1) if n > 1 else 0
            positions = [first_girder_x + i * actual_spacing_px for i in range(n)]
        else:
            positions = [center_x]

        flange_half_px = (self.girder['flange_width'] * scale * self.girder_visual_scale['flange_width']) / 2.0
        min_allowed_x = deck_left_x + flange_half_px + 1
        max_allowed_x = deck_right_x - flange_half_px - 1
        positions = [max(min_allowed_x, min(max_allowed_x, p)) for p in positions]

        RAILING_OUTER_WIDTH_MM = 375
        railing_outer_width_px = RAILING_OUTER_WIDTH_MM * scale
        railing_width_px = railing_outer_width_px

        # Draw deck slab
        deck_slab_left = left_barrier_x
        deck_slab_right = right_barrier_end_x
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(deck_slab_left, deck_top_y,
                            deck_slab_right - deck_slab_left, deck_thick_px))

        if median_present:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(cw1_start_x, deck_top_y,
                                cw1_end_x - cw1_start_x, deck_thick_px))
            painter.drawRect(QRectF(cw2_start_x, deck_top_y,
                                cw2_end_x - cw2_start_x, deck_thick_px))
            painter.setBrush(QBrush(MEDIAN_COLOR))
            painter.drawRect(QRectF(median_start_x, deck_top_y,
                                median_end_x - median_start_x, deck_thick_px))
        else:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(carriageway_start_x, deck_top_y,
                                carriageway_end_x - carriageway_start_x, deck_thick_px))

        # Crash barrier deck zones
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawRect(QRectF(left_barrier_x, deck_top_y,
                                crash_barrier_width_px, deck_thick_px))
        painter.drawRect(QRectF(right_barrier_x, deck_top_y,
                                crash_barrier_width_px, deck_thick_px))

        # footpath to deck connecting line
        dashed_pen = QPen(QColor(0, 0, 0), 1.5, Qt.DashLine)
        dashed_pen.setDashPattern([2, 2])  # Tiny dashes

        # making the line dashed
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            # Draw footpath fill only (no border)
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(left_fp_x, fp_top_y,
                                left_fp_width_px, fp_thick_px))
            
            # Draw horizontal edges as solid
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            # Top edge
            painter.drawLine(QPointF(left_fp_x, fp_top_y), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y))
            # Bottom edge
            painter.drawLine(QPointF(left_fp_x, fp_top_y + fp_thick_px), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y + fp_thick_px))
            
            # Left edge 
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawLine(QPointF(left_fp_x, fp_top_y), 
                            QPointF(left_fp_x, fp_top_y + fp_thick_px))
            
            # Right edge
            painter.setPen(dashed_pen)
            painter.drawLine(QPointF(left_fp_x + left_fp_width_px, fp_top_y), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y + fp_thick_px))

        if fp_config in ['right', 'both'] and right_fp_width > 0:
            # Draw footpath fill
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(right_fp_x, fp_top_y,
                                right_fp_width_px, fp_thick_px))
            
            # Draw horizontal edges as solid
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            # Top edge
            painter.drawLine(QPointF(right_fp_x, fp_top_y), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y))
            # Bottom edge
            painter.drawLine(QPointF(right_fp_x, fp_top_y + fp_thick_px), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y + fp_thick_px))
            
            # Left edge (inner edge connecting to deck) - DASHED
            painter.setPen(dashed_pen)
            painter.drawLine(QPointF(right_fp_x, fp_top_y), 
                            QPointF(right_fp_x, fp_top_y + fp_thick_px))
            
            # Right edge (outer edge where railing sits) - SOLID
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawLine(QPointF(right_fp_x + right_fp_width_px, fp_top_y), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y + fp_thick_px))
        # Draw crash barriers
        cb_y = deck_top_y
        # Left barrier: x is where it STARTS (left edge)
        self.draw_crash_barrier(painter, left_barrier_x, cb_y, scale, side='left')
        # Right barrier: x is where it ENDS (right edge) = right_barrier_end_x
        self.draw_crash_barrier(painter, right_barrier_end_x, cb_y, scale, side='right')
        
        if median_present:
            self.draw_median_crash_barriers(painter, median_start_x, median_end_x, deck_top_y, scale)

        # Draw the main deck bottom line solid (only the deck slab portion)
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.drawLine(QPointF(deck_slab_left, deck_bottom_y), 
                        QPointF(deck_slab_right, deck_bottom_y))

        # Draw dashed lines for footpath area bottom and vertical connections
        # Left footpath area
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            painter.setPen(dashed_pen)
            # Bottom line under footpath area (dashed)
            painter.drawLine(QPointF(deck_left_x, deck_bottom_y), 
                            QPointF(deck_slab_left, deck_bottom_y))
            # Outer vertical line from footpath bottom to deck bottom level (dashed)
            painter.drawLine(QPointF(deck_left_x, fp_top_y + fp_thick_px), 
                            QPointF(deck_left_x, deck_bottom_y))

        # Right footpath area
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            painter.setPen(dashed_pen)
            # Bottom line under footpath area (dashed)
            painter.drawLine(QPointF(deck_slab_right, deck_bottom_y), 
                            QPointF(deck_right_x, deck_bottom_y))
            # Outer vertical line from footpath bottom to deck bottom level (dashed)
            painter.drawLine(QPointF(deck_right_x, fp_top_y + fp_thick_px), 
                            QPointF(deck_right_x, deck_bottom_y))

        # Draw cross bracing between girders
        if n > 1:
            girder_top_edge = base_y - girder_depth_visual
            girder_bottom_edge = base_y
            
            for i in range(n - 1):
                x1 = positions[i]
                x2 = positions[i + 1]
                
                panel_points = [
                    QPointF(x1, girder_top_edge),
                    QPointF(x2, girder_top_edge),
                    QPointF(x2, girder_bottom_edge),
                    QPointF(x1, girder_bottom_edge)
                ]
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 240, 220, 100)))
                painter.drawPolygon(QPolygonF(panel_points))
                
                line_spacing = 3
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(CROSS_BRACING_COLOR, 1.0))
                
                dx = x2 - x1
                dy = girder_bottom_edge - girder_top_edge
                length = math.sqrt(dx * dx + dy * dy)
                
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length
                    off_x = perp_x * line_spacing / 2
                    off_y = perp_y * line_spacing / 2
                    
                    painter.drawLine(QPointF(x1 + off_x, girder_top_edge + off_y), 
                                    QPointF(x2 + off_x, girder_bottom_edge + off_y))
                    painter.drawLine(QPointF(x1 - off_x, girder_top_edge - off_y), 
                                    QPointF(x2 - off_x, girder_bottom_edge - off_y))
                    
                    perp_x2 = dy / length
                    perp_y2 = dx / length
                    off_x2 = perp_x2 * line_spacing / 2
                    off_y2 = perp_y2 * line_spacing / 2
                    
                    painter.drawLine(QPointF(x2 + off_x2, girder_top_edge + off_y2), 
                                    QPointF(x1 + off_x2, girder_bottom_edge + off_y2))
                    painter.drawLine(QPointF(x2 - off_x2, girder_top_edge - off_y2), 
                                    QPointF(x1 - off_x2, girder_bottom_edge - off_y2))
                    
        # Draw girders and stiffeners
        for girder_x in positions:
            self.draw_i_section(painter, girder_x, base_y, scale, GIRDER_COLOR)
            self.draw_stiffeners(painter, girder_x, base_y, scale, STIFFENER_COLOR)

        # Draw railings
        left_railing_rect = None
        right_railing_rect = None

        if fp_config in ['left', 'both'] and left_fp_width > 0:
            railing_x = deck_left_x
            left_railing_rect = self.draw_railing_post_fixed(painter, railing_x, fp_top_y, scale, "left")
            
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            railing_x = deck_right_x - railing_outer_width_px
            right_railing_rect = self.draw_railing_post_fixed(painter, railing_x, fp_top_y, scale, "right")

        # Add dimensions
        self.add_professional_cross_section_dimensions(
            painter, deck_left_x, deck_right_x, carriageway_start_x, carriageway_end_x,
            left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y, fp_top_y,
            base_y, scale, positions, n, fp_config, left_fp_width, right_fp_width,
            left_fp_x, right_fp_x, railing_width_px, girder_depth_visual,
            median_present, median_start_x, median_end_x, median_width,
            crash_barrier_width_px, left_barrier_end_x, right_barrier_end_x
        )

        # Add hover labels
        self.add_cross_section_hover_labels(
            painter, carriageway_start_x, carriageway_end_x, left_barrier_x, right_barrier_x,
            deck_top_y, deck_bottom_y, deck_thick_px, positions, base_y, scale, n, fp_config,
            deck_left_x, deck_right_x, left_fp_width, right_fp_width, fp_top_y, fp_thick_px,
            left_fp_x, right_fp_x, left_railing_rect, right_railing_rect, railing_width_px,
            median_present, median_start_x, median_end_x, median_width, deck_slab_left, deck_slab_right,
            crash_barrier_width_px, left_barrier_end_x, right_barrier_end_x
        )



    def draw_railing_post_fixed(self, painter, x, y, scale, side):
        """Draw RCC railing with exact dimensions:
        - Height: 1100 mm
        - Outer width: 375 mm
        - Inner spacing: 275 mm
        - Base thickness: 100 mm
        """
        RAILING_HEIGHT_MM = 1100
        OUTER_WIDTH_MM = 375
        INNER_SPACING_MM = 275
        BASE_THICKNESS_MM = 100
        
        wall_thickness_mm = (OUTER_WIDTH_MM - INNER_SPACING_MM) / 2
        
        total_h = RAILING_HEIGHT_MM * scale
        outer_w = max(4, OUTER_WIDTH_MM * scale)
        inner_w = max(2, INNER_SPACING_MM * scale)
        base_h = max(3, BASE_THICKNESS_MM * scale)
        wall_t = max(1, wall_thickness_mm * scale)
        
        post_h = total_h - base_h
        
        rect_x = x
        base_bottom_y = y
        base_top_y = y - base_h
        post_top_y = y - total_h
        
        corner_radius = min(outer_w * 0.05, 4)
        
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        base_rect = QRectF(rect_x, base_top_y, outer_w, base_h)
        painter.drawRect(base_rect)
        
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        post_rect = QRectF(rect_x, post_top_y, outer_w, post_h)
        painter.drawRoundedRect(post_rect, corner_radius, corner_radius)
        
        inner_x = rect_x + wall_t
        inner_top_margin = post_h * 0.08
        inner_bottom_margin = post_h * 0.05
        inner_height = post_h - inner_top_margin - inner_bottom_margin
        
        if inner_w > 3 and inner_height > 5:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(120, 120, 120), max(1, scale)))
            
            inner_rect = QRectF(inner_x, post_top_y + inner_top_margin, inner_w, inner_height)
            painter.drawRoundedRect(inner_rect, corner_radius * 0.5, corner_radius * 0.5)
            
            n_rails = 4
            rail_spacing = inner_height / (n_rails + 1)
            rail_height = max(2, 3 * scale)
            
            painter.setBrush(QBrush(QColor(180, 180, 180)))
            painter.setPen(QPen(QColor(100, 100, 100), max(0.5, scale * 0.5)))
            
            for i in range(1, n_rails + 1):
                rail_y = post_top_y + inner_top_margin + i * rail_spacing - rail_height/2
                rail_rect = QRectF(inner_x + 2, rail_y, inner_w - 4, rail_height)
                painter.drawRect(rail_rect)
        
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        outline_margin = 2
        outline_rect = QRectF(rect_x - outline_margin,
                            post_top_y - outline_margin,
                            outer_w + 2 * outline_margin,
                            total_h + 2 * outline_margin)
        painter.drawRoundedRect(outline_rect, corner_radius + 2, corner_radius + 2)
        
        # Return bounding box with actual outer width
        return (rect_x, post_top_y, rect_x + outer_w, y, outer_w)

    def add_professional_cross_section_dimensions(self, painter, deck_left_x, deck_right_x,
                        carriageway_start_x, carriageway_end_x,
                            left_barrier_x, right_barrier_x,
                            deck_top_y, deck_bottom_y, fp_top_y,
                            base_y, scale, positions, n,
                            fp_config, left_fp_width, right_fp_width,
                            left_fp_x, right_fp_x, railing_width_px, girder_depth_visual,
                            median_present=False, median_start_x=None, median_end_x=None, median_width=1200,
                            crash_barrier_width_px=None, left_barrier_end_x=None, right_barrier_end_x=None):
        """Add organized dimension lines with extension lines - with median support"""
        
        fp_thick_px = self.params['footpath_thickness'] * scale
        deck_thick_px = self.params['deck_thickness'] * scale
        
        CRASH_BARRIER_VISUAL_WIDTH = 350.0  # BOTTOM_WIDTH
        crash_barrier_visual_px = CRASH_BARRIER_VISUAL_WIDTH * scale
        
        # Calculate barrier positions if not passed
        if crash_barrier_width_px is None:
            crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        if left_barrier_end_x is None:
            left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        if right_barrier_end_x is None:
            right_barrier_end_x = right_barrier_x + crash_barrier_width_px
        
        # Left barrier starts at left_barrier_x and extends RIGHT by crash_barrier_visual_px
        left_barrier_visual_end = left_barrier_x + crash_barrier_visual_px
        
        # Right barrier ENDS at right_barrier_end_x and extends LEFT by crash_barrier_visual_px
        right_barrier_visual_start = right_barrier_end_x - crash_barrier_visual_px
        
        # LEVEL 1: Overall Bridge Width
        y_level1 = deck_top_y - 115
        total_width_m = (deck_right_x - deck_left_x) / scale / 1000.0

        self.draw_dimension_arrow(
            painter,
            deck_left_x, y_level1,
            deck_right_x, y_level1,
            "", True,
            extension_direction='down',
            extension_end_y=fp_top_y
        )

        mid_x = (deck_left_x + deck_right_x) / 2.0
        label_text = f"Overall Bridge Width = {total_width_m:.2f} m"

        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_w = metrics.boundingRect(label_text).width()
        text_y = y_level1 - 8

        self.draw_text_with_background(
            painter,
            mid_x - text_w / 2.0,
            text_y,
            label_text,
            QColor(255, 255, 255, 240),
            QColor(0, 0, 0),
            7,
            True
        )

        # LEVEL 2: Footpath dimensions
        y_level2 = deck_top_y - 85
        
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            fp_start_x = deck_left_x + railing_width_px
            fp_end_x = left_barrier_x
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, y_level2, 
                                        fp_end_x, y_level2,
                                        f"Footpath Width = {fp_visible_m:.2f} m", True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 2c: Carriageway/Median Dimensions
        y_level2c = deck_top_y - 55
    
        actual_cw_start = left_barrier_visual_end
        actual_cw_end = right_barrier_visual_start
        
        if median_present and median_start_x is not None and median_end_x is not None:
            cw_m = self.params['carriageway_width'] / 1000
            
            # Left carriageway - starts exactly at left barrier visual end
            self.draw_dimension_arrow(painter, actual_cw_start, y_level2c, median_start_x, y_level2c,
                                    f"Carriageway = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Median dimension
            median_m = median_width / 1000
            self.draw_dimension_arrow(painter, median_start_x, y_level2c - 25, median_end_x, y_level2c - 25,
                                    f"Median = {median_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Right carriageway - ends exactly at right barrier visual start
            self.draw_dimension_arrow(painter, median_end_x, y_level2c, actual_cw_end, y_level2c,
                                    f"Carriageway = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        else:
            # Single carriageway
            cw_m = self.params['carriageway_width'] / 1000
            # From left barrier visual end to right barrier visual start
            self.draw_dimension_arrow(painter, actual_cw_start, y_level2c, actual_cw_end, y_level2c,
                                    f"Carriageway Width = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        
        # Right footpath dimension
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            fp_start_x = right_barrier_end_x
            fp_end_x = deck_right_x - railing_width_px
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, y_level2, 
                                        fp_end_x, y_level2,
                                        f"Footpath Width = {fp_visible_m:.2f} m", True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 3: Below bridge - Overhang
        y_level3 = base_y + 50
        
        if n > 0 and len(positions) > 0:
            first_girder_x = positions[0]
            overhang_m = self.params.get('deck_overhang', 1000) / 1000
            self.draw_dimension_arrow(painter, deck_left_x, y_level3, first_girder_x, y_level3,
                                    f"Overhang = {overhang_m:.2f} m", True, 
                                    extension_direction='up',
                                    extension_end_y=deck_bottom_y)
        
        # Girder spacing
        if n > 1 and len(positions) >= 2:
            y_level4 = base_y + 90
            x_left = positions[0]
            x_right = positions[1]
            
            gs_m = self.params['girder_spacing'] / 1000
            self.draw_dimension_arrow(painter, x_left, y_level4, x_right, y_level4,
                                    f"Girder Spacing = {gs_m:.2f} m", True, 
                                    extension_direction='up',
                                    extension_end_y=base_y)
        
        # FOOTPATH THICKNESS DIMENSION 
        fp_t_mm = self.params['footpath_thickness']
        
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_left_x - 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath\nThickness = {fp_t_mm:.0f} mm", 'left')
        
        if fp_config == 'right' and right_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_right_x + 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath\nThickness = {fp_t_mm:.0f} mm", 'right')
        
        # DECK THICKNESS DIMENSION - position adjusted for median
        deck_t_mm = self.params['deck_thickness']
        deck_slab_left = left_barrier_x
        deck_slab_right = right_barrier_end_x
        
        # If median is present, move deck thickness dimension to the left carriageway area
        if median_present and median_start_x is not None:
            # Position in the left carriageway (between left barrier and median)
            deck_center_x = (left_barrier_visual_end + median_start_x) / 2
        else:
            deck_center_x = (deck_slab_left + deck_slab_right) / 2

        if deck_thick_px > 5:
            painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            painter.drawLine(QPointF(deck_center_x, deck_top_y), QPointF(deck_center_x, deck_bottom_y))
            
            arrow_size = 4
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            
            top_arrow = [
                QPointF(deck_center_x, deck_top_y),
                QPointF(deck_center_x - arrow_size/2, deck_top_y + arrow_size),
                QPointF(deck_center_x + arrow_size/2, deck_top_y + arrow_size)
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(deck_center_x, deck_bottom_y),
                QPointF(deck_center_x - arrow_size/2, deck_bottom_y - arrow_size),
                QPointF(deck_center_x + arrow_size/2, deck_bottom_y - arrow_size)
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            tick_len = 4
            painter.drawLine(QPointF(deck_center_x - tick_len, deck_top_y), 
                            QPointF(deck_center_x + tick_len, deck_top_y))
            painter.drawLine(QPointF(deck_center_x - tick_len, deck_bottom_y), 
                            QPointF(deck_center_x + tick_len, deck_bottom_y))
            
            # Renamed to "Deck Thickness"
            text = f"Deck Thickness = {deck_t_mm:.0f} mm"
            font = QFont('Arial', 7, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            text_x = deck_center_x - text_width / 2
            text_y = deck_top_y - 8
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)
    def add_cross_section_hover_labels(self, painter, carriageway_start_x, carriageway_end_x,
                    left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y,
                    deck_thick_px, positions, base_y, scale, n, fp_config,
                    deck_left_x, deck_right_x, left_fp_width, 
                    right_fp_width, fp_top_y, fp_thick_px,
                    left_fp_x, right_fp_x, left_railing_rect, right_railing_rect,
                    railing_width_px, median_present, median_start_x, median_end_x, median_width,
                    deck_slab_left, deck_slab_right,
                    crash_barrier_width_px=None, left_barrier_end_x=None, right_barrier_end_x=None):
        """Hover labels with specific positioning requirements"""
        
        # Calculate if not passed
        if crash_barrier_width_px is None:
            crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        if left_barrier_end_x is None:
            left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        if right_barrier_end_x is None:
            right_barrier_end_x = right_barrier_x + crash_barrier_width_px
        
        cb_height = self.crash_barrier['height'] * scale
        visual = self.girder_visual_scale
        girder_depth_visual = self.girder['depth'] * scale * visual['depth']
        bf = self.girder['flange_width'] * scale * visual['flange_width']
        
        # Common label line Y position (below girders)
        label_line_y = base_y + 80
        
        components = []
        
        # Deck slab - straight line below girder
        deck_rect = QRectF(deck_slab_left, deck_top_y, deck_slab_right - deck_slab_left, deck_thick_px)
        deck_center_x = (deck_slab_left + deck_slab_right) / 2
        components.append((deck_rect, "Deck", deck_center_x, deck_bottom_y, 'straight_line', None))
        
        # Left crash barrier - text on top of figure
        left_cb_rect = QRectF(left_barrier_x, deck_top_y - cb_height,
                            crash_barrier_width_px, cb_height)
        left_cb_center_x = left_barrier_x + crash_barrier_width_px / 2
        left_cb_top_y = deck_top_y - cb_height
        components.append((left_cb_rect, "Crash Barrier", left_cb_center_x, left_cb_top_y, 'on_figure_top', None))
        
        # Right crash barrier - text on top of figure
        right_cb_rect = QRectF(right_barrier_x, deck_top_y - cb_height,
                            crash_barrier_width_px, cb_height)
        right_cb_center_x = right_barrier_x + crash_barrier_width_px / 2
        right_cb_top_y = deck_top_y - cb_height
        components.append((right_cb_rect, "Crash Barrier", right_cb_center_x, right_cb_top_y, 'on_figure_top', None))
        
        # Left footpath - tilted line towards left
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            left_fp_rect = QRectF(left_fp_x + railing_width_px, fp_top_y, 
                                left_fp_width * scale - railing_width_px, fp_thick_px)
            fp_center_x = (left_fp_x + railing_width_px + left_barrier_x) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            components.append((left_fp_rect, "Footpath", fp_center_x, fp_center_y, 'tilted_line_left', None))
        
        # Right footpath - straight line same level as deck
        if fp_config in ['right', 'both'] and right_fp_width > 0 and fp_thick_px > 5:
            # Right footpath starts at right_barrier_end_x and ends at deck_right_x
            right_fp_rect = QRectF(right_barrier_end_x, fp_top_y,
                                deck_right_x - right_barrier_end_x - railing_width_px, fp_thick_px)
            fp_center_x = (right_barrier_end_x + deck_right_x - railing_width_px) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            components.append((right_fp_rect, "Footpath", fp_center_x, fp_center_y, 'straight_line', None))
        
        # Left railing - text on top of figure
        if left_railing_rect is not None:
            railing_rect = QRectF(left_railing_rect[0], left_railing_rect[1],
                                left_railing_rect[4], left_railing_rect[3] - left_railing_rect[1])
            railing_center_x = left_railing_rect[0] + left_railing_rect[4] / 2
            railing_top_y = left_railing_rect[1]
            components.append((railing_rect, "Railing", railing_center_x, railing_top_y, 'on_figure_top', None))
        
        # Right railing - text on top of figure
        if right_railing_rect is not None:
            railing_rect = QRectF(right_railing_rect[0], right_railing_rect[1],
                                right_railing_rect[4], right_railing_rect[3] - right_railing_rect[1])
            railing_center_x = right_railing_rect[0] + right_railing_rect[4] / 2
            railing_top_y = right_railing_rect[1]
            components.append((railing_rect, "Railing", railing_center_x, railing_top_y, 'on_figure_top', None))
        
        # Median barriers - straight line same level as deck
        if median_present and median_start_x is not None:
            median_rect = QRectF(median_start_x, deck_top_y - cb_height,
                                median_end_x - median_start_x, cb_height)
            median_center_x = (median_start_x + median_end_x) / 2
            components.append((median_rect, "Median",
                            median_center_x, deck_bottom_y, 'straight_line', None))
        
        # Girders with stiffeners - pointer 50 below
        for i, girder_x in enumerate(positions):
            stiff_w = self.stiffener['width'] * scale * visual['flange_width']
            tw = self.girder['web_thickness'] * scale * visual['web_thickness']
            total_width = bf + 2 * stiff_w
            girder_rect = QRectF(girder_x - total_width/2, base_y - girder_depth_visual, 
                                total_width, girder_depth_visual)
            components.append((girder_rect, "Girder",
                            girder_x, base_y - girder_depth_visual / 2, 'lower_pointer', None))
        
        # Cross bracing zones - pointer 50 below
        if n > 1:
            for i in range(n - 1):
                x1 = positions[i] + bf/2
                x2 = positions[i + 1] - bf/2
                if x2 > x1:
                    bracing_rect = QRectF(x1, base_y - girder_depth_visual, x2 - x1, girder_depth_visual)
                    center_x = (x1 + x2) / 2
                    components.append((bracing_rect, "Cross Bracing",
                                    center_x, base_y - girder_depth_visual / 2, 'lower_pointer', None))
        
        # Register all for hover detection
        for rect, name, tx, ty, ltype, extra in components:
            self.hover_labels.append((rect, name, QColor(255, 255, 255, 240), QColor(60, 60, 60)))
        
        # Draw label only for hovered component
        if self.hovered_label_index >= 0 and self.hovered_label_index < len(components):
            rect, name, target_x, target_y, label_type, extra = components[self.hovered_label_index]
            
            if label_type == 'on_figure_top':
                font = QFont('Arial', 7, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                text_height = metrics.height()
                
                text_x = target_x - text_width / 2
                text_y = target_y - 5
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 220), QColor(60, 60, 60), 7, True)
            
            elif label_type == 'straight_line':
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(target_x, label_line_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 7, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = target_x - text_width / 2
                text_y = label_line_y + 12
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 240), QColor(60, 60, 60), 7, True)
            
            elif label_type == 'tilted_line_left':
                label_x = target_x - 80
                label_y = label_line_y
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(label_x, label_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 7, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = label_x - text_width - 5
                text_y = label_y + 4
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 240), QColor(60, 60, 60), 7, True)
            
            elif label_type == 'lower_pointer':
                label_y = target_y + 50
                
                if target_x < self.width() / 2:
                    label_x = target_x + 40
                else:
                    label_x = target_x - 40
                
                self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                            name, QColor(60, 60, 60), QColor(120, 120, 120))

    def draw_vertical_dimension_with_arrow(self, painter, x, y1, y2, text, side='left'):
        """Draw vertical dimension with arrow and text"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Main vertical line
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))
        
        tick_len = 4
        painter.drawLine(QPointF(x - tick_len, y1), QPointF(x + tick_len, y1))
        painter.drawLine(QPointF(x - tick_len, y2), QPointF(x + tick_len, y2))
        
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        top_arrow = [
            QPointF(x, y1),
            QPointF(x - arrow_size/2, y1 + arrow_size),
            QPointF(x + arrow_size/2, y1 + arrow_size)
        ]
        painter.drawPolygon(QPolygonF(top_arrow))
        
        bottom_arrow = [
            QPointF(x, y2),
            QPointF(x - arrow_size/2, y2 - arrow_size),
            QPointF(x + arrow_size/2, y2 - arrow_size)
        ]
        painter.drawPolygon(QPolygonF(bottom_arrow))
        
        # TEXT PART (multi-line)
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        
        # Split into lines using \n
        lines = text.split('\n')
        line_height = metrics.height()
        max_width = max(metrics.boundingRect(line).width() for line in lines)
        total_height = line_height * len(lines)
        
        # Center vertically between y1 & y2
        center_y = (y1 + y2) / 2.0
        
        # First baseline y (use ascent to keep text nicely placed)
        first_baseline_y = center_y - total_height / 2.0 + metrics.ascent()
        
        # X placement left or right
        if side == 'left':
            text_x = x - max_width - 8
        else:
            text_x = x + 8
        
        # Background rect
        margin = 2
        bg_rect = QRectF(
            text_x - margin,
            center_y - total_height / 2.0 - margin,
            max_width + 2 * margin,
            total_height + 2 * margin
        )
        
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawRect(bg_rect)
        painter.restore()
        
        # Draw each line
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        for i, line in enumerate(lines):
            painter.drawText(
                QPointF(text_x, first_baseline_y + i * line_height),
                line
            )

    def draw_i_section(self, painter, x, base_y, scale, girder_color):
        """Draw I-section girder"""
        visual = self.girder_visual_scale
        d = self.girder['depth'] * scale * visual['depth']
        bf = self.girder['flange_width'] * scale * visual['flange_width']
        tf = self.girder['flange_thickness'] * scale * visual['flange_thickness']
        tw = self.girder['web_thickness'] * scale * visual['web_thickness']
        
        painter.setBrush(QBrush(girder_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        
        painter.drawRect(QRectF(x - bf/2, base_y - tf, bf, tf))
        web_height = d - 2*tf
        painter.drawRect(QRectF(x - tw/2, base_y - d + tf, tw, web_height))
        painter.drawRect(QRectF(x - bf/2, base_y - d, bf, tf))
        
    def draw_stiffeners(self, painter, x, base_y, scale, stiffener_color):
        """Draw vertical stiffeners"""
        visual = self.girder_visual_scale
        
        stiff_w = self.stiffener['width'] * scale * visual['flange_width']
        stiff_h = self.stiffener['height'] * scale * visual['depth']
        
        tw = self.girder['web_thickness'] * scale * visual['web_thickness']
        flange_thick_visual = self.girder['flange_thickness'] * scale * visual['flange_thickness']
        girder_depth_visual = self.girder['depth'] * scale * visual['depth']
        
        painter.setBrush(QBrush(stiffener_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        stiff_top_y = base_y - girder_depth_visual + flange_thick_visual
        
        painter.drawRect(QRectF(x - tw/2 - stiff_w, stiff_top_y, stiff_w, stiff_h))
        painter.drawRect(QRectF(x + tw/2, stiff_top_y, stiff_w, stiff_h))

    def draw_crash_barrier(self, painter, x, y, scale, side='left'):
        """Draw RCC crash barrier matching the exact irc diamentions."""
        
        # DIMENSIONS (in mm)
        TOTAL_HEIGHT = 900.0
        TOP_WIDTH = 175.0
        BOTTOM_WIDTH = 350.0
        BASE_VERTICAL = 100.0
        
        # Scale everything
        h = TOTAL_HEIGHT * scale
        top_w = TOP_WIDTH * scale
        bottom_w = BOTTOM_WIDTH * scale
        base_v = BASE_VERTICAL * scale
        
        # Key Y positions (from deck going up, so negative)
        y_bottom = y
        y_base_top = y - base_v
        y_mid = y - (1000 - 650) * scale
        y_top = y - h
        
        # Offsets 
        right_at_mid = (400 - 150) * scale   # 250 * scale
        left_at_top = (200 - 150) * scale    # 50 * scale
        right_at_top = (375 - 150) * scale   # 225 * scale
        
        if side == 'left':
            # Left barrier: x is the LEFT edge (where barrier starts)
            # Barrier extends to the RIGHT from x
            
            p0 = QPointF(x, y_bottom)                          # bottom-left
            p1 = QPointF(x + bottom_w, y_bottom)               # bottom-right
            p2 = QPointF(x + bottom_w, y_base_top)             # right after base
            p3 = QPointF(x + right_at_mid, y_mid)              # right at middle
            p4 = QPointF(x + right_at_top, y_top)              # top-right
            p5 = QPointF(x + left_at_top, y_top)               # top-left
            p6 = QPointF(x, y_base_top)                        # left after base
            
            points = [p0, p1, p2, p3, p4, p5, p6]
            
        else:  # right side
            # Right barrier: x is the RIGHT edge (where barrier ends)
            # Barrier extends to the LEFT from x
            # The shape is mirrored so front (sloped side) faces left toward carriageway
            
            x_right = x                    # Right edge of barrier
            x_left = x - bottom_w          # Left edge of barrier at bottom
            
            p0 = QPointF(x_left, y_bottom)                              # bottom-left
            p1 = QPointF(x_right, y_bottom)                             # bottom-right
            p2 = QPointF(x_right, y_base_top)                           # right after base
            p3 = QPointF(x_right - left_at_top, y_top)                  # top-right (mirrored)
            p4 = QPointF(x_right - right_at_top, y_top)                 # top-left (mirrored)
            p5 = QPointF(x_right - right_at_mid, y_mid)                 # left at middle (mirrored)
            p6 = QPointF(x_left, y_base_top)                            # left after base
            
            points = [p0, p1, p2, p3, p4, p5, p6]
        
        # Draw the barrier
        painter.setBrush(QBrush(QColor(255, 210, 160)))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points))

    def draw_top_view(self, painter):
        """Draw top view with hover labels"""
        # Clear top view hover zones
        self.top_view_hover_zones = []
        
        # Define colors
        GIRDER_COLOR = QColor(0, 100, 0)
        CROSS_BRACING_COLOR = QColor(255, 140, 0)
        END_DIAPHRAGM_COLOR = QColor(139, 69, 19)
        
        # Highlight colors 
        GIRDER_HIGHLIGHT = QColor(0, 200, 0)
        CROSS_BRACING_HIGHLIGHT = QColor(255, 200, 50)
        END_DIAPHRAGM_HIGHLIGHT = QColor(200, 120, 50)
        BEARING_HIGHLIGHT = QColor(255, 100, 100)
        
        width = self.width()
        height = self.height()

        margin = 120
        available_width = width - 2 * margin
        available_height = height - 2 * margin - 180

        n = self.params['num_girders']
        
        if n > 1:
            total_girder_width = (n - 1) * self.params['girder_spacing'] + 2 * self.params['deck_overhang']
        else:
            total_girder_width = 2 * self.params['deck_overhang']
        
        total_model_width = total_girder_width

        span_scale = available_width / max(self.params['span_length'], 1.0)
        width_scale = available_height / max(total_model_width, 1.0)
        scale = min(span_scale, width_scale)

        center_x = width / 2
        center_y = height / 2 - 40

        title_text = "TOP VIEW - Girder and Cross Bracing Layout"
        self.draw_text_with_background(painter, 30, 35, title_text,
                                QColor(255, 245, 230, 250), QColor(0, 0, 100), 11, True)

        # FIX: Negate the skew angle
        skew_rad = math.radians(-self.params['skew_angle'])  # CHANGED: Added negative sign
        
        girder_positions_y = []
        
        if n > 1:
            spacing_px = self.params['girder_spacing'] * scale
            total_width_px = (n - 1) * spacing_px
            start_y = center_y - total_width_px / 2
            for i in range(n):
                y_pos = start_y + i * spacing_px
                girder_positions_y.append(y_pos)
        else:
            girder_positions_y = [center_y]

        span_length_px = self.params['span_length'] * scale
        start_x_base = center_x - span_length_px / 2
        end_x_base = center_x + span_length_px / 2

        # Check hover states
        girder_hovered = self.hovered_top_view_element == 'girder'
        bracing_hovered = self.hovered_top_view_element == 'cross_bracing'
        diaphragm_hovered = self.hovered_top_view_element == 'end_diaphragm'
        bearing_hovered = self.hovered_top_view_element == 'bearing'

        # Draw girders
        girder_color = GIRDER_HIGHLIGHT if girder_hovered else GIRDER_COLOR
        girder_width = 4.5 if girder_hovered else 2.5
        painter.setPen(QPen(girder_color, girder_width))
        
        girder_lines = []
        for y_pos in girder_positions_y:
            y_offset_from_first = y_pos - girder_positions_y[0]
            x_offset = y_offset_from_first * math.tan(skew_rad)
            
            x1 = start_x_base + x_offset
            x2 = end_x_base + x_offset
            
            painter.drawLine(QPointF(x1, y_pos), QPointF(x2, y_pos))
            girder_lines.append({'y': y_pos, 'x1': x1, 'x2': x2})
            
            # Register hover zone with larger padding for easier selection
            hover_padding = 15
            self.top_view_hover_zones.append((
                QRectF(x1, y_pos - hover_padding, x2 - x1, hover_padding * 2), 'girder'
            ))

        # Calculate bearing line positions
        bearing_gap_px = max(30, 0.3 * self.params['girder_spacing'] * scale)

        top_extent = girder_positions_y[0] - bearing_gap_px
        bottom_extent = girder_positions_y[-1] + bearing_gap_px if n > 1 else girder_positions_y[0] + bearing_gap_px

        left_bearing_base_x = start_x_base
        right_bearing_base_x = end_x_base

        left_top_x = left_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        left_bottom_x = left_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        right_top_x = right_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        right_bottom_x = right_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        # Draw END DIAPHRAGMS
        if n > 1:
            diaphragm_color = END_DIAPHRAGM_HIGHLIGHT if diaphragm_hovered else END_DIAPHRAGM_COLOR
            diaphragm_width = 4.0 if diaphragm_hovered else 3.0
            
            # Use solid line with slight offset for double-line effect
            painter.setBrush(Qt.NoBrush)
            
            # Left end diaphragm
            for i in range(len(girder_positions_y) - 1):
                y1 = girder_positions_y[i]
                y2 = girder_positions_y[i + 1]
                
                y1_offset = y1 - girder_positions_y[0]
                y2_offset = y2 - girder_positions_y[0]
                
                x1 = left_bearing_base_x + y1_offset * math.tan(skew_rad)
                x2 = left_bearing_base_x + y2_offset * math.tan(skew_rad)
                
                # Draw double solid lines for end diaphragm
                line_offset = 2
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length * line_offset
                    perp_y = dx / length * line_offset
                    
                    painter.setPen(QPen(diaphragm_color, diaphragm_width, Qt.SolidLine))
                    painter.drawLine(QPointF(x1 + perp_x, y1 + perp_y), QPointF(x2 + perp_x, y2 + perp_y))
                    painter.drawLine(QPointF(x1 - perp_x, y1 - perp_y), QPointF(x2 - perp_x, y2 - perp_y))
                
                
                # Register hover zone with larger padding
                hover_padding = 20
                min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                min_y, max_y = min(y1, y2), max(y1, y2)
                self.top_view_hover_zones.append((
                    QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'end_diaphragm'
                ))
            
            # Right end diaphragm
            for i in range(len(girder_positions_y) - 1):
                y1 = girder_positions_y[i]
                y2 = girder_positions_y[i + 1]
                
                y1_offset = y1 - girder_positions_y[0]
                y2_offset = y2 - girder_positions_y[0]
                
                x1 = right_bearing_base_x + y1_offset * math.tan(skew_rad)
                x2 = right_bearing_base_x + y2_offset * math.tan(skew_rad)
                
                # Draw double solid lines
                line_offset = 2
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length * line_offset
                    perp_y = dx / length * line_offset
                    
                    painter.setPen(QPen(diaphragm_color, diaphragm_width, Qt.SolidLine))
                    painter.drawLine(QPointF(x1 + perp_x, y1 + perp_y), QPointF(x2 + perp_x, y2 + perp_y))
                    painter.drawLine(QPointF(x1 - perp_x, y1 - perp_y), QPointF(x2 - perp_x, y2 - perp_y))
                
                
                hover_padding = 20
                min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                min_y, max_y = min(y1, y2), max(y1, y2)
                self.top_view_hover_zones.append((
                    QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'end_diaphragm'
                ))

        # Draw center line of bearings
        bearing_color = BEARING_HIGHLIGHT if bearing_hovered else QColor(255, 0, 0)
        bearing_width = 2.5 if bearing_hovered else 1.5
        
        pen = QPen(bearing_color, bearing_width, Qt.CustomDashLine)
        pen.setDashPattern([8, 8])
        painter.setPen(pen)
        
        painter.drawLine(QPointF(left_top_x, top_extent), 
                        QPointF(left_bottom_x, bottom_extent))
        painter.drawLine(QPointF(right_top_x, top_extent), 
                        QPointF(right_bottom_x, bottom_extent))
        
        # Register bearing hover zones with larger padding
        hover_padding = 20
        self.top_view_hover_zones.append((
            QRectF(min(left_top_x, left_bottom_x) - hover_padding, top_extent, 
                abs(left_top_x - left_bottom_x) + hover_padding * 2, bottom_extent - top_extent), 'bearing'
        ))
        self.top_view_hover_zones.append((
            QRectF(min(right_top_x, right_bottom_x) - hover_padding, top_extent,
                abs(right_top_x - right_bottom_x) + hover_padding * 2, bottom_extent - top_extent), 'bearing'
        ))

        # Cross bracing
        bracing_positions_x = []
        if self.params['cross_bracing_spacing'] > 0 and n > 1:
            span_length = self.params['span_length']
            bracing_spacing = self.params['cross_bracing_spacing']
            
            num_braces = max(1, int(math.ceil(span_length / bracing_spacing)))
            actual_spacing_px = span_length_px / num_braces
            
            bracing_color = CROSS_BRACING_HIGHLIGHT if bracing_hovered else CROSS_BRACING_COLOR
            bracing_width = 3.5 if bracing_hovered else 1.8
            painter.setPen(QPen(bracing_color, bracing_width))
            
            for section in range(1, num_braces):
                brace_x_base = start_x_base + section * actual_spacing_px
                
                for i in range(len(girder_positions_y) - 1):
                    y1 = girder_positions_y[i]
                    y2 = girder_positions_y[i + 1]
                    
                    y1_offset = y1 - girder_positions_y[0]
                    y2_offset = y2 - girder_positions_y[0]
                    
                    x1 = brace_x_base + y1_offset * math.tan(skew_rad)
                    x2 = brace_x_base + y2_offset * math.tan(skew_rad)
                    
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    
                    # Register hover zone with larger padding
                    hover_padding = 15
                    min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                    min_y, max_y = min(y1, y2), max(y1, y2)
                    self.top_view_hover_zones.append((
                        QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'cross_bracing'
                    ))
                    
                    if i == 0:
                        bracing_positions_x.append(brace_x_base)

        # Draw skew angle indicator
        if abs(self.params['skew_angle']) > 0.1:
            self.draw_skew_angle_indicator(painter, girder_lines[0]['x1'], girder_positions_y[0], 
                                        skew_rad, scale, left_bearing_base_x)

        # Add dimensions (always visible) and hover labels (only on hover)
        self.add_clean_top_view_dimensions(
            painter, girder_lines, girder_positions_y, scale, n, bracing_positions_x,
            skew_rad, start_x_base, end_x_base, left_bearing_base_x, right_bearing_base_x,
            top_extent, bottom_extent, left_top_x, right_top_x,
            GIRDER_COLOR, CROSS_BRACING_COLOR, END_DIAPHRAGM_COLOR
        )

        self.add_clean_top_view_notes(painter, height)


    def draw_skew_angle_indicator(self, painter, girder_start_x, girder_y, skew_rad, scale, bearing_x):
        """Draw skew angle indicator with arc and proper sign display"""
        skew_deg = self.params['skew_angle']  # CHANGED
        
        if abs(skew_deg) < 0.1:
            return
        
        # Reference point at the first girder on the bearing line
        ref_x = bearing_x
        ref_y = girder_y
        
        arc_radius = 50
        
        # Draw vertical reference line (what 0 skew would look like)
        painter.setPen(QPen(QColor(100, 100, 100), 1.5, Qt.DashLine))
        painter.drawLine(QPointF(ref_x, ref_y), QPointF(ref_x, ref_y - arc_radius - 20))
        
        # Draw the actual skewed bearing line direction
        # The skew causes the bearing line to rotate, so we show that angle
        skewed_end_x = ref_x - arc_radius * math.sin(skew_rad)
        skewed_end_y = ref_y - arc_radius * math.cos(skew_rad)
        
        painter.setPen(QPen(QColor(0, 100, 200), 2.0))
        painter.drawLine(QPointF(ref_x, ref_y), QPointF(skewed_end_x, skewed_end_y))
        
        # Draw arc from vertical to skewed line
        # Qt uses 1/16 degree units, angles measured counter-clockwise from 3 o'clock
        # 90 degrees (in Qt) = pointing up
        arc_rect = QRectF(ref_x - arc_radius, ref_y - arc_radius, arc_radius * 2, arc_radius * 2)
        
        # Start angle is 90 degrees (pointing up/vertical)
        start_angle_deg = 90
        # Span angle is the skew angle (use original input value for arc direction)
        span_angle_deg = skew_deg
        
        painter.setPen(QPen(QColor(0, 100, 200), 2.5))
        painter.drawArc(arc_rect, int(start_angle_deg * 16), int(-span_angle_deg * 16))
        
        # Draw arrow at end of arc
        arrow_angle_rad = math.radians(90 - skew_deg)
        arrow_x = ref_x + arc_radius * math.cos(arrow_angle_rad)
        arrow_y = ref_y - arc_radius * math.sin(arrow_angle_rad)
        
        # Small arrow head at arc end
        arrow_size = 6
        # Tangent direction at arc end (perpendicular to radius)
        tangent_angle = arrow_angle_rad + (math.pi/2 if skew_deg > 0 else -math.pi/2)
        
        arrow_points = [
            QPointF(arrow_x, arrow_y),
            QPointF(arrow_x - arrow_size * math.cos(tangent_angle - 0.4),
                    arrow_y + arrow_size * math.sin(tangent_angle - 0.4)),
            QPointF(arrow_x - arrow_size * math.cos(tangent_angle + 0.4),
                    arrow_y + arrow_size * math.sin(tangent_angle + 0.4))
        ]
        painter.setBrush(QBrush(QColor(0, 100, 200)))
        painter.drawPolygon(QPolygonF(arrow_points))
        
        # Add angle label with proper sign - using ORIGINAL input value
        # Position label near the arc
        label_radius = arc_radius + 25
        label_angle_rad = math.radians(90 - skew_deg/2)  # Middle of the arc
        label_x = ref_x + label_radius * math.cos(label_angle_rad)
        label_y = ref_y - label_radius * math.sin(label_angle_rad)
        
        # Format with explicit sign (+ or -) - showing ORIGINAL input value
        if skew_deg >= 0:
            angle_text = f"Skew = +{abs(skew_deg):.1f}°"
        else:
            angle_text = f"Skew = {skew_deg:.1f}°"
        
        # Adjust label position based on skew direction
        if skew_deg > 0:
            label_x -= 10
        else:
            label_x -= 70
        
        self.draw_text_with_background(painter, label_x, label_y,
                                    angle_text, QColor(230, 240, 255, 250),
                                    QColor(0, 100, 200), 8, True)

    def add_clean_top_view_dimensions(self, painter, girder_lines, girder_positions_y,
                            scale, n, bracing_positions, skew_rad,
                            start_x_base, end_x_base, left_bearing_base_x, right_bearing_base_x,
                            top_extent, bottom_extent, left_top_x, right_top_x,
                            girder_color, cross_bracing_color, end_diaphragm_color):
        """Add dimensions (always visible) and hover labels (only on hover)"""
        
        if not girder_lines:
            return
        
        # Get last girder for reference
        last_girder_idx = len(girder_lines) - 1
        last_girder = girder_lines[last_girder_idx]
        last_girder_y = last_girder['y']
        
        y_offset_last = last_girder_y - girder_positions_y[0]
        x_offset_last = y_offset_last * math.tan(skew_rad)
        
        dim_y_base = last_girder_y + 50
        
        # SPAN LENGTH dimension (always visible)
        dim_y1 = dim_y_base
        x1_span = last_girder['x1']
        x2_span = last_girder['x2']
        span_m = self.params['span_length'] / 1000
        
        self.draw_dimension_arrow_with_extensions_up(
            painter, x1_span, dim_y1, x2_span, dim_y1,
            f"Span Length = {span_m:.1f} m", last_girder_y
        )

        # BRACING SPACING dimension (always visible)
        if self.params['cross_bracing_spacing'] > 0 and len(bracing_positions) > 1:
            dim_y2 = dim_y_base + 35
            cb_spacing_m = self.params['cross_bracing_spacing'] / 1000
            
            x1_brace = bracing_positions[0] + x_offset_last
            x2_brace = bracing_positions[1] + x_offset_last
            
            self.draw_dimension_arrow_with_extensions_up(
                painter, x1_brace, dim_y2, x2_brace, dim_y2,
                f"Bracing Spacing = {cb_spacing_m:.2f} m", last_girder_y
            )

        # GIRDER SPACING dimension (always visible)
        if n > 1:
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1_at_end = end_x_base + y1_offset * math.tan(skew_rad) + 30
            x2_at_end = end_x_base + y2_offset * math.tan(skew_rad) + 30
            
            gs_m = self.params['girder_spacing'] / 1000

            # just the skewed dimension line + arrows, no text on it
            self.draw_skewed_dimension_arrow(
                painter, x1_at_end, y1, x2_at_end, y2,
                "",  # no inline text
                skew_rad
            )
            
            # Girder Spacing label + value (3 lines)
            label_x = max(x1_at_end, x2_at_end) + 25
            label_y = (y1 + y2) / 2

            label_text = f"Girder\nSpacing\n= {gs_m:.2f} m"

            self.draw_text_with_background(
                painter, label_x, label_y,
                label_text,
                QColor(255, 255, 255, 250),
                QColor(0, 100, 0), 7, True
            )

        # CL OF BEARING labels - ALWAYS VISIBLE (moved outside hover condition)
        label_y_bearing = top_extent - 15
        
        left_label_x = left_top_x - 80
        right_label_x = right_top_x - 45
        
        self.draw_text_with_background(painter, left_label_x, label_y_bearing,
                                    "CL of Bearing", QColor(255, 255, 255, 250),
                                    QColor(200, 0, 0), 7, True)
        
        self.draw_text_with_background(painter, right_label_x, label_y_bearing,
                                    "CL of Bearing", QColor(255, 255, 255, 250),
                                    QColor(200, 0, 0), 7, True)

        # HOVER LABELS (only shown when hovered) 
        
        # 1. GIRDER label - show only when girder is hovered
        if len(girder_lines) > 0 and self.hovered_top_view_element == 'girder':
            first_girder = girder_lines[0]
            target_x = (first_girder['x1'] + first_girder['x2']) / 2
            target_y = first_girder['y']
            
            label_x = target_x
            label_y = target_y - 60
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "Girder", girder_color, QColor(0, 100, 0))

        # 2. CROSS BRACING label - show only when cross bracing is hovered
        if n > 1 and len(bracing_positions) > 0 and self.hovered_top_view_element == 'cross_bracing':
            brace_index = min(6, len(bracing_positions) - 1)
            brace_x_base = bracing_positions[brace_index]
            
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1 = brace_x_base + y1_offset * math.tan(skew_rad)
            x2 = brace_x_base + y2_offset * math.tan(skew_rad)
            
            target_x = (x1 + x2) / 2
            target_y = (y1 + y2) / 2
            
            label_offset = 60
            label_x = target_x - label_offset * math.sin(skew_rad)
            label_y = target_y - label_offset
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "Cross Bracing", cross_bracing_color, QColor(200, 100, 0))
        
        # 3. END DIAPHRAGM label - show only when end diaphragm is hovered
        if n > 1 and len(girder_positions_y) >= 2 and self.hovered_top_view_element == 'end_diaphragm':
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1 = left_bearing_base_x + y1_offset * math.tan(skew_rad)
            x2 = left_bearing_base_x + y2_offset * math.tan(skew_rad)
            
            target_x = (x1 + x2) / 2
            target_y = (y1 + y2) / 2
            
            label_offset = 50
            label_x = target_x - label_offset - 10
            label_y = target_y + 20
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "End Diaphragm", end_diaphragm_color, QColor(139, 69, 19))

    def draw_dimension_arrow_with_extensions_up(self, painter, x1, y1, x2, y2, text, girder_y):
        """Dimension line with arrows and extension lines going UP to girder level (dimension below)"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Draw main dimension line
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw extension lines going UP to girder (y1 > girder_y since dimension is below)
        painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
        painter.drawLine(QPointF(x1, y1), QPointF(x1, girder_y))
        painter.drawLine(QPointF(x2, y2), QPointF(x2, girder_y))
        
        # Reset pen for arrows
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Draw end ticks
        ext_len = 6
        painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
        painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
        
        # Draw arrows
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        left_arrow = [
            QPointF(x1, y1),
            QPointF(x1 + arrow_size, y1 - arrow_size/2),
            QPointF(x1 + arrow_size, y1 + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(left_arrow))
        
        right_arrow = [
            QPointF(x2, y2),
            QPointF(x2 - arrow_size, y2 - arrow_size/2),
            QPointF(x2 - arrow_size, y2 + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(right_arrow))
        
        # Draw text BELOW the dimension line (above in terms of value since we add to y)
        text_x = (x1 + x2) / 2
        text_y = y1 + 15  # Below the dimension line
        
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        
        self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                    QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)


    def draw_skewed_dimension_arrow(self, painter, x1, y1, x2, y2, text, skew_rad):
        """Draw a dimension arrow that follows skew angle with horizontal text"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        nx = dx / length
        ny = dy / length
        
        px = -ny
        py = nx
        
        tick_len = 5
        
        painter.drawLine(QPointF(x1 - px * tick_len, y1 - py * tick_len),
                        QPointF(x1 + px * tick_len, y1 + py * tick_len))
        painter.drawLine(QPointF(x2 - px * tick_len, y2 - py * tick_len),
                        QPointF(x2 + px * tick_len, y2 + py * tick_len))
        
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        angle1 = math.atan2(dy, dx)
        arrow1 = [
            QPointF(x1, y1),
            QPointF(x1 + arrow_size * math.cos(angle1 - 2.5), y1 + arrow_size * math.sin(angle1 - 2.5)),
            QPointF(x1 + arrow_size * math.cos(angle1 + 2.5), y1 + arrow_size * math.sin(angle1 + 2.5))
        ]
        painter.drawPolygon(QPolygonF(arrow1))
        
        angle2 = math.atan2(-dy, -dx)
        arrow2 = [
            QPointF(x2, y2),
            QPointF(x2 + arrow_size * math.cos(angle2 - 2.5), y2 + arrow_size * math.sin(angle2 - 2.5)),
            QPointF(x2 + arrow_size * math.cos(angle2 + 2.5), y2 + arrow_size * math.sin(angle2 + 2.5))
        ]
        painter.drawPolygon(QPolygonF(arrow2))
        
        # Draw text horizontally at midpoint, offset to the right
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        text_x = mid_x + 8
        text_y = mid_y + 4
        
        self.draw_text_with_background(painter, text_x, text_y, text,
                                    QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)

    def add_clean_top_view_notes(self, painter, height):
        """Add professional notes"""
        notes_y = height - 160
        
        self.draw_text_with_background(painter, 30, notes_y + 5,
                                    "NOTES:", QColor(240, 245, 250, 250),
                                    QColor(0, 0, 0), 9, True)
        
        notes = [
            f"1. Green lines: Girders (Qty = {self.params['num_girders']})",
            f"2. Orange lines: Cross bracing (ISA 100×100×8)",
            f"3. Brown lines: End diaphragms at bearing locations",
            f"4. Red dashed: Centerline of bearings",
            f"5. Skew angle: {self.params['skew_angle']:.1f}°",
            f"6. All dimensions in meters",
        ]
        
        painter.setFont(QFont('Arial', 7))
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        for i, note in enumerate(notes):
            note_y = notes_y + 22 + i * 13
            painter.drawText(32, note_y, note)


class BridgeDesignGUI(QMainWindow):
    """Main window for bridge design application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steel Girder Bridge CAD")

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        avail_width = available.width() if available else 1400
        avail_height = available.height() if available else 900

        default_width = min(1400, max(1000, avail_width - 120))
        default_height = min(900, max(700, avail_height - 120))

        self.resize(default_width, default_height)
        self.setMinimumSize(900, 650)
        
        self._updating = False
        self._last_changed = None
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        self.cad_widget = BridgeCADWidget()
        splitter.addWidget(self.cad_widget)
        
        splitter.setSizes([380, 1200])
    
    def compute_deck_total_width_mm(self, params):
        """Compute total deck width including median if present"""
        carriageway = params.get('carriageway_width', 10500)
        crash_barrier = params.get('crash_barrier_width', 500)
        footpath_width = params.get('footpath_width', 1500)
        fp_config = params.get('footpath_config', 'both')
        median_present = params.get('median_present', False)
        median_width = params.get('median_width', 1200)
        
        if fp_config == 'both':
            num_fp = 2
        elif fp_config in ['left', 'right']:
            num_fp = 1
        else:
            num_fp = 0
        
        if median_present:
            deck_total = (carriageway + 
                          median_width +
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        else:
            deck_total = (carriageway + 
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        
        return deck_total, num_fp
        
    def create_control_panel(self):
        """Create control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        title = QLabel("Bridge Design Parameters")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 11, QFont.Bold))
        title.setStyleSheet("background-color: #1e40af; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(title)
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f0f9ff;
                color: #1e40af;
                padding: 8px;
                border: 1px solid #bfdbfe;
                border-radius: 4px;
                font-size: 9px;
            }
        """)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(50)
        layout.addWidget(self.status_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        self.create_general_bridge_details(scroll_layout)
        self.create_geometry_group(scroll_layout)
        self.create_deck_footpath_group(scroll_layout)
        self.create_view_controls(scroll_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.create_action_buttons(layout)
        
        return panel
        
    def create_general_bridge_details(self, layout):
        """Create general bridge details - REMOVED median width input"""
        group = QGroupBox("General Bridge Details")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #1e40af; }")
        g = QGridLayout()
        
        r = 0
        
        g.addWidget(QLabel("Span (m):"), r, 0)
        self.span_input = QDoubleSpinBox()
        self.span_input.setRange(20, 45)
        self.span_input.setValue(35)
        self.span_input.setSingleStep(0.5)
        self.span_input.setDecimals(1)
        self.span_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.span_input, r, 1)
        g.addWidget(QLabel("[20-45m]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Carriageway (m):"), r, 0)
        self.carriageway_input = QDoubleSpinBox()
        self.carriageway_input.setRange(4.25, 24.0)
        self.carriageway_input.setValue(10.5)
        self.carriageway_input.setSingleStep(0.25)
        self.carriageway_input.setDecimals(2)
        self.carriageway_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.carriageway_input, r, 1)
        r += 1
        
        # MEDIAN OPTION - Only Yes/No, no width input
        g.addWidget(QLabel("Median:"), r, 0)
        self.median_combo = QComboBox()
        self.median_combo.addItems(["No", "Yes"])
        self.median_combo.setCurrentText("No")
        self.median_combo.currentTextChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.median_combo, r, 1)
        r += 1
                
        g.addWidget(QLabel("Footpath:"), r, 0)
        self.footpath_combo = QComboBox()
        self.footpath_combo.addItems(["None", "Left", "Right", "Both"])
        self.footpath_combo.setCurrentText("Both")
        self.footpath_combo.currentTextChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.footpath_combo, r, 1)
        r += 1
        
        g.addWidget(QLabel("Skew Angle (°):"), r, 0)
        self.skew_input = QDoubleSpinBox()
        self.skew_input.setRange(-15.0, 15.0)
        self.skew_input.setValue(0.0)
        self.skew_input.setSingleStep(1.0)
        self.skew_input.setDecimals(1)
        self.skew_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.skew_input, r, 1)
        g.addWidget(QLabel("[-15° to +15°]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_geometry_group(self, layout):
        """Create bridge geometry controls"""
        group = QGroupBox("Bridge Geometry")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #059669; }")
        g = QGridLayout()
        
        r = 0
        
        g.addWidget(QLabel("Number of Girders:"), r, 0)
        self.girders_input = QSpinBox()
        self.girders_input.setRange(2, 12)
        self.girders_input.setValue(4)
        self.girders_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.girders_input, r, 1)
        g.addWidget(QLabel("[2-12]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Girder Spacing (m):"), r, 0)
        self.spacing_input = QDoubleSpinBox()
        self.spacing_input.setRange(1.0, 24.0)
        self.spacing_input.setValue(2.75)
        self.spacing_input.setSingleStep(0.1)
        self.spacing_input.setDecimals(2)
        self.spacing_input.valueChanged.connect(lambda: self.on_param_changed('spacing'))
        g.addWidget(self.spacing_input, r, 1)
        g.addWidget(QLabel("[1.0-24.0m]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Deck Overhang (m):"), r, 0)
        self.deck_overhang_input = QDoubleSpinBox()
        self.deck_overhang_input.setRange(0.1, 5.0)
        self.deck_overhang_input.setValue(1.0)
        self.deck_overhang_input.setSingleStep(0.05)
        self.deck_overhang_input.setDecimals(3)
        self.deck_overhang_input.setToolTip("Distance from outermost girder to deck edge (enforced: 300-2000mm)")
        self.deck_overhang_input.valueChanged.connect(lambda: self.on_param_changed('overhang'))
        g.addWidget(self.deck_overhang_input, r, 1)
        g.addWidget(QLabel("[0.3-2.0m]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Bracing Spacing (m):"), r, 0)
        self.bracing_spacing_input = QDoubleSpinBox()
        self.bracing_spacing_input.setRange(1.0, 45.0)
        self.bracing_spacing_input.setValue(3.5)
        self.bracing_spacing_input.setSingleStep(0.5)
        self.bracing_spacing_input.setDecimals(2)
        self.bracing_spacing_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.bracing_spacing_input, r, 1)
        g.addWidget(QLabel("[1.0m-span]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_deck_footpath_group(self, layout):
        """Create deck and footpath controls"""
        group = QGroupBox("Deck / Footpath Details")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #7c3aed; }")
        g = QGridLayout()
        
        r = 0
        
        g.addWidget(QLabel("Deck Thickness (mm):"), r, 0)
        self.deck_input = QDoubleSpinBox()
        self.deck_input.setRange(0, 500)
        self.deck_input.setValue(200)
        self.deck_input.setSingleStep(10)
        self.deck_input.setDecimals(0)
        self.deck_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.deck_input, r, 1)
        g.addWidget(QLabel("[0-500mm]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Footpath Width (m):"), r, 0)
        self.fp_width_input = QDoubleSpinBox()
        self.fp_width_input.setRange(0.0, 10.0)
        self.fp_width_input.setValue(1.5)
        self.fp_width_input.setSingleStep(0.1)
        self.fp_width_input.setDecimals(2)
        self.fp_width_input.setToolTip("IRC minimum: 1.5m when footpath is provided")
        self.fp_width_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.fp_width_input, r, 1)
        g.addWidget(QLabel("[0-10.0m]"), r, 2)
        r += 1
        
        g.addWidget(QLabel("Footpath Thick (mm):"), r, 0)
        self.fp_thick_input = QDoubleSpinBox()
        self.fp_thick_input.setRange(0, 500)
        self.fp_thick_input.setValue(200)
        self.fp_thick_input.setSingleStep(10)
        self.fp_thick_input.setDecimals(0)
        self.fp_thick_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.fp_thick_input, r, 1)
        g.addWidget(QLabel("[0-500mm]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_view_controls(self, layout):
        """Create view selection controls"""
        group = QGroupBox("View Selection")
        group.setStyleSheet("QGroupBox { font-weight: bold; color: #ea580c; }")
        v = QVBoxLayout()
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Cross-Section", "Top View"])
        self.view_combo.currentIndexChanged.connect(self.on_view_changed)
        v.addWidget(self.view_combo)
        
        group.setLayout(v)
        layout.addWidget(group)
        
    def create_action_buttons(self, layout):
        """Create action buttons"""
        btn_layout = QGridLayout()
        
        self.export_btn = QPushButton("Export PNG")
        self.export_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px; font-weight: bold;")
        self.export_btn.clicked.connect(self.export_png)
        btn_layout.addWidget(self.export_btn, 0, 0)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; font-weight: bold;")
        self.reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(self.reset_btn, 0, 1)
        
        layout.addLayout(btn_layout)
        
    def on_view_changed(self, idx):
        if idx == 0:
            self.cad_widget.set_view_type('cross-section')
        else:
            self.cad_widget.set_view_type('top-view')
    
    def on_param_changed(self, source):
        """Track what parameter changed and update"""
        self._last_changed = source
        self.update_bridge()
    
    def update_status(self, message, is_warning=False):
        """Update the status label with notification"""
        if is_warning:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fef3c7;
                    color: #92400e;
                    padding: 8px;
                    border: 1px solid #fbbf24;
                    border-radius: 4px;
                    font-size: 9px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f9ff;
                    color: #1e40af;
                    padding: 8px;
                    border: 1px solid #bfdbfe;
                    border-radius: 4px;
                    font-size: 9px;
                }
            """)
        
        self.status_label.setText(message)
        QTimer.singleShot(8000, lambda: self.status_label.setText("Status: Ready"))
    
    def update_bridge(self):
        """Collect values, enforce formulas, and update CAD - FIXED for removed median width input"""
        MIN_OVERHANG = 300
        MAX_OVERHANG = 2000
        
        if self._updating:
            return
        
        self._updating = True
        
        try:
            params = {}
            
            params['span_length'] = float(self.span_input.value()) * 1000.0
            params['carriageway_width'] = float(self.carriageway_input.value()) * 1000.0
            params['skew_angle'] = float(self.skew_input.value())
            params['footpath_config'] = self.footpath_combo.currentText().lower()
            
            # MEDIAN PARAMETERS - Fixed width of 1.2m (1200mm)
            params['median_present'] = self.median_combo.currentText() == "Yes"
            params['median_width'] = 1200.0  # Fixed value, no input
            
            params['num_girders'] = int(self.girders_input.value())
            params['girder_spacing'] = float(self.spacing_input.value()) * 1000.0
            params['cross_bracing_spacing'] = float(self.bracing_spacing_input.value()) * 1000.0
            params['crash_barrier_width'] = 500.0
            
            params['deck_thickness'] = float(self.deck_input.value())
            params['deck_overhang'] = float(self.deck_overhang_input.value()) * 1000.0
            params['footpath_width'] = float(self.fp_width_input.value()) * 1000.0
            params['footpath_thickness'] = float(self.fp_thick_input.value())
            params['railing_height'] = 1000.0
            params['railing_width'] = 100.0
            
            if params['cross_bracing_spacing'] > params['span_length']:
                params['cross_bracing_spacing'] = params['span_length']
                self.bracing_spacing_input.blockSignals(True)
                self.bracing_spacing_input.setValue(params['span_length'] / 1000.0)
                self.bracing_spacing_input.blockSignals(False)
            
            deck_total, num_fp = self.compute_deck_total_width_mm(params)
            n = params['num_girders']
            
            if self._last_changed == 'overhang':
                if n > 1:
                    new_spacing = (deck_total - 2 * params['deck_overhang']) / (n - 1)
                    new_spacing = max(1000, min(24000, new_spacing))
                    
                    if abs(new_spacing - params['girder_spacing']) > 1:
                        params['girder_spacing'] = new_spacing
                        self.spacing_input.blockSignals(True)
                        self.spacing_input.setValue(new_spacing / 1000.0)
                        self.spacing_input.blockSignals(False)
                        self.update_status(f"⚙ Girder Spacing adjusted to {new_spacing/1000:.2f}m")
                        
            elif self._last_changed == 'spacing':
                if n > 1:
                    new_overhang = (deck_total - params['girder_spacing'] * (n - 1)) / 2.0
                else:
                    new_overhang = deck_total / 2.0
                
                new_overhang = max(MIN_OVERHANG, min(MAX_OVERHANG, new_overhang))
                if abs(new_overhang - params['deck_overhang']) > 1:
                    params['deck_overhang'] = new_overhang
                    self.deck_overhang_input.blockSignals(True)
                    self.deck_overhang_input.setValue(new_overhang / 1000.0)
                    self.deck_overhang_input.blockSignals(False)
                    self.update_status(f"Deck Overhang adjusted to {new_overhang/1000:.3f}m to match deck width")
                    
            else:
                if n > 1:
                    required_overhang = (deck_total - params['girder_spacing'] * (n - 1)) / 2.0
                else:
                    required_overhang = deck_total / 2.0
                
                if required_overhang < MIN_OVERHANG:
                    if n > 1:
                        new_spacing = (deck_total - 2 * MIN_OVERHANG) / (n - 1)
                        new_spacing = max(1000, min(24000, new_spacing))
                        params['girder_spacing'] = new_spacing
                        params['deck_overhang'] = MIN_OVERHANG
                        
                        self.spacing_input.blockSignals(True)
                        self.spacing_input.setValue(new_spacing / 1000.0)
                        self.spacing_input.blockSignals(False)
                        
                        self.deck_overhang_input.blockSignals(True)
                        self.deck_overhang_input.setValue(MIN_OVERHANG / 1000.0)
                        self.deck_overhang_input.blockSignals(False)
                        
                        self.update_status(f"⚙ Auto-adjusted: Spacing={new_spacing/1000:.2f}m, Overhang={MIN_OVERHANG/1000:.3f}m")
                    else:
                        params['deck_overhang'] = MIN_OVERHANG
                        self.deck_overhang_input.blockSignals(True)
                        self.deck_overhang_input.setValue(MIN_OVERHANG / 1000.0)
                        self.deck_overhang_input.blockSignals(False)
                        
                elif required_overhang > MAX_OVERHANG:
                    if n > 1:
                        new_spacing = (deck_total - 2 * MAX_OVERHANG) / (n - 1)
                        new_spacing = max(1000, min(24000, new_spacing))
                        params['girder_spacing'] = new_spacing
                        params['deck_overhang'] = MAX_OVERHANG
                        
                        self.spacing_input.blockSignals(True)
                        self.spacing_input.setValue(new_spacing / 1000.0)
                        self.spacing_input.blockSignals(False)
                        
                        self.deck_overhang_input.blockSignals(True)
                        self.deck_overhang_input.setValue(MAX_OVERHANG / 1000.0)
                        self.deck_overhang_input.blockSignals(False)
                        
                        self.update_status(f"⚙ Auto-adjusted: Spacing={new_spacing/1000:.2f}m, Overhang={MAX_OVERHANG/1000:.3f}m")
                    else:
                        params['deck_overhang'] = MAX_OVERHANG
                        self.deck_overhang_input.blockSignals(True)
                        self.deck_overhang_input.setValue(MAX_OVERHANG / 1000.0)
                        self.deck_overhang_input.blockSignals(False)
                else:
                    if abs(required_overhang - params['deck_overhang']) > 1:
                        params['deck_overhang'] = required_overhang
                        self.deck_overhang_input.blockSignals(True)
                        self.deck_overhang_input.setValue(required_overhang / 1000.0)
                        self.deck_overhang_input.blockSignals(False)
            
            self.cad_widget.update_params(params)
            
        finally:
            self._updating = False
        
    def reset_defaults(self):
        """Reset to default values per specification"""
        self._last_changed = 'other'
        
        self.span_input.setValue(35.0)
        self.girders_input.setValue(4)
        self.spacing_input.setValue(2.75)
        self.bracing_spacing_input.setValue(3.5)
        self.carriageway_input.setValue(10.5)
        self.skew_input.setValue(0.0)
        self.deck_input.setValue(200)
        self.deck_overhang_input.setValue(1.0)
        self.fp_width_input.setValue(1.5)
        self.fp_thick_input.setValue(200)
        self.footpath_combo.setCurrentText("Both")
        self.view_combo.setCurrentIndex(0)
        
        self.update_bridge()
        self.update_status("Reset to default values (Span=35m, N=4, Spacing=2.75m, Carriageway=10.5m)")
        
    def export_png(self):
        """Export current CAD view to PNG"""
        view_name = "cross_section" if self.view_combo.currentIndex() == 0 else "top_view"
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Bridge CAD", 
            f"bridge_{view_name}.png", 
            "PNG Files (*.png)"
        )
        if fname:
            pix = QPixmap(self.cad_widget.size())
            self.cad_widget.render(pix)
            pix.save(fname, "PNG")
            self.update_status(f"✓ Exported to: {fname}")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BridgeDesignGUI()
    window.show()
    
    window.reset_defaults()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()