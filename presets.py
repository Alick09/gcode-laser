from lib import GCodeWriter
from image_processing.scan import ScanImageWriter

gcode = GCodeWriter()
gcode.init_laser(left_bottom_corner=[55, 40], default_z=71.2, default_speed=700, default_power=100)

def height_test(minv, maxv):
    gcode.draw_line(0, 5, 80, 5, minv, maxv)
    gcode.draw_line(0, 0, 0, 10, speed=100, z_value=0.5*(minv+maxv))
    gcode.draw_line(80, 0, 80, 10, speed=100, z_value=0.5*(minv+maxv))
    gcode.save('test-z-quick.gcode')

def dot_test(x, y):
    gcode.draw_line(x, y-5, x, y+5)
    gcode.draw_line(x-5, y, x+5, y)
    gcode.save('test-dot.gcode')

def grid_test(rows=2, columns=2, size=5):
    for i in range(rows+1):
        gcode.draw_line(0, i * size, columns * size, i * size)
    for j in range(columns+1):
        gcode.draw_line(j * size, 0, j * size, rows * size)
    gcode.save('test-grid.gcode')

def test_on_material(x1, x2, y, z, speed):
    gcode.draw_line(x1, y, x2, y, z + gcode.default_z, speed=speed)
    gcode.save('test-on-material.gcode')


def full_desk_image_3_step(path):
    gcode = GCodeWriter()
    gcode.init_laser(left_bottom_corner=[15-9.3, 65-4], default_z=67.2, default_speed=500, default_power=100)
    im = ScanImageWriter(gcode)
    im.set_image(path, 3)
    im.set_width(149)
    im.process(distance_mm=1)
    im.render()
    im.save('image-sto.gcode')