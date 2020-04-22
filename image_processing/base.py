import numpy as np
import cv2
import logging


class ImageWriter(object):
    RENDER_PIXELS_IN_MM = 8

    def __init__(self, gcode_writer=None):
        self.gcode = gcode_writer
        self.logger = logging.getLogger("image")
        self.image = None
        self.w = None
        self.h = None
        self.pixel_size = None
        if self.gcode is None:
            self.logger.warning("All operations with gcode will be ignored. Set it in constructor if you want to fix it.")

    def set_image(self, path):
        self.image = cv2.imread(path)

    def set_width(self, width_in_mm):
        self.w = width_in_mm

    def __convert_to_mm(self, point):
        return (point[0] * self.pixel_size, point[1] * self.pixel_size)

    def render(self):
        cv2.imshow("render", self.render_image)
        cv2.waitKey()

    def save(self, path):
        if self.gcode is None:
            self.logger.warning("Gcode wouldn't be saved. Give it to constructor to solve this issue.")
        else:
            self.gcode.save(path)

    def _place_line(self, start, end):
        start, end = [self.__convert_to_mm(p) for p in [start, end]]
        cv2.line(
            self.render_image, 
            (int(start[0]*self.RENDER_PIXELS_IN_MM), int(start[1]*self.RENDER_PIXELS_IN_MM)),
            (int(end[0]*self.RENDER_PIXELS_IN_MM), int(end[1]*self.RENDER_PIXELS_IN_MM)),
            0, 1
        )
        if self.gcode is not None:
            self.gcode.draw_line(self.w - start[0], start[1], self.w - end[0], end[1])

    def _image_resized(self, ratio_kept=False):
        if not ratio_kept:
            self.h = int(self.image.shape[0] * self.w / self.image.shape[1])
            self.render_image = np.zeros((self.h * self.RENDER_PIXELS_IN_MM, self.w * self.RENDER_PIXELS_IN_MM), dtype=np.uint8)
            self.render_image[:,:] = 255
        self.pixel_size = self.w / (self.image.shape[1] - 1)

    def _prepare(self):
        self._image_resized()

    def process(self):
        self._prepare()
