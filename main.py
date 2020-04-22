import presets as p
from lib import GCodeWriter
import os


if __name__ == "__main__":
    p.gcode.init_laser(left_bottom_corner=[15, 65], default_z=67.2, default_speed=700, default_power=100)
    #p.height_test(40, 90)
    #p.grid_test(4, 4)
    #p.test_on_material(0, 20, 0, 6.8, 100)
    p.full_desk_image_3_step(os.path.join('data', 'img', '3-step-image.png'))  # WARNING REINIT OF DEFAULT SETTINGS!!!!!!!