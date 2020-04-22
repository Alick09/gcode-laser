import numpy as np
import cv2

def clamp(x, minv, maxv):
    if x < minv:
        return minv
    if x > maxv:
        return maxv
    return x

class Shape(object):
    def __init__(self, img_w, img_h):
        self.img_w = img_w
        self.img_h = img_h
        self.__stamp = None

    def _get_bbox(self):
        """ Returns x, y, w, h """
        raise NotImplementedError()

    def _draw(self, img):
        raise NotImplementedError()

    def _copy(self):
        raise NotImplementedError()

    def _clamp(self, x, y):
        return clamp(x, 0, self.img_w - 1), clamp(y, 0, self.img_h - 1)

    def get_stamp(self):
        """ Returns (x, y, image) """
        if self.__stamp is None:
            x, y, w, h = self._get_bbox()
            img = np.zeros((h, w), dtype=np.int16)
            self._draw(img)
            self.__stamp = x, y, img
        return self.__stamp

    def _morph_inplace(self, temperature):
        raise NotImplementedError()

    def morph(self, temperature):
        """ Returns morphed shape. Lower temperature is lower morphs """
        res = self._copy()
        res._morph_inplace(temperature)
        return res

    def to_array(self):
        raise NotImplementedError()

    @staticmethod
    def from_array(self, arr):
        raise NotImplementedError()


class LineShape(Shape):
    def __init__(self, img_w, img_h, copy_from=None):
        super().__init__(img_w, img_h)
        if copy_from is None:
            self.x1, self.x2 = map(int, (img_w * np.random.random(2)).tolist())
            self.y1, self.y2 = map(int, (img_h * np.random.random(2)).tolist())
        else:
            if isinstance(copy_from, LineShape):
                self.x1, self.y1, self.x2, self.y2 = copy_from.x1, copy_from.y1, copy_from.x2, copy_from.y2
            else:
                x1, y1, x2, y2 = map(int, copy_from)
                self.x1, self.y1 = self._clamp(x1, y1)
                self.x2, self.y2 = self._clamp(x2, y2)

    def _get_bbox(self):
        self.bbox = min(self.x1, self.x2), min(self.y1, self.y2), abs(self.x1 - self.x2) + 1, abs(self.y1 - self.y2) + 1
        return self.bbox

    def _draw(self, img):
        cv2.line(img, (self.x1-self.bbox[0], self.y1-self.bbox[1]), (self.x2-self.bbox[0], self.y2-self.bbox[1]), 85, 1)

    def __get_morphing_shift(self, temperature):
        if temperature > 0:
            scale = temperature
            dx = int(self.img_w * 2 * (np.random.random() - 0.5) * scale)
            dy = int(self.img_h * 2 * (np.random.random() - 0.5) * scale)
        else:
            dx, dy = 0, 0

        while dx == 0 and dy == 0:
            dx = np.random.randint(-1, 2)
            dy = np.random.randint(-1, 2)

        return dx, dy

    def _copy(self):
        return LineShape(self.img_w, self.img_h, copy_from=self)

    def _morph_inplace(self, temperature):
        d1, d2 = [self.__get_morphing_shift(temperature) for i in range(2)]
        self.x1, self.y1 = self._clamp(self.x1 + d1[0], self.y1 + d1[1])
        self.x2, self.y2 = self._clamp(self.x2 + d2[0], self.y2 + d2[1])

    def to_array(self):
        return np.array([self.x1, self.y1, self.x2, self.y2])

    @staticmethod
    def from_array(self, arr):
        return LineShape(self.img_w, self.img_h, arr)