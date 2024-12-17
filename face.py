import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QTimer

class EyesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set window to fullscreen
        self.showFullScreen()
        self.setStyleSheet("background-color: white;")
        
        # Initialize blinking state
        self.is_blinking = False
        
        # Set up blink timer
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        
        # Blink every 5 seconds
        self.blink_timer.start(5000)
        
        # Timer for blink duration
        self.blink_duration = QTimer()
        self.blink_duration.timeout.connect(self.open_eyes)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get window dimensions
        width = self.width()
        height = self.height()
        
        # Calculate eye dimensions and positions
        eye_width = width // 3  # Increased from 1/6 to 1/4 of screen width
        eye_height = height // 3  # Increased from 1/4 to 1/3 of screen height
        eye_spacing = eye_width // 3  # Reduced spacing to accommodate larger eyes
        
        # Calculate center position
        center_x = width // 2 + width // 64
        # center_y = height // 2
        center_y = (height // 2) - (height // 8)
        
        # Draw eyes
        if not self.is_blinking:
            # Draw white of eyes
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(Qt.GlobalColor.white, 3))
            
            # Left eye
            painter.drawEllipse(center_x - eye_spacing - eye_width, 
                              center_y - eye_height//2,
                              eye_width, eye_height)
            
            # Right eye
            painter.drawEllipse(center_x + eye_spacing, 
                              center_y - eye_height//2,
                              eye_width, eye_height)
            
            # Draw pupils
            painter.setBrush(QColor(0, 0, 0))
            pupil_size = eye_width // 2 + eye_width // 4
            
            # Left pupil
            painter.drawEllipse(center_x - eye_spacing - eye_width//2 - pupil_size//2,
                              center_y - pupil_size//2,
                              pupil_size, pupil_size)
            
            # Right pupil
            painter.drawEllipse(center_x + eye_spacing + eye_width//2 - pupil_size//2,
                              center_y - pupil_size//2,
                              pupil_size, pupil_size)
        else:
            # Draw closed eyes (just lines)
            painter.setPen(QPen(Qt.GlobalColor.black, 5))
            
            # Left eye
            painter.drawLine(center_x - eye_spacing - eye_width, center_y,
                           center_x - eye_spacing, center_y)
            
            # Right eye
            painter.drawLine(center_x + eye_spacing, center_y,
                           center_x + eye_spacing + eye_width, center_y)
    
    def blink(self):
        self.is_blinking = True
        self.update()
        # Keep eyes closed for 200ms
        self.blink_duration.start(200)
    
    def open_eyes(self):
        self.is_blinking = False
        self.update()
    
    def keyPressEvent(self, event):
        # Press 'Esc' to exit
        if event.key() == Qt.Key.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EyesWindow()
    sys.exit(app.exec())