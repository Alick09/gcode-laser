import re
import os


class GCodeWriter(object):
    LASER_ON = 106
    LASER_OFF = 107

    def __init__(self):
        self.code = ''
        self.type = 'printer'

    def init_laser(self, move_speed=3000, pause_before_start_seconds=0.3, default_z=60, auto_home=True, 
                   left_bottom_corner=[55, 40], default_speed=100, default_power=100, corner_margin=5):
        """
            left-bottom-corner - X and Y value for printer axis where laser looks at left-bottom corner (the smallest X and Y)
        """
        self.move_speed = 3000
        self.pause_before_start_seconds = pause_before_start_seconds
        self.code = 'M{} S0\n\nG90\nG21{}\nG1  Z{:.4f}\n'.format(self.LASER_OFF, '\nG28' if auto_home else '', default_z)
        self.default_z = default_z
        self.left_bottom_corner = [v + corner_margin for v in left_bottom_corner]
        self.default_speed = default_speed
        self.default_power = default_power

    def __convert_pos(self, x, y):
        x += self.left_bottom_corner[0]
        y += self.left_bottom_corner[1]
        return x, y

    def __move(self, x, y, z=None, absolute=False):
        if not absolute:
            x, y = self.__convert_pos(x, y)
        if z is None:
            self.code += '\nG1  X{:.4f} Y{:.4f}'.format(x, y)
        else:
            self.code += '\nG1  X{:.4f} Y{:.4f} Z{:.4f}'.format(x, y, z)

    def __move_g2(self, x, y, r, absolute=False):
        if not absolute:
            x, y = self.__convert_pos(x, y)
        self.code += '\nG2  X{:.4f} Y{:.4f} R{:.4f}'.format(x, y, r)

    def __prepare(self, start_point, z_value=None, power=None, speed=None):
        if speed is None:
            speed = self.default_speed
        if power is None:
            power = self.default_power
        self.code += '\nG1 F{}'.format(self.move_speed)
        self.__move(*start_point)
        if z_value is not None:
            self.code += '\nG1  Z{:.4f}'.format(z_value)
        self.code += '\nG4 P0'
        self.code += '\nM{} S{}'.format(self.LASER_ON, power)
        self.code += '\nG4 P{:.4f}'.format(self.pause_before_start_seconds)
        self.code += '\nG1 F{:.4f}'.format(speed)

    def __element_finished(self):
        self.code += '\nG4 P0\nM{} S0'.format(self.LASER_OFF)

    def draw_path(self, points, **kwargs):
        self.__prepare(points[-1], **kwargs)
        for p in points:
            self.__move(*p)
        self.__element_finished()

    def draw_rectangle(self, x, y, w, h, **kwargs):
        points = [[x+w, y], [x+w, y+h], [x, y+h], [x, y]]
        self.draw_path(points, **kwargs)

    def draw_circle(self, x, y, r, **kwargs):
        self.__prepare([x-r, y], **kwargs)
        self.__move_g2(x, y+r, r)
        self.__move_g2(x+r, y, r)
        self.__move_g2(x, y-r, r)
        self.__move_g2(x-r, y, r)
        self.__element_finished()

    def draw_line(self, x1, y1, x2, y2, z1=None, z2=None, **kwargs):
        if z1 is None:
            if 'z_value' in kwargs:
                z1 = kwargs.pop('z_value')
        if z2 is None:
            z2 = z1
        a, b = (x1, y1) if z1 is None else (x1, y1, z1), (x2, y2) if z2 is None else (x2, y2, z2)
        self.__prepare(a, **kwargs)
        self.__move(*b)
        self.__element_finished()

    def __parse_move_line(self, line):
        """G02 X88.704067 Y251.364508 Z-0.125000 I0.032899 J0.064154"""
        parts = re.sub('\(.*?\)', '', line).split()
        x, y = None, None
        for part in parts[:0:-1]:
            axis = part.upper()[0]
            value = float(part[1:])
            if axis in ['Z', 'F']:
                parts.remove(part)
            elif axis == 'X':
                x = value
                parts.remove(part)
            elif axis == 'Y':
                y = value
                parts.remove(part)
        if x is None or y is None:
            return None
        template = parts[0] + ' X{:.6f} Y{:.6f} ' + ' '.join(parts[1:])
        return [template, x, y]


    def load_from_inkscape_gcode(self, filename, w, cx, cy, **kwargs):
        """
            Loads path created in inkscape using (Extensions > Gcode tools > Path to GCode)
        """
        lines = [x.strip() for x in open(filename).read().split('\n')]
        xs, ys = [], []
        shapes = dict()
        current_path = None
        for line in lines:
            path_start = re.search('Start cutting path id: ([^\s\)]+)', line)
            path_end = re.search('End cutting path id: ', line)
            if path_start is not None:
                current_path = path_start.group(1)
                shapes[current_path] = []
            elif path_end is not None:
                current_path = None
            elif line.startswith('('):
                continue
            elif line.upper().startswith('G'):
                if current_path is not None:
                    x = self.__parse_move_line(line)
                    if x is not None:
                        shapes[current_path].append(x)
                        xs.append(x[1])
                        ys.append(x[2])
        min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
        
        scale = w/(max_x - min_x)
        dx, dy = (max_x + min_x)/2, (max_y + min_y)/2
        cx += self.left_bottom_corner[0]
        cy += self.left_bottom_corner[1]
        print(scale, dx, dy, cx, cy, min_x, max_x)

        for item in sorted(shapes.values(), key= lambda x: x[0][1]):
            self.code += '\n'
            for i, (template, x, y) in enumerate(item):
                x = (x - dx)*scale + cx
                y = (y - dy)*scale + cy
                if i == 0:
                    self.__prepare([x - self.left_bottom_corner[0], y - self.left_bottom_corner[1]], **kwargs)
                else:
                    self.code += '\n' + template.format(x, y)
            self.__element_finished()

    def __finalize(self):
        self.code += '\nG1 F{}'.format(self.move_speed)
        self.__move(0, 0, absolute=True)
        lines = self.code.split('\n')
        lines = [x.lstrip() for x in lines]
        while lines[0].strip() == '':
            lines.pop(0)
        while lines[-1].strip() == '':
            lines.pop()
        self.code = '\n'.join(lines)

    def save(self, filename):
        self.__finalize()
        with open(os.path.join('data', filename), 'w') as f:
            f.write(self.code)
            print("File {} saved successfully.".format(filename))


if __name__ == "__main__":
    gcode = GCodeWriter()
    gcode.init_laser(left_bottom_corner=[55, 40], default_z=71.2, default_speed=700, default_power=100)
    # gcode.load_from_inkscape_gcode('alenka_0001.gcode', 15, 10, 10, speed=900)
    # gcode.draw_circle(10, 10, 10, speed=300)
    gcode.draw_line(0, 0, 20, 0)
    gcode.draw_line(20, 0, 20, 20)
    gcode.draw_line(20, 20, 0, 20)
    gcode.draw_line(0, 20, 0, 0)
    gcode.draw_line(0, 10, 20, 10)
    gcode.draw_line(10, 0, 10, 20)
    gcode.save('test-grid-2.gcode')