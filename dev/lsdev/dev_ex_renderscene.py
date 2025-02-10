"""Example that creates a scene and renders a single image
"""

import os
from pathlib import Path
import mooseherder as mh
import numpy as np
from dev_blenderscene import BlenderScene
from dev_partblender import *
from dev_objectmaterial import MaterialData
from dev_blendercamera import CameraData
from dev_lightingblender import LightData, LightType
from dev_render import RenderData, Render

def main() -> None:
    # Making Blender scene
    data_path = Path('src/pyvale/data/case18_1_out.e')
    data_reader = mh.ExodusReader(data_path)
    sim_data = data_reader.read_all_sim_data()

    dir = Path.cwd() / 'dev/lsdev/blender_files'
    filename = 'case18.blend'
    filepath = dir / filename
    all_files = os.listdir(dir)
    for ff in all_files:
        if filename == ff:
            os.remove(dir / ff)

    filepath = str(filepath)

    scene = BlenderScene()

    part_location = (0, 0, 0)
    part_rotation = (0, 0, np.radians(0))
    part, pv_surf, spat_dim, components = scene.add_part(sim_data=sim_data)
    print(f"{part.dimensions=}")
    scene.set_part_location(part, part_location)
    scene.set_part_rotation(part, part_rotation)

    sensor_px = (2464, 2056)
    cam_position = (0, 0, 250)
    focal_length = 15.0
    cam_data = CameraData(sensor_px=sensor_px,
                          position=cam_position,
                          focal_length=focal_length,
                          part_dimension=part.dimensions)

    camera= scene.add_camera(cam_data)

    type = LightType.POINT
    light_position = (0, 0, 200)
    energy = 400 * (10)**3
    light_data = LightData(type=type,
                           position=light_position,
                           energy=energy,
                           part_dimension=part.dimensions)

    light = scene.add_light(light_data)

    mat_data = MaterialData()
    image_path = '/home/lorna/pyvale/src/pyvale/data/optspeckle_2464x2056px_spec5px_8bit_gblur1px.tiff'
    mat = scene.add_material(mat_data, part, image_path, cam_data)

    #---------------------------------------------------------------------------
    # Rendering images
    image_path = Path.cwd() / 'dev/lsdev/rendered_images'
    output_path = Path.cwd() / 'dev/lsdev/rendered_images//output.txt'


    render_data = RenderData(samples=1)
    render = Render(render_data, image_path=image_path, output_path=output_path, cam_data=cam_data)

    render_counter = 0
    render_name = 'test_bw'

    for i in range(render_data.samples):
        render.render_image(render_name, render_counter, part)
        render_counter += 1

    scene.save_model(filepath)

if __name__ == "__main__":
    main()