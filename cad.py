"""
Dynamic 2D CAD Model of a Steel Girder Bridge
Strictly follows IRC and IS standards as per DDCL specification
Corrected version with proper cross-bracing visualization
Author: Arushi
"""

import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox,
                               QPushButton, QComboBox, QGroupBox, QGridLayout,
                               QScrollArea, QFileDialog, QSplitter, QCheckBox)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPixmap


class BridgeCADWidget(QWidget):
    """Custom widget for drawing bridge CAD views per DDCL specs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 600)
        self.view_type = 'cross-section'
        
        # Bridge parameters with default values (all in mm) - DDCL defaults
        self.params = {
            'span_length': 35000,          # 20-45m per DDCL
            'num_girders': 4,              # 2-12 per DDCL
            'girder_spacing': 2750,        # 1-24m per DDCL
            'cross_bracing_spacing': 3500, # ≥1m, ≤span_length per DDCL
            'carriageway_width': 10500,    # ≥4.25m per IRC 5
            'skew_angle': 0,               # -15 to +15° per IRC 5
            'deck_thickness': 200,         # 0-500mm per DDCL
            'footpath_width': 1500,        # 0-10m per IRC 5
            'footpath_thickness': 200,     # 0-500mm per DDCL
            'crash_barrier_width': 500,    # typical 500mm per IRC
            'railing_height': 1000,        # per IRC 5
            'footpath_config': 'both',     # none/left/right/both
        }
        
        # ISMB 500 Girder dimensions (mm) - Standard Indian section
        self.girder = {
            'depth': 500,
            'flange_width': 180,
            'flange_thickness': 17.2,
            'web_thickness': 10.2,
        }

        # Visual scale multipliers for girder rendering (makes girders bolder on screen)
        self.girder_visual_scale = {
            'flange_width': 1.25,
            'flange_thickness': 1.35,
            'web_thickness': 1.25,
        }
        
        # ISA 100x100x8 Cross bracing (mm) - Standard Indian angle section
        self.bracing = {
            'depth': 100,
            'width': 100,
            'thickness': 8,
        }
        
        # Crash barrier dimensions (IRC typical values)
        self.crash_barrier = {
            'width': 500,
            'height': 800,
            'base_width': 300,
        }
        
        # Railing dimensions (IRC 5 requirements)
        self.railing = {
            'post_dia': 50,
            'height': 1000,
            'rail_count': 3,
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
            
    def draw_cross_section(self, painter):
        """Draw cross-section view with robust girder placement so none overflow."""
        width = self.width()
        height = self.height()

        # DDCL 3.1.1: Calculate Overall Bridge Width
        fp_config = self.params.get('footpath_config', 'both')

        # Calculate footpath widths based on configuration
        left_fp_width = self.params['footpath_width'] if fp_config in ['left', 'both'] else 0
        right_fp_width = self.params['footpath_width'] if fp_config in ['right', 'both'] else 0

        # Overall Bridge Width = Carriageway Width + 2*Crash Barrier + Footpaths
        total_width = (self.params['carriageway_width'] +
                       2 * self.params['crash_barrier_width'] +
                       left_fp_width + right_fp_width)

        # Calculate scale
        margin = 100
        scale = min((width - 2*margin) / total_width,
                   (height - 2*margin - 200) / (self.girder['depth'] +
                                                self.params['deck_thickness'] +
                                                self.params['footpath_thickness'] + 1500))

        center_x = width / 2
        # move baseline slightly lower to avoid upward nudge when scale changes
        base_y = height - margin - 200   # <-- was 250, reduced to stabilize vertical anchoring

        # Draw title
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawText(20, 30, "Figure 1: Cross-Section of the Bridge")

        
        # top of girder where deck sits
        girder_top_y = base_y - self.girder['depth'] * scale

        deck_thick_px = self.params['deck_thickness'] * scale
        fp_thick_px = self.params['footpath_thickness'] * scale

        # deck top and bottom (bottom sits on girder top)
        deck_bottom_y = girder_top_y
        deck_top_y = deck_bottom_y - deck_thick_px

        # footpath band stays anchored just above girder top regardless of deck thickness
        fp_bottom_y = deck_bottom_y
        fp_top_y = fp_bottom_y - fp_thick_px

        # horizontal extents
        deck_start_x = center_x - (total_width * scale) / 2
        deck_left_x = deck_start_x
        deck_right_x = deck_start_x + total_width * scale
        deck_width_scaled = deck_right_x - deck_left_x
        barrier_width_px = self.params['crash_barrier_width'] * scale
        left_barrier_x = deck_left_x + left_fp_width * scale
        right_barrier_x = deck_right_x - right_fp_width * scale - barrier_width_px

        # carriageway extents (deck only between inner faces of crash barriers)
        carriageway_start_x = left_barrier_x + barrier_width_px
        carriageway_width_px = self.params['carriageway_width'] * scale
        carriageway_end_x = carriageway_start_x + carriageway_width_px

        # draw carriageway deck (anchored to deck_top_y and deck_bottom_y)
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(QRectF(carriageway_start_x,
                               deck_top_y,
                               carriageway_width_px,
                               deck_thick_px))

        # deck under crash barrier zones should grow with deck thickness too
        if barrier_width_px > 0:
            painter.drawRect(QRectF(left_barrier_x,
                                    deck_top_y,
                                    barrier_width_px,
                                    deck_thick_px))
            painter.drawRect(QRectF(right_barrier_x,
                                    deck_top_y,
                                    barrier_width_px,
                                    deck_thick_px))

        # draw small vertical separators at inner faces of crash barriers
        painter.drawLine(QPointF(carriageway_start_x, deck_top_y),
                         QPointF(carriageway_start_x, deck_bottom_y))
        painter.drawLine(QPointF(carriageway_end_x, deck_top_y),
                         QPointF(carriageway_end_x, deck_bottom_y))

        # deck label (centered over carriageway)
        painter.setFont(QFont('Arial', 9))
        painter.drawText(int(carriageway_start_x + carriageway_width_px/2 - 15),
                         int(deck_top_y + deck_thick_px/2),
                         "Deck")

        # draw left footpath (fixed thickness anchored above girder top)
        if fp_config in ['left', 'both']:
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(QRectF(deck_left_x,
                                   fp_top_y,
                                   left_fp_width * scale,
                                   fp_thick_px))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(int(deck_left_x + 5),
                             int(fp_top_y + fp_thick_px/2),
                             "Footpath")

        # draw right footpath (fixed thickness anchored above girder top)
        if fp_config in ['right', 'both']:
            right_fp_x = deck_left_x + (total_width - right_fp_width) * scale
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawRect(QRectF(right_fp_x,
                                   fp_top_y,
                                   right_fp_width * scale,
                                   fp_thick_px))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(int(right_fp_x + 5),
                             int(fp_top_y + fp_thick_px/2),
                             "Footpath")

        # place crash-barriers using deck_top_y as base so they sit on deck
        cb_y = deck_top_y   # base of crash barrier aligned with deck top
        left_cb_x = left_barrier_x
        right_cb_x = right_barrier_x
        left_cb_x = max(deck_left_x, min(deck_right_x, left_cb_x))
        right_cb_x = max(deck_left_x, min(deck_right_x, right_cb_x))
        self.draw_crash_barrier(painter, left_cb_x, cb_y, scale)
        self.draw_crash_barrier(painter, right_cb_x, cb_y, scale)

        deck_top_line_start = left_barrier_x
        deck_top_line_end = deck_right_x - right_fp_width * scale

        # continuous deck edge lines (bottom spans full width, top spans deck-only region)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(QPointF(deck_left_x, deck_bottom_y), QPointF(deck_right_x, deck_bottom_y))
        painter.drawLine(QPointF(deck_top_line_start, deck_top_y), QPointF(deck_top_line_end, deck_top_y))

        # aliases for downstream code compatibility
        deck_y = deck_bottom_y
        fp_y = fp_bottom_y

        # ----- GIRDERS: robust group placement so none overflow right/left -----
        deck_left_x = deck_start_x
        deck_right_x = deck_start_x + total_width * scale
        deck_width_scaled = deck_right_x - deck_left_x

        n = max(1, int(self.params['num_girders']))
        # half flange in px for guard
        flange_half_px = (self.girder['flange_width'] * scale) / 2.0
        epsilon = 1.0  # tiny padding

        min_allowed_x = deck_left_x + flange_half_px + epsilon
        max_allowed_x = deck_right_x - flange_half_px - epsilon

        # desired spacing in px
        if n > 1:
            desired_spacing_px = self.params['girder_spacing'] * scale
            # maximum spacing that allows the group to be centered inside deck
            max_spacing_if_centered = deck_width_scaled / (n - 1)
            spacing_px = min(desired_spacing_px, max_spacing_if_centered)
            total_span_px = spacing_px * (n - 1)
            start_x = deck_left_x + (deck_width_scaled - total_span_px) / 2.0
            positions = [start_x + i * spacing_px for i in range(n)]
        else:
            positions = [(deck_left_x + deck_right_x) / 2.0]

        # check bounds and compute necessary shift (shift group together)
        min_pos = min(positions)
        max_pos = max(positions)

        shift = 0.0
        if min_pos < min_allowed_x:
            shift = min_allowed_x - min_pos
        if max_pos + shift > max_allowed_x:
            # if shifting right causes exceed on right, compute alternative shift to fit on right side
            shift = min(shift, max_allowed_x - max_pos)
            # if both sides impossible, we will resample positions evenly in available span
            if min_allowed_x > max_allowed_x:
                # degenerate case: no horizontal space -> collapse to center clamp
                positions = [ (min_allowed_x + max_allowed_x) / 2.0 ] * n
            else:
                avail_span = max_allowed_x - min_allowed_x
                if n > 1:
                    spacing_px = avail_span / (n - 1)
                    positions = [min_allowed_x + i * spacing_px for i in range(n)]
                else:
                    positions = [ (min_allowed_x + max_allowed_x) / 2.0 ]

        # apply shift
        positions = [p + shift for p in positions]

        # final safety clamp
        positions = [max(min_allowed_x, min(max_allowed_x, p)) for p in positions]

        # Draw girders and stiffeners
        painter.setBrush(QBrush(QColor(70, 130, 180)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))

        for girder_x in positions:
            self.draw_i_section(painter, girder_x, base_y, scale)
            self.draw_stiffeners(painter, girder_x, base_y, scale)

        # Draw X-bracing between girders (visual)
        if n > 1:
            painter.setPen(QPen(QColor(255, 140, 0), 2))
            painter.setFont(QFont('Arial', 8))
            girder_top_edge = base_y - self.girder['depth'] * scale
            girder_bottom_edge = base_y
            for i in range(n - 1):
                x1 = positions[i]
                x2 = positions[i + 1]
                y_top = girder_top_edge
                y_bot = girder_bottom_edge
                painter.drawLine(QPointF(x1, y_top), QPointF(x2, y_bot))
                painter.drawLine(QPointF(x1, y_bot), QPointF(x2, y_top))
                if i == 0:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y_top + y_bot) / 2
                    painter.drawText(int(mid_x - 35), int(mid_y), "Cross Bracing")

        # Draw railings (at outer edges of footpaths per IRC 105.2.1)
        railing_base_y = fp_top_y

        if fp_config in ['left', 'both']:
            self.draw_railing(painter, deck_left_x, railing_base_y, scale, "left")
        if fp_config in ['right', 'both']:
            self.draw_railing(painter, deck_right_x, railing_base_y, scale, "right")

        # Add dimensions
        # carriageway start/width used for labels (approx)
        carriageway_start_x = deck_left_x + left_fp_width * scale + self.params['crash_barrier_width'] * scale
        carriageway_width_scaled = self.params['carriageway_width'] * scale
        self.add_cross_section_dimensions(painter, deck_start_x, total_width, scale,
                                          carriageway_start_x, carriageway_width_scaled,
                                          base_y, deck_y, fp_y, fp_top_y)

    def draw_i_section(self, painter, x, base_y, scale):
        """Draw I-section girder with proper proportions"""
        visual = getattr(self, 'girder_visual_scale', {})
        d = self.girder['depth'] * scale
        bf = self.girder['flange_width'] * scale * visual.get('flange_width', 1.0)
        tf = self.girder['flange_thickness'] * scale * visual.get('flange_thickness', 1.0)
        tw = self.girder['web_thickness'] * scale * visual.get('web_thickness', 1.0)
        
        # Bottom flange
        painter.drawRect(QRectF(x - bf/2, base_y - tf, bf, tf))
        
        # Web
        web_height = d - 2*tf
        painter.drawRect(QRectF(x - tw/2, base_y - d + tf, tw, web_height))
        
        # Top flange
        painter.drawRect(QRectF(x - bf/2, base_y - d, bf, tf))
        
    def draw_stiffeners(self, painter, x, base_y, scale):
        """Draw vertical stiffeners on girder web per DDCL"""
        visual = getattr(self, 'girder_visual_scale', {})
        flange_scale = visual.get('flange_width', 1.0)
        flange_thick_scale = visual.get('flange_thickness', 1.0)
        web_scale = visual.get('web_thickness', 1.0)

        stiff_width = ((self.girder['flange_width'] * flange_scale) - (self.girder['web_thickness'] * web_scale)) / 2
        stiff_height = self.girder['depth'] - 2 * (self.girder['flange_thickness'] * flange_thick_scale)

        stiff_w = stiff_width * scale
        stiff_h = stiff_height * scale
        tw = self.girder['web_thickness'] * scale * web_scale
        
        painter.setBrush(QBrush(QColor(255, 100, 100)))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Left stiffener
        painter.drawRect(QRectF(x - tw/2 - stiff_w, 
                               base_y - self.girder['depth'] * scale + self.girder['flange_thickness'] * scale,
                               stiff_w, stiff_h))
        
        # Right stiffener
        painter.drawRect(QRectF(x + tw/2, 
                               base_y - self.girder['depth'] * scale + self.girder['flange_thickness'] * scale,
                               stiff_w, stiff_h))
        
    def draw_crash_barrier(self, painter, x, y, scale):
        """Draw crash barrier per IRC specifications"""
        h = self.crash_barrier['height'] * scale
        top_w = 200 * scale
        bot_w = self.crash_barrier['base_width'] * scale
        
        painter.setBrush(QBrush(QColor(255, 165, 0)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        points = [
            QPointF(x + (bot_w - top_w)/2, y - h),
            QPointF(x + (bot_w + top_w)/2, y - h),
            QPointF(x + bot_w, y),
            QPointF(x, y)
        ]
        painter.drawPolygon(QPolygonF(points))
        
        # Add label
        painter.setFont(QFont('Arial', 7))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawText(int(x + 5), int(y - h/2), "Crash\nBarrier")
        
    def draw_railing(self, painter, x, y, scale, side):
        """Draw railing per IRC 5 requirements"""
        h = self.params['railing_height'] * scale
        
        painter.setPen(QPen(QColor(80, 80, 80), 3))
        
        # Post
        painter.drawLine(QPointF(x, y), QPointF(x, y - h))
        
        # Horizontal rails
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        for i in range(1, self.railing['rail_count'] + 1):
            rail_y = y - (h * i / (self.railing['rail_count'] + 1))
            if side == "left":
                painter.drawLine(QPointF(x, rail_y), QPointF(x + 15, rail_y))
            else:
                painter.drawLine(QPointF(x - 15, rail_y), QPointF(x, rail_y))
        
        # Label
        painter.setFont(QFont('Arial', 7))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        if side == "left":
            painter.drawText(int(x + 5), int(y - h - 5), "Railing")
        else:
            painter.drawText(int(x - 35), int(y - h - 5), "Railing")

    def draw_top_view(self, painter):
        """Draw top view with LINE-BASED representation and proper skew angle rotation"""
        width = self.width()
        height = self.height()

        # Calculate scale factors
        margin = 120
        available_width = width - 2 * margin
        available_height = height - 2 * margin - 200

        # Total bridge width (distance between outermost girders in model units)
        if self.params['num_girders'] > 1:
            total_girder_width = (self.params['num_girders'] - 1) * self.params['girder_spacing']
        else:
            total_girder_width = self.params['girder_spacing']

        total_model_width = total_girder_width + 2000  # add annotation margin

        # Scales
        span_scale = available_width / max(self.params['span_length'], 1.0)
        width_scale = available_height / max(total_model_width, 1.0)
        scale = min(span_scale, width_scale)

        # Center of rotation and drawing
        center_x = width / 2
        center_y = height / 2 - 50

        # Title
        painter.setFont(QFont('Arial', 12, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawText(20, 30, "Figure 2: Top View of Bridge showing Girder and Cross Bracing Arrangement")

        # Save painter state before rotation
        painter.save()
        
        # Apply skew angle rotation around center point
        painter.translate(center_x, center_y)
        painter.rotate(self.params['skew_angle'])
        painter.translate(-center_x, -center_y)

        # Compute girder line positions (relative to center)
        span_length_px = self.params['span_length'] * scale
        start_x = center_x - span_length_px / 2
        end_x = center_x + span_length_px / 2

        girder_positions = []
        n = self.params['num_girders']
        
        if n > 1:
            total_width_px = total_girder_width * scale
            start_y = center_y - total_width_px / 2
            spacing_px = self.params['girder_spacing'] * scale
            for i in range(n):
                y_pos = start_y + i * spacing_px
                girder_positions.append(y_pos)
        else:
            total_width_px = self.params['girder_spacing'] * scale
            start_y = center_y - total_width_px / 2
            girder_positions = [center_y]

        # Draw girders as THICK LINES (not rectangles)
        painter.setPen(QPen(QColor(0, 51, 153), 4))  # Dark blue, thick line
        for y_pos in girder_positions:
            painter.drawLine(QPointF(start_x, y_pos), QPointF(end_x, y_pos))

        # Draw cross-bracing as X-pattern LINES between adjacent girders
        painter.setPen(QPen(QColor(255, 140, 0), 2))  # Orange lines for bracing
        
        if self.params['cross_bracing_spacing'] > 0 and n > 1:
            num_sections = max(1, int(self.params['span_length'] / self.params['cross_bracing_spacing']))
            bracing_spacing_px = self.params['cross_bracing_spacing'] * scale
            
            # Draw X-bracing at regular intervals along span
            for section in range(num_sections + 1):
                brace_x = start_x + section * bracing_spacing_px
                if brace_x > end_x:
                    break
                    
                # Draw X pattern between each pair of adjacent girders
                for i in range(len(girder_positions) - 1):
                    y1 = girder_positions[i]
                    y2 = girder_positions[i + 1]
                    
                    # Define small segment width for X pattern
                    segment_width = min(bracing_spacing_px * 0.8, 
                                       self.params['girder_spacing'] * scale * 0.3)
                    
                    x_left = brace_x - segment_width / 2
                    x_right = brace_x + segment_width / 2
                    
                    # Ensure we don't go beyond span limits
                    x_left = max(start_x, x_left)
                    x_right = min(end_x, x_right)
                    
                    # Draw X pattern: two diagonal lines
                    painter.drawLine(QPointF(x_left, y1), QPointF(x_right, y2))  # Top-left to bottom-right
                    painter.drawLine(QPointF(x_left, y2), QPointF(x_right, y1))  # Bottom-left to top-right

        # Draw center lines of bearing on both sides (vertical lines left/right of girders)
        bearing_gap_px = max(40, 0.35 * self.params['girder_spacing'] * scale)
        top_extent = start_y - bearing_gap_px
        bottom_extent = start_y + total_width_px + bearing_gap_px

        left_line_x = start_x - bearing_gap_px
        right_line_x = end_x + bearing_gap_px

        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(QPointF(left_line_x, top_extent), QPointF(left_line_x, bottom_extent))
        painter.drawLine(QPointF(right_line_x, top_extent), QPointF(right_line_x, bottom_extent))

        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.drawText(QPointF(left_line_x - 40, top_extent - 15), "Center Line")
        painter.drawText(QPointF(left_line_x - 45, top_extent), "of Bearing")

        painter.restore()  # Restore to remove rotation

        # Re-apply rotation for dimension lines
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.params['skew_angle'])
        painter.translate(-center_x, -center_y)

        # Draw girder spacing dimension (left side)
        if n > 1:
            dim_x = start_x - 70
            y1 = girder_positions[0]
            y2 = girder_positions[1]
            
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawLine(QPointF(dim_x, y1), QPointF(dim_x, y2))
            
            # Arrows
            arrow_size = 6
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            
            top_arrow = [QPointF(dim_x, y1), 
                        QPointF(dim_x - arrow_size/2, y1 + arrow_size),
                        QPointF(dim_x + arrow_size/2, y1 + arrow_size)]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [QPointF(dim_x, y2),
                           QPointF(dim_x - arrow_size/2, y2 - arrow_size),
                           QPointF(dim_x + arrow_size/2, y2 - arrow_size)]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            painter.setFont(QFont('Arial', 8))
            text_y = (y1 + y2) / 2
            painter.drawText(int(dim_x - 65), int(text_y - 10), "Girder")
            painter.drawText(int(dim_x - 65), int(text_y + 5), "Spacing:")
            painter.drawText(int(dim_x - 65), int(text_y + 20), f"{self.params['girder_spacing']/1000:.2f} m")

        # Draw span length dimension (bottom)
        dim_y = girder_positions[-1] + 60 if girder_positions else center_y + 60
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(QPointF(start_x, dim_y), QPointF(end_x, dim_y))
        
        arrow_size = 6
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        left_arrow = [QPointF(start_x, dim_y),
                     QPointF(start_x + arrow_size, dim_y - arrow_size/2),
                     QPointF(start_x + arrow_size, dim_y + arrow_size/2)]
        painter.drawPolygon(QPolygonF(left_arrow))
        
        right_arrow = [QPointF(end_x, dim_y),
                      QPointF(end_x - arrow_size, dim_y - arrow_size/2),
                      QPointF(end_x - arrow_size, dim_y + arrow_size/2)]
        painter.drawPolygon(QPolygonF(right_arrow))
        
        painter.setFont(QFont('Arial', 9))
        painter.drawText(int((start_x + end_x)/2 - 40), int(dim_y + 15), 
                        f"Span Length: {self.params['span_length']/1000:.1f} m")

        # Draw cross-bracing spacing dimension
        if self.params['cross_bracing_spacing'] > 0:
            brace_end_x = start_x + self.params['cross_bracing_spacing'] * scale
            dim_y2 = dim_y - 25
            
            painter.drawLine(QPointF(start_x, dim_y2), QPointF(brace_end_x, dim_y2))
            
            left_arrow2 = [QPointF(start_x, dim_y2),
                          QPointF(start_x + arrow_size, dim_y2 - arrow_size/2),
                          QPointF(start_x + arrow_size, dim_y2 + arrow_size/2)]
            painter.drawPolygon(QPolygonF(left_arrow2))
            
            right_arrow2 = [QPointF(brace_end_x, dim_y2),
                           QPointF(brace_end_x - arrow_size, dim_y2 - arrow_size/2),
                           QPointF(brace_end_x - arrow_size, dim_y2 + arrow_size/2)]
            painter.drawPolygon(QPolygonF(right_arrow2))
            
            text_x = (start_x + brace_end_x) / 2
            painter.drawText(int(text_x - 85), int(dim_y2 - 8),
                            f"Cross Bracing Spacing: {self.params['cross_bracing_spacing']/1000:.2f} m")

        painter.restore()  # Restore from rotation

        # Draw skew angle annotation (only if skew is non-zero)
        if abs(self.params['skew_angle']) > 0.1:
            self.draw_skew_annotation(painter, center_x, center_y, scale)

        # Notes section (not rotated)
        self.add_top_view_notes(painter, height)


    def draw_girder_spacing_dimension(self, painter, start_x, start_y, scale):
        """Draw girder spacing dimension on left side"""
        dim_x = start_x - 70
        y1 = start_y
        y2 = start_y + self.params['girder_spacing'] * scale
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(QPointF(dim_x, y1), QPointF(dim_x, y2))
        
        # Arrows
        arrow_size = 6
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        # Top arrow
        top_arrow = [
            QPointF(dim_x, y1),
            QPointF(dim_x - arrow_size/2, y1 + arrow_size),
            QPointF(dim_x + arrow_size/2, y1 + arrow_size)
        ]
        painter.drawPolygon(QPolygonF(top_arrow))
        
        # Bottom arrow
        bottom_arrow = [
            QPointF(dim_x, y2),
            QPointF(dim_x - arrow_size/2, y2 - arrow_size),
            QPointF(dim_x + arrow_size/2, y2 - arrow_size)
        ]
        painter.drawPolygon(QPolygonF(bottom_arrow))
        
        # Text - centered vertically
        text_x = dim_x - 65
        text_y = (y1 + y2) / 2
        painter.setFont(QFont('Arial', 8))
        painter.drawText(int(text_x), int(text_y - 15), "Girder Spacing")
        painter.drawText(int(text_x), int(text_y), "(Equal):")
        painter.drawText(int(text_x), int(text_y + 15), f"{self.params['girder_spacing']/1000:.2f} m")

    def draw_bottom_dimensions(self, painter, start_x, start_y, scale, total_girder_width):
        """Draw span length and cross-bracing spacing dimensions at bottom"""
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Calculate dimension line Y position
        if self.params['num_girders'] > 1:
            dim_y = start_y + total_girder_width * scale + 60
        else:
            dim_y = start_y + 60
        
        span_end_x = start_x + self.params['span_length'] * scale
        
        # Draw span length dimension line
        painter.drawLine(QPointF(start_x, dim_y), QPointF(span_end_x, dim_y))
        
        # Draw arrows for span length
        arrow_size = 6
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        left_arrow = [
            QPointF(start_x, dim_y),
            QPointF(start_x + arrow_size, dim_y - arrow_size/2),
            QPointF(start_x + arrow_size, dim_y + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(left_arrow))
        
        right_arrow = [
            QPointF(span_end_x, dim_y),
            QPointF(span_end_x - arrow_size, dim_y - arrow_size/2),
            QPointF(span_end_x - arrow_size, dim_y + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(right_arrow))
        
        # Span length text
        text_x = (start_x + span_end_x) / 2
        painter.drawText(int(text_x - 40), int(dim_y + 15), f"Span Length: {self.params['span_length']/1000:.1f} m")
        
        # Cross bracing spacing dimension (above span length)
        if self.params['cross_bracing_spacing'] > 0:
            brace_end_x = start_x + self.params['cross_bracing_spacing'] * scale
            dim_y2 = dim_y - 25
            
            painter.drawLine(QPointF(start_x, dim_y2), QPointF(brace_end_x, dim_y2))
            
            left_arrow2 = [
                QPointF(start_x, dim_y2),
                QPointF(start_x + arrow_size, dim_y2 - arrow_size/2),
                QPointF(start_x + arrow_size, dim_y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow2))
            
            right_arrow2 = [
                QPointF(brace_end_x, dim_y2),
                QPointF(brace_end_x - arrow_size, dim_y2 - arrow_size/2),
                QPointF(brace_end_x - arrow_size, dim_y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow2))
            
            text_x2 = (start_x + brace_end_x) / 2
            painter.drawText(int(text_x2 - 85), int(dim_y2 - 8), 
                            f"Cross Bracing Spacing (Equal): {self.params['cross_bracing_spacing']/1000:.2f} m")

    def draw_skew_annotation(self, painter, start_x, center_y, scale):
        """Draw precise skew angle annotation"""
        annot_x_center = start_x + self.params['span_length'] * scale / 2
        
        # Draw perpendicular line to girder (green solid line)
        painter.setPen(QPen(QColor(0, 128, 0), 2))  # Green
        perp_len = 100
        painter.drawLine(QPointF(annot_x_center - perp_len/2, center_y),
                       QPointF(annot_x_center + perp_len/2, center_y))
        
        # Draw bearing center line (red solid line) with skew angle
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        angle_rad = math.radians(self.params['skew_angle'])
        dx = perp_len * math.sin(angle_rad) / 2
        dy = perp_len * math.cos(angle_rad) / 2
        
        painter.drawLine(QPointF(annot_x_center - dx, center_y - dy),
                       QPointF(annot_x_center + dx, center_y + dy))
        
        # Draw arc showing angle
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        arc_radius = 35
        arc_rect = QRectF(annot_x_center - arc_radius, center_y - arc_radius, 
                         2 * arc_radius, 2 * arc_radius)
        
        start_angle = 0 * 16
        span_angle = int(self.params['skew_angle'] * 16)
        painter.drawArc(arc_rect, start_angle, span_angle)
        
        # Labels
        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawText(int(annot_x_center + 45), int(center_y + 5), 
                       f"Skew Angle: {self.params['skew_angle']}°")
        
        # Line labels
        painter.setFont(QFont('Arial', 8))
        painter.setPen(QPen(QColor(0, 128, 0), 1))
        painter.drawText(int(annot_x_center - perp_len/2 - 45), int(center_y - 8), 
                       "Perpendicular to Girder")
        
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        label_x = annot_x_center + dx + 10
        label_y = center_y + dy - 5
        painter.drawText(int(label_x), int(label_y), "Bearing Center Line")

    def add_top_view_notes(self, painter, height):
        """Add notes section per DDCL Figure 2"""
        notes_y = height - 150
        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawText(20, notes_y, "Notes:")
        
        painter.setFont(QFont('Arial', 8))
        notes = [
            f"1. Girder (shown in blue rectangles) spacing: > 1 m and < 24 m.",
            f"2. No. of girders: >2 and <12",
            f"3. Span length of girder: > 20 m and < 45 m.",
            f"4. Cross bracing (shown in orange rectangles) spacing: > 1 m and < span length.",
            "5. Red line shows the center line of bearing. Bearing refers to support below girder.",
            "6. Skew angle is the angle between green line (which is perpendicular to girder line that is",
            "    horizontal) and red line (bearing). Skew angle should vary between -15 to +15 degrees."
        ]
        
        for i, note in enumerate(notes):
            if "girder" in note.lower() and "spacing" in note.lower():
                painter.setPen(QPen(QColor(0, 51, 153), 1))
            elif "cross bracing" in note.lower():
                painter.setPen(QPen(QColor(255, 140, 0), 1))
            elif "red line" in note.lower():
                painter.setPen(QPen(QColor(255, 0, 0), 1))
            elif "green line" in note.lower():
                painter.setPen(QPen(QColor(0, 128, 0), 1))
            else:
                painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(20, notes_y + 20 + i * 15, note)

    def draw_dimension_line(self, painter, x1, y1, x2, y2, text):
        """Draw horizontal dimension line with arrows and text"""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw arrows
        arrow_size = 6
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        # Left arrow
        left_arrow = [
            QPointF(x1, y1),
            QPointF(x1 + arrow_size, y1 - arrow_size/2),
            QPointF(x1 + arrow_size, y1 + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(left_arrow))
        
        # Right arrow
        right_arrow = [
            QPointF(x2, y2),
            QPointF(x2 - arrow_size, y2 - arrow_size/2),
            QPointF(x2 - arrow_size, y2 + arrow_size/2)
        ]
        painter.drawPolygon(QPolygonF(right_arrow))
        
        # Draw text
        text_x = (x1 + x2) / 2
        text_y = y1 - 8
        
        # Handle multiline text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            text_width = len(line) * 5
            painter.drawText(int(text_x - text_width/2), int(text_y - i * 12), line)
    
    def draw_vertical_dimension(self, painter, x1, y1, x2, y2, text):
        """Draw vertical dimension line with arrows and text"""
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw arrows
        arrow_size = 6
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        # Top arrow
        top_arrow = [
            QPointF(x2, y2),
            QPointF(x2 - arrow_size/2, y2 + arrow_size),
            QPointF(x2 + arrow_size/2, y2 + arrow_size)
        ]
        painter.drawPolygon(QPolygonF(top_arrow))
        
        # Bottom arrow
        bottom_arrow = [
            QPointF(x1, y1),
            QPointF(x1 - arrow_size/2, y1 - arrow_size),
            QPointF(x1 + arrow_size/2, y1 - arrow_size)
        ]
        painter.drawPolygon(QPolygonF(bottom_arrow))
        
        # Draw text
        text_x = x1 - 10
        text_y = (y1 + y2) / 2
        
        # Handle multiline text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            painter.drawText(int(text_x - len(line) * 5), int(text_y + i * 12), line)
    # --- END moved methods ---

    def add_cross_section_dimensions(self, painter, deck_start_x, total_width, scale, 
                                     carriageway_start_x, carriageway_width_scaled,
                                     base_y, deck_y, fp_y, fp_top_y):
        """Add dimension annotation for cross-section (kept simple)"""
        # Example dimension: overall width
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        x1 = deck_start_x
        x2 = deck_start_x + total_width * scale
        y = base_y + 30
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))
        painter.drawText(int((x1 + x2)/2 - 40), int(y + 15), f"Overall Width: {total_width/1000:.2f} m")


class BridgeDesignGUI(QMainWindow):
    """Main window for bridge design application per DDCL"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steel Girder Bridge - Dynamic 2D CAD Model (IRC/IS/DDCL Standards)")

        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        avail_width = available.width() if available else 1400
        avail_height = available.height() if available else 900

        default_width = min(1400, max(1000, avail_width - 120))
        default_height = min(900, max(700, avail_height - 120))

        self.resize(default_width, default_height)
        self.setMinimumSize(900, 650)
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create layout
        layout = QHBoxLayout(main_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create control panel
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # Create CAD view
        self.cad_widget = BridgeCADWidget()
        splitter.addWidget(self.cad_widget)
        
        # Set splitter sizes
        splitter.setSizes([400, 1200])
        
    def create_control_panel(self):
        """Create control panel per DDCL input requirements"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Bridge Parameters\n(IRC/IS/DDCL Standards)")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 13, QFont.Bold))
        title.setStyleSheet("background-color: #1e40af; color: white; padding: 12px; border-radius: 5px;")
        layout.addWidget(title)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Create parameter groups per DDCL 2.1
        self.create_general_bridge_details(scroll_layout)
        self.create_geometry_group(scroll_layout)
        self.create_deck_footpath_group(scroll_layout)
        self.create_view_controls(scroll_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Action buttons
        self.create_action_buttons(layout)
        
        return panel
        
    def create_general_bridge_details(self, layout):
        """Create general bridge details per DDCL 2.1.2"""
        group = QGroupBox("General Bridge Details (DDCL 2.1.2)")
        g = QGridLayout()
        
        r = 0
        
        # Span length (DDCL: 20-45m)
        g.addWidget(QLabel("Span (m):"), r, 0)
        self.span_input = QDoubleSpinBox()
        self.span_input.setRange(20, 45)
        self.span_input.setValue(35)
        self.span_input.setSingleStep(0.5)
        self.span_input.setDecimals(1)
        self.span_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.span_input, r, 1)
        g.addWidget(QLabel("[20-45m, DDCL]"), r, 2)
        r += 1
        
        # Carriageway width (DDCL: ≥4.25m per IRC 5)
        g.addWidget(QLabel("Carriageway Width (m):"), r, 0)
        self.carriageway_input = QDoubleSpinBox()
        self.carriageway_input.setRange(4.25, 24.0)
        self.carriageway_input.setValue(10.5)
        self.carriageway_input.setSingleStep(0.25)
        self.carriageway_input.setDecimals(2)
        self.carriageway_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.carriageway_input, r, 1)
        g.addWidget(QLabel("[≥4.25m, IRC 5]"), r, 2)
        r += 1
        
        # Footpath configuration (DDCL 2.1.2)
        g.addWidget(QLabel("Footpath:"), r, 0)
        self.footpath_combo = QComboBox()
        self.footpath_combo.addItems(["None", "Left", "Right", "Both"])
        self.footpath_combo.setCurrentText("Both")
        self.footpath_combo.currentTextChanged.connect(self.on_footpath_changed)
        g.addWidget(self.footpath_combo, r, 1)
        g.addWidget(QLabel("[IRC 5 Cl. 101.41]"), r, 2)
        r += 1
        
        # Skew angle (DDCL: 0° default, recommend ≤30° per IRC 5)
        g.addWidget(QLabel("Skew Angle (°):"), r, 0)
        self.skew_input = QDoubleSpinBox()
        self.skew_input.setRange(-15.0, 15.0)
        self.skew_input.setValue(0.0)
        self.skew_input.setSingleStep(1.0)
        self.skew_input.setDecimals(1)
        self.skew_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.skew_input, r, 1)
        g.addWidget(QLabel("[-15° to +15°]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_geometry_group(self, layout):
        """Create bridge geometry controls per DDCL 2.1.4.1"""
        group = QGroupBox("Bridge Geometry (DDCL 2.1.4.1)")
        g = QGridLayout()
        
        r = 0
        
        # Number of girders (DDCL: 2-12)
        g.addWidget(QLabel("Number of Girders:"), r, 0)
        self.girders_input = QSpinBox()
        self.girders_input.setRange(2, 12)
        self.girders_input.setValue(4)
        self.girders_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.girders_input, r, 1)
        g.addWidget(QLabel("[2-12, DDCL]"), r, 2)
        r += 1
        
        # Girder spacing (DDCL: 1-24m)
        g.addWidget(QLabel("Girder Spacing (m):"), r, 0)
        self.spacing_input = QDoubleSpinBox()
        self.spacing_input.setRange(1.0, 24.0)
        self.spacing_input.setValue(2.75)
        self.spacing_input.setSingleStep(0.25)
        self.spacing_input.setDecimals(2)
        self.spacing_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.spacing_input, r, 1)
        g.addWidget(QLabel("[1-24m, DDCL]"), r, 2)
        r += 1
        
        # Cross bracing spacing (DDCL: ≥1m, ≤span)
        g.addWidget(QLabel("Cross-Bracing Spacing (m):"), r, 0)
        self.bracing_spacing_input = QDoubleSpinBox()
        self.bracing_spacing_input.setRange(1.0, 45.0)
        self.bracing_spacing_input.setValue(3.5)
        self.bracing_spacing_input.setSingleStep(0.5)
        self.bracing_spacing_input.setDecimals(2)
        self.bracing_spacing_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.bracing_spacing_input, r, 1)
        g.addWidget(QLabel("[≥1m, DDCL]"), r, 2)
        r += 1
        
        # Crash barrier width (DDCL: typical 500mm)
        g.addWidget(QLabel("Crash Barrier Width (mm):"), r, 0)
        self.cb_width_input = QDoubleSpinBox()
        self.cb_width_input.setRange(200, 2000)
        self.cb_width_input.setValue(500)
        self.cb_width_input.setSingleStep(50)
        self.cb_width_input.setDecimals(0)
        self.cb_width_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.cb_width_input, r, 1)
        g.addWidget(QLabel("[IRC typical]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_deck_footpath_group(self, layout):
        """Create deck and footpath controls per DDCL 2.1.4.1"""
        group = QGroupBox("Deck / Footpath / Railing (DDCL 2.1.4.1)")
        g = QGridLayout()
        
        r = 0
        
        # Deck thickness (DDCL: 0-500mm)
        g.addWidget(QLabel("Deck Thickness (mm):"), r, 0)
        self.deck_input = QDoubleSpinBox()
        self.deck_input.setRange(0, 500)
        self.deck_input.setValue(200)
        self.deck_input.setSingleStep(10)
        self.deck_input.setDecimals(0)
        self.deck_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.deck_input, r, 1)
        g.addWidget(QLabel("[0-500mm]"), r, 2)
        r += 1
        
        # Footpath width (DDCL: 0-10m, IRC 5 min requirements)
        g.addWidget(QLabel("Footpath Width (m):"), r, 0)
        self.fp_width_input = QDoubleSpinBox()
        self.fp_width_input.setRange(0.0, 10.0)
        self.fp_width_input.setValue(1.5)
        self.fp_width_input.setSingleStep(0.1)
        self.fp_width_input.setDecimals(2)
        self.fp_width_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.fp_width_input, r, 1)
        g.addWidget(QLabel("[0-10m, IRC 5]"), r, 2)
        r += 1
        
        # Footpath thickness (DDCL: 0-500mm)
        g.addWidget(QLabel("Footpath Thickness (mm):"), r, 0)
        self.fp_thick_input = QDoubleSpinBox()
        self.fp_thick_input.setRange(0, 500)
        self.fp_thick_input.setValue(200)
        self.fp_thick_input.setSingleStep(10)
        self.fp_thick_input.setDecimals(0)
        self.fp_thick_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.fp_thick_input, r, 1)
        g.addWidget(QLabel("[0-500mm]"), r, 2)
        r += 1
        
        # Railing height (IRC 5 requirements)
        g.addWidget(QLabel("Railing Height (mm):"), r, 0)
        self.railing_height_input = QDoubleSpinBox()
        self.railing_height_input.setRange(200, 2000)
        self.railing_height_input.setValue(1000)
        self.railing_height_input.setSingleStep(50)
        self.railing_height_input.setDecimals(0)
        self.railing_height_input.valueChanged.connect(self.update_bridge)
        g.addWidget(self.railing_height_input, r, 1)
        g.addWidget(QLabel("[IRC 5 Cl. 109.7]"), r, 2)
        r += 1
        
        group.setLayout(g)
        layout.addWidget(group)
        
    def create_view_controls(self, layout):
        """Create view selection controls"""
        group = QGroupBox("View Controls")
        v = QVBoxLayout()
        
        # View selector
        v.addWidget(QLabel("Select View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Cross-Section (Figure 1)", "Top View (Figure 2)"])
        self.view_combo.currentIndexChanged.connect(self.on_view_changed)
        v.addWidget(self.view_combo)
        
        group.setLayout(v)
        layout.addWidget(group)
        
    def create_action_buttons(self, layout):
        """Create action buttons"""
        btn_layout = QGridLayout()
        
        # Export PNG button
        self.export_btn = QPushButton("Export PNG")
        self.export_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px; font-weight: bold;")
        self.export_btn.clicked.connect(self.export_png)
        btn_layout.addWidget(self.export_btn, 0, 0)
        
        # Reset button
        self.reset_btn = QPushButton("Reset to DDCL Defaults")
        self.reset_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; font-weight: bold;")
        self.reset_btn.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(self.reset_btn, 0, 1)
        
        # Calculate button (per DDCL 2.2.1)
        self.calc_btn = QPushButton("Calculate Design")
        self.calc_btn.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; font-weight: bold;")
        self.calc_btn.clicked.connect(self.calculate_design)
        btn_layout.addWidget(self.calc_btn, 1, 0, 1, 2)
        
        layout.addLayout(btn_layout)
        
    def on_footpath_changed(self, value):
        """Handle footpath configuration change"""
        self.update_bridge()
        
    def on_view_changed(self, idx):
        """Handle view change"""
        if idx == 0:
            self.cad_widget.set_view_type('cross-section')
        else:
            self.cad_widget.set_view_type('top-view')
            
    def update_bridge(self):
        """Collect values and update CAD widget per DDCL"""
        params = {}
        
        # General bridge details (convert m -> mm where needed)
        params['span_length'] = float(self.span_input.value()) * 1000.0
        params['carriageway_width'] = float(self.carriageway_input.value()) * 1000.0
        params['skew_angle'] = float(self.skew_input.value())
        params['footpath_config'] = self.footpath_combo.currentText().lower()
        
        # Bridge geometry
        params['num_girders'] = int(self.girders_input.value())
        params['girder_spacing'] = float(self.spacing_input.value()) * 1000.0
        params['cross_bracing_spacing'] = float(self.bracing_spacing_input.value()) * 1000.0
        params['crash_barrier_width'] = float(self.cb_width_input.value())
        
        # Deck and footpath
        params['deck_thickness'] = float(self.deck_input.value())
        params['footpath_width'] = float(self.fp_width_input.value()) * 1000.0
        params['footpath_thickness'] = float(self.fp_thick_input.value())
        params['railing_height'] = float(self.railing_height_input.value())
        
        # Validate cross-bracing spacing per DDCL
        if params['cross_bracing_spacing'] > params['span_length']:
            params['cross_bracing_spacing'] = params['span_length']
            self.bracing_spacing_input.setValue(params['span_length'] / 1000.0)
        
        # Update CAD widget
        self.cad_widget.update_params(params)
        
    def reset_defaults(self):
        """Reset to DDCL example values (Table on page 9)"""
        # DDCL Table 5 example values
        self.span_input.setValue(35.0)
        self.girders_input.setValue(4)
        self.spacing_input.setValue(2.75)
        self.bracing_spacing_input.setValue(3.5)
        self.carriageway_input.setValue(10.5)
        self.skew_input.setValue(0.0)
        self.deck_input.setValue(200)
        self.fp_width_input.setValue(1.5)
        self.fp_thick_input.setValue(200)
        self.cb_width_input.setValue(500)
        self.railing_height_input.setValue(1000)
        self.footpath_combo.setCurrentText("Both")
        self.view_combo.setCurrentIndex(0)
        
        # Update display
        self.update_bridge()
        
    def calculate_design(self):
        """Placeholder for design calculations per DDCL Chapter 3"""
        # This would implement DDCL 3.1, 3.2, 3.3 calculations
        # For now, just show a message
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Calculate Design", 
                               "Design calculation per DDCL Chapter 3:\n\n"
                               "• Preliminary sizing (DDCL 3.1)\n"
                               "• Load evaluation (DDCL 3.2)\n"
                               "• Post-analysis design (DDCL 3.3)\n\n"
                               "This feature would perform full structural analysis.")
        
    def export_png(self):
        """Export current CAD view to PNG"""
        view_name = "cross_section" if self.view_combo.currentIndex() == 0 else "top_view"
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Bridge CAD Drawing", 
            f"bridge_{view_name}.png", 
            "PNG Files (*.png)"
        )
        if fname:
            pix = QPixmap(self.cad_widget.size())
            self.cad_widget.render(pix)
            pix.save(fname, "PNG")
            
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export Successful", 
                                   f"Bridge drawing saved to:\n{fname}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = BridgeDesignGUI()
    window.show()
    
    # Initialize with DDCL defaults
    window.reset_defaults()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
