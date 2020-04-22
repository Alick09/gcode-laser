import numpy as np
from image_processing.base import ImageWriter


class ScanImageWriter(ImageWriter):
    def set_image(self, path, levels):
        super().set_image(path)
        #self.image = np.hstack((self.image[1080:1480,1900:2100], self.image[2540:2940, 1840:2040]))
        self.levels = levels

    def _prepare(self):
        super()._prepare()
        self.image = self.image[:,:,0]
        count = []
        for i in range(256):
            count.append((i, (self.image == i).sum()))
        thresholds = []
        for x in sorted(count, key=lambda x: -x[1]):
            thresholds.append(x[0])
            if len(thresholds) == self.levels + 1:
                break
        
        self.level_image = np.zeros(self.image.shape, dtype=np.uint8)
        last_t = None
        for t in sorted(thresholds, reverse=True):
            if last_t is not None:
                t_ = (t+last_t)/2
                self.level_image += (self.image < t_).astype(np.uint8)
            last_t = t

    def __values(self, start, end, precision_pix):
        factor = -1 if (end[0] - start[0]) * (end[1] - start[1]) < 0 else 1
        if start[0] < end[0]:
            xs = range(start[0], end[0], precision_pix)
        if start[0] > end[0]:
            xs = reversed(list(range(end[0], start[0], precision_pix)))
        for x in xs:
            y = int(start[1] + factor * (x - start[0]))
            yield self.level_image[y, x], (x, y)

    def __lines(self, distance_pix, shift, crossed=False):
        hp, wp = self.level_image.shape
        swap = False
        for i in range(-hp + shift, wp, distance_pix):
            start = (i, 0) if i >= 0 else (0, -i)
            end = (i+hp-1, hp-1) if i+hp-1 < wp else (wp-1, wp-i-1)

            if start[0] < end[0]:

                if crossed:
                    start = (wp-1-start[0], start[1])
                    end = (wp-1-end[0], end[1])

                if swap:
                    start, end = end, start
                swap = not swap

                yield start, end

    def __go_pattern(self, distance_pix, shift, min_level, precision_pix, crossed=False):
        for line_start, line_end in self.__lines(distance_pix, shift, crossed):
            start_point = None
            end_point = None
            for v, p in self.__values(line_start, line_end, precision_pix):
                if v >= min_level:
                    if start_point is None:
                        start_point = p
                    else:
                        end_point = p
                else:
                    if end_point is not None:
                        self._place_line(start_point, end_point)
                    start_point = end_point = None
            if end_point is not None:
                self._place_line(start_point, end_point)

    def process(self, distance_mm = 2, precision_mm = 0.2):
        super().process()
        assert self.levels <= 3, "Not implemented for level count > 3"

        distance_pix = int(distance_mm/self.pixel_size)
        if self.levels > 2:
            distance_pix = distance_pix + (distance_pix % 2)
        precision_pix = max(1, int(precision_mm/self.pixel_size))

        self.__go_pattern(distance_pix, 0, 1, precision_pix)
        if self.levels > 1:
            self.__go_pattern(distance_pix, 0, 2, precision_pix, crossed=True)
            if self.levels > 2:
                self.__go_pattern(distance_pix, distance_pix//2, 3, precision_pix)
                self.__go_pattern(distance_pix, distance_pix//2, 3, precision_pix, crossed=True)

