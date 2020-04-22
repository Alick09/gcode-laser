if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.abspath('..'))
    
import numpy as np
import cv2
from image_processing.base import ImageWriter
from image_processing.smart_fit_shapes import LineShape

__all__ = ['SmartFitImageWriter']



class SmartFitImageWriter(ImageWriter):
    def set_image(self, path, approx_level=1):
        """
            approx_level means how rude can be approximation.
            So, image will be resized with scale_ratio equal to 1/approx_level
        """
        self.approx_level = approx_level
        super().set_image(path)

    def _prepare(self):
        super()._prepare()
        if self.approx_level > 1:
            h_, w_ = self.image.shape[:2]
            self.image = cv2.resize(self.image, (w_//self.approx_level, h_//self.approx_level))
            self._image_resized(ratio_kept=True)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        maxv, minv = self.image.max(), self.image.min()
        self.image = (255 * ((maxv - self.image) / (maxv - minv))).astype(np.int16)

    def __get_random_shape(self):
        return LineShape(self.image.shape[1], self.image.shape[0])

    def __get_random_best_shape(self, max_iter=300, eps=0.001, min_threshold=0.01):
        best_shape, score = None, -1
        while score < min_threshold:
            best_shape = self.__get_random_shape()
            score = self.__value(best_shape)

        for i in range(max_iter):
            shape = best_shape.morph(0.9-score)
            value = self.__value(shape)
            if value > score:
                best_shape, score = shape, value
            if value > 1 - eps:
                break
        return best_shape, score

    def __value(self, shape):
        x, y, stamp = shape.get_stamp()
        res = self.image[y:y+stamp.shape[0], x:x+stamp.shape[1]] - stamp
        weight = stamp.sum()
        bad_weight = -(res[res<0].sum())
        good_weight = weight - bad_weight
        if weight < 1:
            return -1
        return good_weight / weight

    def __apply(self, shape):
        x, y, stamp = shape.get_stamp()
        self.image[y:y+stamp.shape[0], x:x+stamp.shape[1]] -= stamp
        if stamp.shape[1] < abs(shape.x1 - shape.x2):
            raise Exception("{}, {}".format(stamp.shape[0], abs(shape.y1 - shape.y2)))
        if isinstance(shape, LineShape):
            self._place_line([shape.x1, shape.y1], [shape.x2, shape.y2])

    def __show_image(self, winname='image', wait=0):
        cv2.imshow(winname, np.dstack((self.image * (self.image >= 0), 
                                       self.image * (self.image >= 0),
                                       np.abs(self.image))).astype(np.uint8))
        cv2.waitKey(wait)

    def process(self, epoch_size=2000, epoch_count=10, render_epoch=False):
        super().process()
        if render_epoch:
            cv2.namedWindow('processing') #, cv2.WINDOW_NORMAL)
        for epoch_i in range(epoch_count):
            print("Running epoch {}/{}".format(epoch_i+1, epoch_count))
            values, applied = [], 0
            for i in range(epoch_size):
                shape, value = self.__get_random_best_shape()
                values.append(value)
                if value > 0.8:
                    applied += 1
                    self.__apply(shape)
            if render_epoch:
                self.__show_image("processing", 0 if epoch_i == epoch_count - 1 else 100)
            print("Values mean: {}, Values max: {}, Applied: {}".format(np.mean(values), np.max(values), applied))
                
        if render_epoch:
            cv2.destroyAllWindows()



if __name__ == "__main__":
    import os, sys
    sys.path.append(os.path.abspath('..'))

    im = SmartFitImageWriter()
    im.set_image(os.path.join('..', 'data', 'img', 'fit-test.png'), 2)

    im.set_width(149)
    #im.set_width(15)

    im.process(render_epoch=True, epoch_count=1, epoch_size=2000)
    im.render()
    im.save('image-fitted.gcode')
