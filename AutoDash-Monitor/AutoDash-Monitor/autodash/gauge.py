from PyQt5.QtCore import Qt, QRectF, pyqtProperty, QPointF
from PyQt5.QtGui import QPainter, QPen, QFont, QConicalGradient, QColor
from PyQt5.QtWidgets import QWidget

class Gauge(QWidget):
    def __init__(self, minimum=0, maximum=100, value=0, unit="%", label="Gauge", parent=None):
        super().__init__(parent)
        self._min = minimum
        self._max = maximum
        self._value = value
        self._unit = unit
        self._label = label
        self.setMinimumSize(140, 140)

    def setRange(self, minimum, maximum):
        self._min, self._max = minimum, maximum
        self.update()

    def setUnit(self, unit):
        self._unit = unit; self.update()

    def setLabel(self, label):
        self._label = label; self.update()

    def getValue(self):
        return self._value

    def setValue(self, v):
        if v is None: v = 0
        v = float(max(self._min, min(self._max, v)))
        if v != self._value:
            self._value = v
            self.update()

    value = pyqtProperty(float, fget=getValue, fset=setValue)

    def paintEvent(self, e):
        side = min(self.width(), self.height())
        rect = QRectF((self.width()-side)/2+10, (self.height()-side)/2+10, side-20, side-20)
        start_angle = 225  # degrees
        span_angle = 270
        with QPainter(self) as p:
            p.setRenderHint(QPainter.Antialiasing)
            # background arc
            pen = QPen(QColor(30, 42, 54), 14)
            p.setPen(pen)
            p.drawArc(rect, int((90-start_angle)*16), int(-span_angle*16))

            # progress arc
            frac = 0 if self._max == self._min else (self._value - self._min)/(self._max - self._min)
            frac = max(0.0, min(1.0, frac))
            # gradient-ish pen
            pen2 = QPen(QColor(55, 149, 255), 16)
            p.setPen(pen2)
            p.drawArc(rect, int((90-start_angle)*16), int(-span_angle*frac*16))

            # labels
            p.setPen(QColor(158, 207, 255))
            font = QFont(self.font())
            font.setPointSize(int(side/10))
            font.setBold(True)
            p.setFont(font)
            value_text = f"{int(self._value)}{self._unit}"
            p.drawText(self.rect(), Qt.AlignCenter, value_text)

            # bottom label
            p.setPen(QColor(120, 160, 200))
            font2 = QFont(self.font())
            font2.setPointSize(int(side/14))
            p.setFont(font2)
            p.drawText(self.rect().adjusted(0, int(side*0.35), 0, 0), Qt.AlignHCenter | Qt.AlignTop, self._label)
