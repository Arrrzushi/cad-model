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
        
        # Bridge parameters with default values (all in mm)
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
        }
        
        # Girder dimensions (mm)
        self.girder = {
            'depth': 500,
            'flange_width': 180,
            'flange_thickness': 17.2,
            'web_thickness': 10.2,
        }
        
        # Stiffener dimensions
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
        
        # Crash barrier dimensions (mm) 
        self.crash_barrier = {
            'width': 500,
            'height': 800,
            'base_width': 300,
        }
        
        # Railing dimensions
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
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if self.view_type == 'cross-section':
            self.draw_cross_section(painter)
        else:
            self.draw_top_view(painter)
    
    def draw_text_with_background(self, painter, x, y, text, bg_color=QColor(255, 255, 255, 230), 
                                  text_color=QColor(0, 0, 0), font_size=7, bold=False):
        """text with a semi-transparent background for visibility"""
        font_weight = QFont.Bold if bold else QFont.Normal
        font = QFont('Arial', font_size, font_weight)
        painter.setFont(font)
        
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(text)
        
        padding = 2
        bg_rect = QRectF(x - padding, y - text_rect.height() - padding, 
                        text_rect.width() + 2*padding, text_rect.height() + 2*padding)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(bg_rect)
        
        painter.setPen(QPen(text_color, 0.8))
        painter.drawText(int(x), int(y - padding), text)
    
    def draw_dimension_arrow(self, painter, x1, y1, x2, y2, text, horizontal=True, offset=0, text_offset=0, draw_extensions=True, extension_direction='down'):
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
    
    def compute_deck_total_width(self):
        """Compute total deck width """
        carriageway = self.params.get('carriageway_width', 10500)
        crash_barrier = self.params.get('crash_barrier_width', 500)
        footpath_width = self.params.get('footpath_width', 1500)
        fp_config = self.params.get('footpath_config', 'both')
        
        if fp_config == 'both':
            num_fp = 2
        elif fp_config in ['left', 'right']:
            num_fp = 1
        else:
            num_fp = 0
        
        deck_total = (carriageway + 
                      2 * crash_barrier + 
                      num_fp * footpath_width)
        
        return deck_total, num_fp
            
    def draw_cross_section(self, painter):
        """Draw cross-section"""
        # Define colors used in cross-section
        GIRDER_COLOR = QColor(180, 230, 180)  # green color for girders and stiffeners
        CROSS_BRACING_COLOR = QColor(255, 140, 0)  # orange for cross bracing
        
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
        
        # Layout positions
        left_fp_x = deck_left_x
        left_barrier_x = left_fp_x + left_fp_width * scale
        carriageway_start_x = left_barrier_x + self.params['crash_barrier_width'] * scale
        
        carriageway_end_x = carriageway_start_x + self.params['carriageway_width'] * scale
        right_barrier_x = carriageway_end_x
        right_fp_x = right_barrier_x + self.params['crash_barrier_width'] * scale

        # Calculate girder positions
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

        # Draw deck slab
        deck_slab_left = left_barrier_x
        deck_slab_right = right_barrier_x + self.params['crash_barrier_width'] * scale
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(deck_slab_left, deck_top_y,
                            deck_slab_right - deck_slab_left, deck_thick_px))

        # Fill carriageway area
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(carriageway_start_x, deck_top_y,
                            self.params['carriageway_width'] * scale, deck_thick_px))

        # Crash barrier areas on deck
        painter.drawRect(QRectF(left_barrier_x, deck_top_y,
                                self.params['crash_barrier_width'] * scale, deck_thick_px))
        painter.drawRect(QRectF(right_barrier_x, deck_top_y,
                                self.params['crash_barrier_width'] * scale, deck_thick_px))

        # Draw footpaths
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(QRectF(left_fp_x, fp_top_y,
                                left_fp_width * scale, fp_thick_px))

        if fp_config in ['right', 'both'] and right_fp_width > 0:
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(QRectF(right_fp_x, fp_top_y,
                                right_fp_width * scale, fp_thick_px))

        # Draw crash barriers 
        cb_y = deck_top_y
        self.draw_crash_barrier(painter, left_barrier_x, cb_y, scale, side='left')
        self.draw_crash_barrier(painter, right_barrier_x, cb_y, scale, side='right')

        # Draw bottom line of deck
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.drawLine(QPointF(deck_left_x, deck_bottom_y), 
                        QPointF(deck_right_x, deck_bottom_y))

        # Draw X-bracing using cross bracing color
        if n > 1:
            girder_top_edge = base_y - girder_depth_visual
            girder_bottom_edge = base_y
            
            for i in range(n - 1):
                x1 = positions[i]
                x2 = positions[i + 1]
                
                # Draw beige highlight panel
                panel_points = [
                    QPointF(x1, girder_top_edge),
                    QPointF(x2, girder_top_edge),
                    QPointF(x2, girder_bottom_edge),
                    QPointF(x1, girder_bottom_edge)
                ]
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 240, 220, 100)))
                painter.drawPolygon(QPolygonF(panel_points))
                
                # Double-line X bracing using orange color
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
                    
        # Draw girders and stiffeners using green color
        painter.setBrush(QBrush(GIRDER_COLOR))
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))

        for girder_x in positions:
            self.draw_i_section(painter, girder_x, base_y, scale, GIRDER_COLOR)
            self.draw_stiffeners(painter, girder_x, base_y, scale, GIRDER_COLOR)

        # Draw railings
        left_railing_rect = None
        right_railing_rect = None

        railing_width_px = max(3, self.params['railing_width'] * scale)

        if fp_config in ['left', 'both'] and left_fp_width > 0:
            railing_x = deck_left_x
            left_railing_rect = self.draw_railing_post(painter, railing_x, fp_top_y, scale, "left")
            
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            actual_railing_width = max(3, self.params['railing_width'] * scale)
            railing_x = deck_right_x - actual_railing_width
            right_railing_rect = self.draw_railing_post(painter, railing_x, fp_top_y, scale, "right")
            if right_railing_rect and len(right_railing_rect) > 4:
                railing_width_px = right_railing_rect[4]

        self.add_professional_cross_section_dimensions(
            painter, deck_left_x, deck_right_x, carriageway_start_x, carriageway_end_x,
            left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y, fp_top_y,
            base_y, scale, positions, n, fp_config, left_fp_width, right_fp_width,
            left_fp_x, right_fp_x, railing_width_px
        )

        self.add_clean_component_labels(
            painter, carriageway_start_x, carriageway_end_x, left_barrier_x, right_barrier_x,
            deck_top_y, deck_bottom_y, deck_thick_px, positions, base_y, scale, n, fp_config,
            deck_left_x, deck_right_x, left_fp_width, right_fp_width, fp_top_y, fp_thick_px,
            left_fp_x, right_fp_x, left_railing_rect, right_railing_rect, railing_width_px
        )

    def draw_railing_post(self, painter, x, y, scale, side):
        """Draw railing with a base of 100mm """
        # Fixed base
        RAILING_BASE_HEIGHT_MM = 100  # mm 
        
        total_h = self.params['railing_height'] * scale
        w = self.params['railing_width'] * scale
        
        # Minimum width 
        w = max(3, w)
        
        # Fixed base height (100mm)
        base_h = RAILING_BASE_HEIGHT_MM * scale
        
        # Ensure base doesn't exceed total height
        base_h = min(base_h, total_h * 0.3)  # Max 30% of total height
        base_h = max(base_h, 3)  # Minimum visibility
        
        # Post height (variable part)
        post_h = total_h - base_h
        
        rect_x = x
        base_bottom_y = y  # Base sits on footpath
        base_top_y = y - base_h
        post_top_y = y - total_h
        
        corner_radius = min(w * 0.1, 6)
        
        # Draw BASE RECTANGLE 
        painter.setBrush(QBrush(QColor(200, 200, 200)))  
        painter.setPen(QPen(QColor(34, 34, 34), max(1, scale * 2)))
        
        base_rect = QRectF(rect_x, base_top_y, w, base_h)
        painter.drawRoundedRect(base_rect, corner_radius * 0.5, corner_radius * 0.5)
        
        # Draw POST (variable height, extends upward from base)
        if post_h > 2:  # Only draw if there's meaningful height
            painter.setBrush(QBrush(QColor(242, 242, 242)))  # Light gray
            painter.setPen(QPen(QColor(34, 34, 34), max(1, scale * 2)))
            
            post_rect = QRectF(rect_x, post_top_y, w, post_h)
            painter.drawRoundedRect(post_rect, corner_radius, corner_radius)
            
            # Draw square window cutouts 
            window_margin_ratio = 0.15
            window_size = w * (1 - 2 * window_margin_ratio)
            window_size = max(2, min(window_size, post_h * 0.25))  # Ensure windows fit
            
            window_x = rect_x + (w - window_size) / 2
            
            # Calculate window positions within post
            available_height = post_h * 0.85
            top_margin = post_h * 0.08
            
            # Calculate number of windows based on available space
            min_window_spacing = window_size * 1.3
            if available_height > window_size:
                num_windows = max(1, int(available_height / min_window_spacing))
                num_windows = min(num_windows, 6)  # Max 6 windows
                
                if num_windows > 1:
                    actual_spacing = (available_height - window_size) / (num_windows - 1)
                else:
                    actual_spacing = 0
                
                window_corner_radius = min(window_size * 0.15, 4)
                
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.setPen(QPen(QColor(119, 119, 119), max(1, scale * 1.0)))
                
                for i in range(num_windows):
                    window_y = post_top_y + top_margin + i * actual_spacing
                    # Ensure window stays within post bounds
                    if window_y + window_size < base_top_y - 2:
                        window_rect = QRectF(window_x, window_y, window_size, window_size)
                        painter.drawRoundedRect(window_rect, window_corner_radius, window_corner_radius)
        
        # Dashed outer guideline for entire railing
        painter.setPen(QPen(QColor(189, 189, 189), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        outline_margin = 2
        outline_rect = QRectF(rect_x - outline_margin, post_top_y - outline_margin, 
                            w + 2*outline_margin, total_h + 2*outline_margin)
        painter.drawRoundedRect(outline_rect, corner_radius + 2, corner_radius + 2)
        
        # Return dimensions: (left_x, top_y, right_x, bottom_y, width)
        return (rect_x, post_top_y, rect_x + w, y, w)

    def add_clean_component_labels(self, painter, carriageway_start_x, carriageway_end_x,
                            left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y,
                            deck_thick_px, positions, base_y, scale, n, fp_config,
                            deck_left_x, deck_right_x, left_fp_width, 
                            right_fp_width, fp_top_y, fp_thick_px,
                            left_fp_x, right_fp_x, left_railing_rect, right_railing_rect,
                            railing_width_px):
        """Add component labels"""
        
        # CRASH BARRIER LABELS
        cb_height = self.crash_barrier['height'] * scale
        
        left_cb_x = left_barrier_x + (self.params['crash_barrier_width'] * scale) / 2
        left_cb_top_y = deck_top_y - cb_height
        
        self.draw_text_with_background(painter, left_cb_x - 30, left_cb_top_y - 8,
                                    "Crash Barrier", QColor(255, 250, 240, 250), 
                                    QColor(200, 100, 0), 7, True)
        
        right_cb_x = right_barrier_x + (self.params['crash_barrier_width'] * scale) / 2
        right_cb_top_y = deck_top_y - cb_height
        
        self.draw_text_with_background(painter, right_cb_x - 30, right_cb_top_y - 8,
                                    "Crash Barrier", QColor(255, 250, 240, 250), 
                                    QColor(200, 100, 0), 7, True)
        
        # STIFFENER LABEL 
        if len(positions) > 0:
            girder_x = positions[-1]
            
            visual = self.girder_visual_scale
            flange_w = self.girder['flange_width'] * scale * visual['flange_width']
            web_w = self.girder['web_thickness'] * scale * visual['web_thickness']
            girder_depth_visual = self.girder['depth'] * scale * visual['depth']
            flange_thick_visual = self.girder['flange_thickness'] * scale * visual['flange_thickness']
            
            stiff_center_x = girder_x + (web_w/2 + flange_w/2) / 2
            stiff_center_y = base_y - girder_depth_visual + flange_thick_visual + (girder_depth_visual - 2*flange_thick_visual) / 2
            stiff_y = stiff_center_y + 3
            
            label_x = stiff_center_x + 40
            label_y = base_y + 50
            
            self.draw_leader_arrow(painter, label_x, label_y, stiff_center_x, stiff_y,
                                "Stiffener", QColor(255, 240, 240, 250), QColor(150, 50, 50))
        
        # CROSS BRACING LABEL
        if n > 1 and len(positions) >= 2:
            mid_x = (positions[-2] + positions[-1]) / 2
            girder_depth_visual = self.girder['depth'] * scale * self.girder_visual_scale['depth']
            mid_y = base_y - girder_depth_visual / 2
            
            label_x = mid_x + 45
            label_y = base_y + 80
            
            self.draw_leader_arrow(painter, label_x, label_y, mid_x, mid_y,
                                "Cross Bracing", QColor(255, 250, 240, 250), QColor(200, 100, 0))
        
        # RAILING LABELS with arrows
        railing_h = self.params['railing_height']
        
        # Left railing label with arrow
        if fp_config in ['left', 'both'] and left_fp_width > 0 and left_railing_rect is not None:
            railing_left_x = left_railing_rect[0]
            railing_top_y = left_railing_rect[1]
            railing_bottom_y = left_railing_rect[3]
            
            arrow_x = railing_left_x - 8
            self.draw_railing_dimension_arrow(painter, arrow_x, railing_top_y, railing_bottom_y,
                                            f"Railing = {railing_h:.0f} mm", 'left')
        
        # Right railing label with arrow
        if fp_config in ['right', 'both'] and right_fp_width > 0 and right_railing_rect is not None:
            railing_right_x = right_railing_rect[2]
            railing_top_y = right_railing_rect[1]
            railing_bottom_y = right_railing_rect[3]
            
            arrow_x = railing_right_x + 8
            self.draw_railing_dimension_arrow(painter, arrow_x, railing_top_y, railing_bottom_y,
                                            f"Railing = {railing_h:.0f} mm", 'right')
        
        # FOOTPATH LABELS
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 10:
            fp_visible_start = deck_left_x + railing_width_px
            fp_visible_end = left_barrier_x
            fp_center_x = (fp_visible_start + fp_visible_end) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            
            if (fp_visible_end - fp_visible_start) > 60:
                self.draw_text_with_background(painter, fp_center_x - 18, fp_center_y + 3,
                                            "Footpath", QColor(220, 220, 220, 240),
                                            QColor(60, 60, 60), 7, True)
        
        if fp_config in ['right', 'both'] and right_fp_width > 0 and fp_thick_px > 10:
            fp_visible_start = right_fp_x
            fp_visible_end = deck_right_x - railing_width_px
            fp_center_x = (fp_visible_start + fp_visible_end) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            
            if (fp_visible_end - fp_visible_start) > 60:
                self.draw_text_with_background(painter, fp_center_x - 18, fp_center_y + 3,
                                            "Footpath", QColor(220, 220, 220, 240),
                                            QColor(60, 60, 60), 7, True)

    def draw_railing_dimension_arrow(self, painter, x, y1, y2, text, side='left'):
        """railing dimension"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
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
        
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        text_height = metrics.height()
        
        text_y = (y1 + y2) / 2 + text_height / 4
        
        if side == 'left':
            text_x = x - text_width - 8
        else:
            text_x = x + 8
        
        self.draw_text_with_background(painter, text_x, text_y, text,
                                    QColor(255, 255, 255, 250), QColor(60, 60, 60), 7, True)

    def add_professional_cross_section_dimensions(self, painter, deck_left_x, deck_right_x,
                                carriageway_start_x, carriageway_end_x,
                                    left_barrier_x, right_barrier_x,
                                    deck_top_y, deck_bottom_y, fp_top_y,
                                    base_y, scale, girder_positions, n,
                                    fp_config, left_fp_width, right_fp_width,
                                    left_fp_x, right_fp_x, railing_width_px):
        """Add organized dimension lines"""
        
        fp_thick_px = self.params['footpath_thickness'] * scale
        
        # LEVEL 1: Overall Bridge Width
        y_level1 = deck_top_y - 150
        total_width_m = (deck_right_x - deck_left_x) / scale / 1000
        self.draw_dimension_arrow(painter, deck_left_x, y_level1, deck_right_x, y_level1,
                                f"Overall Bridge Width = {total_width_m:.2f} m", True, 
                                extension_direction='down')
        
        # LEVEL 2: Footpath dimensions
        y_level2 = deck_top_y - 115
        
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            fp_start_x = deck_left_x + railing_width_px
            fp_end_x = left_barrier_x
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, y_level2, 
                                        fp_end_x, y_level2,
                                        f"Footpath width = {fp_visible_m:.2f} m", True, extension_direction='down')
        
        # LEVEL 2b: DECK dimension
        y_level2b = deck_top_y - 95
        deck_dim_start_x = left_barrier_x
        deck_dim_end_x = right_barrier_x + self.params['crash_barrier_width'] * scale
        deck_width_m = (deck_dim_end_x - deck_dim_start_x) / scale / 1000
        self.draw_dimension_arrow(painter, deck_dim_start_x, y_level2b, deck_dim_end_x, y_level2b,
                                f"Deck = {deck_width_m:.2f} m", True, extension_direction='down')
        
        # LEVEL 2c: Carriageway
        y_level2c = deck_top_y - 62
        cw_m = self.params['carriageway_width'] / 1000
        self.draw_dimension_arrow(painter, carriageway_start_x, y_level2c, carriageway_end_x, y_level2c,
                                f"Carriageway = {cw_m:.2f} m", True, extension_direction='down')
        
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            fp_start_x = right_fp_x
            fp_end_x = deck_right_x - railing_width_px
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, y_level2, 
                                        fp_end_x, y_level2,
                                        f"Footpath width = {fp_visible_m:.2f} m", True, extension_direction='down')
        
        # LEVEL 3: Below bridge - Overhang
        y_level3 = base_y + 50
        
        if n > 0 and len(girder_positions) > 0:
            first_girder_x = girder_positions[0]
            overhang_m = self.params.get('deck_overhang', 1000) / 1000
            self.draw_dimension_arrow(painter, deck_left_x, y_level3, first_girder_x, y_level3,
                                    f"Overhang = {overhang_m:.2f} m", True, 
                                    extension_direction='up')
        
        # Girder spacing
        if n > 1 and len(girder_positions) >= 2:
            y_level4 = base_y + 90
            x_left = girder_positions[0]
            x_right = girder_positions[1]
            
            gs_m = self.params['girder_spacing'] / 1000
            self.draw_dimension_arrow(painter, x_left, y_level4, x_right, y_level4,
                                    f"Girder Spacing = {gs_m:.2f} m", True, 
                                    extension_direction='up')
        
        # FOOTPATH THICKNESS DIMENSION
        fp_t_mm = self.params['footpath_thickness']
        
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_left_x - 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath = {fp_t_mm:.0f} mm", 'left')
        
        if fp_config == 'right' and right_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_right_x + 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath = {fp_t_mm:.0f} mm", 'right')

    def draw_vertical_dimension_with_arrow(self, painter, x, y1, y2, text, side='left'):
        """Draw vertical dimension with arrow and text"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
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
        
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        text_height = metrics.height()
        
        text_y = (y1 + y2) / 2 + text_height / 4
        
        if side == 'left':
            text_x = x - text_width - 8
        else:
            text_x = x + 8
        
        self.draw_text_with_background(painter, text_x, text_y, text,
                                    QColor(255, 255, 255, 240), QColor(0, 0, 0), 7, True)

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
        
    def draw_stiffeners(self, painter, x, base_y, scale, girder_color):
        """Draw vertical stiffeners"""
        visual = self.girder_visual_scale
        
        stiff_w = self.stiffener['width'] * scale * visual['flange_width']
        stiff_h = self.stiffener['height'] * scale * visual['depth']
        
        tw = self.girder['web_thickness'] * scale * visual['web_thickness']
        flange_thick_visual = self.girder['flange_thickness'] * scale * visual['flange_thickness']
        girder_depth_visual = self.girder['depth'] * scale * visual['depth']
        
        painter.setBrush(QBrush(girder_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        stiff_top_y = base_y - girder_depth_visual + flange_thick_visual
        
        painter.drawRect(QRectF(x - tw/2 - stiff_w, stiff_top_y, stiff_w, stiff_h))
        painter.drawRect(QRectF(x + tw/2, stiff_top_y, stiff_w, stiff_h))

    def draw_crash_barrier(self, painter, x, y, scale, side='left'):
        """Draw crash barrier """
        BOTTOM_WIDTH_MM = 500.0
        HEIGHT_MM = 800.0
        
        bot_w = BOTTOM_WIDTH_MM * scale
        h = HEIGHT_MM * scale
        
        top_width_ratio = 30/245
        slant_height_ratio = 350/600
        drop_height_ratio = 60/600
        slant_offset_ratio = 210/245
        
        top_w = bot_w * top_width_ratio
        slant_h = h * slant_height_ratio
        drop_h = h * drop_height_ratio
        slant_offset = bot_w * slant_offset_ratio
        
        if side == 'left':
            points = [
                QPointF(x + 5*scale, y - h),
                QPointF(x + 5*scale + top_w, y - h),
                QPointF(x + slant_offset, y - h + slant_h),
                QPointF(x + slant_offset, y - h + slant_h + drop_h),
                QPointF(x + slant_offset, y),
                QPointF(x, y)
            ]
        else:
            points = [
                QPointF(x + bot_w - 5*scale - top_w, y - h),
                QPointF(x + bot_w - 5*scale, y - h),
                QPointF(x + bot_w, y),
                QPointF(x + bot_w - slant_offset, y),
                QPointF(x + bot_w - slant_offset, y - h + slant_h + drop_h),
                QPointF(x + bot_w - slant_offset, y - h + slant_h),
            ]
        
        painter.setBrush(QBrush(QColor(255, 165, 0)))
        painter.setPen(QPen(QColor(0, 0, 0), max(2.0, scale*2)))
        
        painter.drawPolygon(QPolygonF(points))
        
        painter.setPen(QPen(QColor(0, 0, 0), max(1.0, scale)))
        painter.drawPolyline(QPolygonF(points + [points[0]]))

    def draw_top_view(self, painter):
        """Draw top view"""
        # Define colors used in top view
        GIRDER_COLOR = QColor(180, 230, 180)  # green color for girders
        CROSS_BRACING_COLOR = QColor(255, 140, 0)  # orange for cross bracing
        
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

        skew_rad = math.radians(self.params['skew_angle'])
        
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

        # Draw girders using green color
        painter.setPen(QPen(GIRDER_COLOR.darker(150), 2.5))
        
        girder_lines = []
        for y_pos in girder_positions_y:
            y_offset_from_first = y_pos - girder_positions_y[0]
            x_offset = y_offset_from_first * math.tan(skew_rad)
            
            x1 = start_x_base + x_offset
            x2 = end_x_base + x_offset
            
            painter.drawLine(QPointF(x1, y_pos), QPointF(x2, y_pos))
            girder_lines.append({'y': y_pos, 'x1': x1, 'x2': x2})

        # Cross bracing - using orange color
        painter.setPen(QPen(CROSS_BRACING_COLOR, 1.8))
        
        bracing_positions_x = []
        if self.params['cross_bracing_spacing'] > 0 and n > 1:
            span_length = self.params['span_length']
            bracing_spacing = self.params['cross_bracing_spacing']
            
            num_braces = max(1, int(math.ceil(span_length / bracing_spacing)))
            actual_spacing_px = span_length_px / num_braces
            
            for section in range(num_braces + 1):
                brace_x_base = start_x_base + section * actual_spacing_px
                
                for i in range(len(girder_positions_y) - 1):
                    y1 = girder_positions_y[i]
                    y2 = girder_positions_y[i + 1]
                    
                    y1_offset = y1 - girder_positions_y[0]
                    y2_offset = y2 - girder_positions_y[0]
                    
                    x1 = brace_x_base + y1_offset * math.tan(skew_rad)
                    x2 = brace_x_base + y2_offset * math.tan(skew_rad)
                    
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    
                    if i == 0 and section < num_braces:
                        bracing_positions_x.append(brace_x_base)

        bearing_gap_px = max(30, 0.3 * self.params['girder_spacing'] * scale)

        top_extent = girder_positions_y[0] - bearing_gap_px
        bottom_extent = girder_positions_y[-1] + bearing_gap_px if n > 1 else girder_positions_y[0] + bearing_gap_px

        left_bearing_base_x = start_x_base
        right_bearing_base_x = end_x_base

        left_top_x = left_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        left_bottom_x = left_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        right_top_x = right_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        right_bottom_x = right_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        painter.setPen(QPen(QColor(255, 0, 0), 1.8, Qt.DashLine))
        painter.drawLine(QPointF(left_top_x, top_extent), 
                        QPointF(left_bottom_x, bottom_extent))
        painter.drawLine(QPointF(right_top_x, top_extent), 
                        QPointF(right_bottom_x, bottom_extent))

        self.draw_text_with_background(painter, left_top_x - 38, top_extent - 8,
                                    "Center line of Bearing", QColor(255, 255, 255, 240),
                                    QColor(255, 0, 0), 6, True)
        self.draw_text_with_background(painter, right_top_x - 38, top_extent - 8,
                                    "Center line of Bearing", QColor(255, 255, 255, 240),
                                    QColor(255, 0, 0), 6, True)

        # Draw skew angle indicator at top of left CL bearing line
        if abs(self.params['skew_angle']) > 0.1:
            self.draw_skew_angle_indicator(painter, left_top_x, top_extent, skew_rad, scale)

        self.add_clean_top_view_dimensions(
            painter, girder_lines, girder_positions_y, scale, n, bracing_positions_x,
            skew_rad, start_x_base, end_x_base
        )

        self.add_clean_top_view_notes(painter, height)

    def draw_skew_angle_indicator(self, painter, bearing_x, bearing_y, skew_rad, scale):
        """Draw skew angle indicator at the top of CL bearing line"""
        skew_deg = math.degrees(skew_rad)
        
        # Reference line (vertical/perpendicular to girders)
        ref_length = 40
        ref_end_y = bearing_y - ref_length
        
        # Draw reference vertical line (dashed, thin)
        painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DashLine))
        painter.drawLine(QPointF(bearing_x, bearing_y), QPointF(bearing_x, ref_end_y))
        
        # Draw arc for angle
        arc_radius = 25
        painter.setPen(QPen(QColor(0, 100, 200), 1.5))
        
        start_angle = 90 * 16
        span_angle = -skew_deg * 16
        
        arc_rect = QRectF(bearing_x - arc_radius, bearing_y - ref_length - arc_radius/2,
                         arc_radius * 2, arc_radius * 2)
        
        if abs(skew_deg) > 0.5:
            painter.drawArc(arc_rect, start_angle, span_angle)
            
            text_offset_x = 15 if skew_deg > 0 else -45
            text_y = bearing_y - ref_length + 5
            
            angle_text = f"θ = {abs(skew_deg):.1f}°"
            self.draw_text_with_background(painter, bearing_x + text_offset_x, text_y,
                                        angle_text, QColor(230, 240, 255, 250),
                                        QColor(0, 100, 200), 7, True)
            
            self.draw_text_with_background(painter, bearing_x + text_offset_x, text_y + 14,
                                        "Skew Angle", QColor(230, 240, 255, 250),
                                        QColor(0, 100, 200), 6, False)

    def add_clean_top_view_dimensions(self, painter, girder_lines, girder_positions_y,
                                    scale, n, bracing_positions, skew_rad,
                                    start_x_base, end_x_base):
        """Add clean dimensions that follow skew angle"""
        
        if not girder_lines:
            return
        
        last_girder_idx = len(girder_lines) - 1
        last_girder = girder_lines[last_girder_idx]
        last_girder_y = last_girder['y']
        
        y_offset_last = last_girder_y - girder_positions_y[0]
        x_offset_last = y_offset_last * math.tan(skew_rad)
        
        dim_y_base = last_girder_y + 50
        
        # SPAN LENGTH
        dim_y1 = dim_y_base
        x1_span = last_girder['x1']
        x2_span = last_girder['x2']
        span_m = self.params['span_length'] / 1000
        self.draw_dimension_arrow(painter, x1_span, dim_y1, x2_span, dim_y1,
                                f"Span Length = {span_m:.1f} m", True)

        # BRACING SPACING
        if self.params['cross_bracing_spacing'] > 0 and len(bracing_positions) > 1:
            dim_y2 = dim_y_base - 30
            cb_spacing_m = self.params['cross_bracing_spacing'] / 1000
            
            x1_brace = bracing_positions[0] + x_offset_last
            x2_brace = bracing_positions[1] + x_offset_last
            
            self.draw_dimension_arrow(painter, x1_brace, dim_y2, x2_brace, dim_y2,
                                    f"Bracing = {cb_spacing_m:.2f} m", True)

        # GIRDER SPACING
        if n > 1:
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1_at_end = end_x_base + y1_offset * math.tan(skew_rad) + 30
            x2_at_end = end_x_base + y2_offset * math.tan(skew_rad) + 30
            
            gs_m = self.params['girder_spacing'] / 1000
            
            self.draw_skewed_dimension_arrow(painter, x1_at_end, y1, x2_at_end, y2, 
                                            f"{gs_m:.2f} m", skew_rad)
            
            label_x = max(x1_at_end, x2_at_end) + 45
            label_y = (y1 + y2) / 2
            
            self.draw_text_with_background(painter, label_x, label_y - 8,
                                        "Girder", QColor(255, 255, 255, 250),
                                        QColor(0, 100, 0), 7, True)
            self.draw_text_with_background(painter, label_x, label_y + 6,
                                        "Spacing", QColor(255, 255, 255, 250),
                                        QColor(0, 100, 0), 7, True)

        # Girders label
        if len(girder_positions_y) > 0:
            label_x = (girder_lines[0]['x1'] + girder_lines[0]['x2']) / 2
            label_y = girder_positions_y[0] - 15
            
            self.draw_text_with_background(painter, label_x - 20, label_y,
                                        "Girders", QColor(255, 255, 255, 240),
                                        QColor(0, 100, 0), 7, True)
        
        # Cross Bracing label
        if n > 1 and len(bracing_positions) > 0:
            brace_x = bracing_positions[0] if bracing_positions else start_x_base
            brace_y = (girder_positions_y[0] + girder_positions_y[1]) / 2 if len(girder_positions_y) > 1 else girder_positions_y[0]
            
            self.draw_text_with_background(painter, brace_x + 6, brace_y + 3,
                                        "Cross Bracing", QColor(255, 250, 240, 240),
                                        QColor(200, 100, 0), 6, True)

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
        
        font = QFont('Arial', 7, QFont.Bold)
        painter.setFont(font)
        
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
            f"1. Green lines: Girders, Quantity = {self.params['num_girders']} nos.",
            f"2. Orange lines: Cross bracing members (ISA 100×100×8) connecting adjacent girders",
            f"3. Red dashed lines: Centerline of bearings at supports",
            f"4. Skew angle: {self.params['skew_angle']:.1f}° (angle between bearing CL and perpendicular to girder)",
            f"5. Cross bracing distributed evenly to cover the entire span length",
            f"6. All dimensions in meters unless noted otherwise",
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
        """Compute total deck width """
        carriageway = params.get('carriageway_width', 10500)
        crash_barrier = params.get('crash_barrier_width', 500)
        footpath_width = params.get('footpath_width', 1500)
        fp_config = params.get('footpath_config', 'both')
        
        if fp_config == 'both':
            num_fp = 2
        elif fp_config in ['left', 'right']:
            num_fp = 1
        else:
            num_fp = 0
        
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
        """Create general bridge details"""
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
        
        g.addWidget(QLabel("Railing Height (mm):"), r, 0)
        self.railing_height_input = QDoubleSpinBox()
        self.railing_height_input.setRange(200, 2000)
        self.railing_height_input.setValue(1000)
        self.railing_height_input.setSingleStep(50)
        self.railing_height_input.setDecimals(0)
        self.railing_height_input.setToolTip("Default: 1000mm")
        self.railing_height_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.railing_height_input, r, 1)
        r += 1
        
        g.addWidget(QLabel("Railing Width (mm):"), r, 0)
        self.railing_width_input = QDoubleSpinBox()
        self.railing_width_input.setRange(50, 500)
        self.railing_width_input.setValue(100)
        self.railing_width_input.setSingleStep(10)
        self.railing_width_input.setDecimals(0)
        self.railing_width_input.setToolTip("Railing post width - expands inward, does NOT affect deck width")
        self.railing_width_input.valueChanged.connect(lambda: self.on_param_changed('other'))
        g.addWidget(self.railing_width_input, r, 1)
        g.addWidget(QLabel("[50-500mm]"), r, 2)
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
        """Collect values, enforce formulas, and update CAD"""
        # Overhang validation constants
        MIN_OVERHANG = 300   # mm 
        MAX_OVERHANG = 2000  # mm
        
        if self._updating:
            return
        
        self._updating = True
        
        try:
            params = {}
            
            params['span_length'] = float(self.span_input.value()) * 1000.0
            params['carriageway_width'] = float(self.carriageway_input.value()) * 1000.0
            params['skew_angle'] = float(self.skew_input.value())
            params['footpath_config'] = self.footpath_combo.currentText().lower()
            
            params['num_girders'] = int(self.girders_input.value())
            params['girder_spacing'] = float(self.spacing_input.value()) * 1000.0
            params['cross_bracing_spacing'] = float(self.bracing_spacing_input.value()) * 1000.0
            params['crash_barrier_width'] = 500.0  # Fixed at 500mm
            
            params['deck_thickness'] = float(self.deck_input.value())
            params['deck_overhang'] = float(self.deck_overhang_input.value()) * 1000.0
            params['footpath_width'] = float(self.fp_width_input.value()) * 1000.0
            params['footpath_thickness'] = float(self.fp_thick_input.value())
            params['railing_height'] = float(self.railing_height_input.value())
            params['railing_width'] = float(self.railing_width_input.value())
            
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
        self.railing_height_input.setValue(1000)
        self.railing_width_input.setValue(100)
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