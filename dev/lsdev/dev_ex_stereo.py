"""Example to create a scene in Blender and save it as a Blender file
"""

import os
from pathlib import Path
import numpy as np
import mooseherder as mh
import bpy
from dev_blenderscene import BlenderScene
from dev_partblender import *
from dev_blendercamera import CameraData
from dev_lightingblender import LightData, LightType
from dev_objectmaterial import MaterialData
from dev_stereo import StereoData
from dev_render import RenderData, Render

def main() -> None:
    data_path = Path('src/pyvale/simcases/case18_out.e')
    data_reader = mh.ExodusReader(data_path)
    sim_data = data_reader.read_all_sim_data()

    dir = Path.cwd() / 'dev/lsdev/blender_files'
    filename = 'case18_stereo.blend'
    filepath = dir / filename
    all_files = os.listdir(dir)
    for ff in all_files:
        if filename == ff:
            os.remove(dir / ff)

    filepath = str(filepath)

    scene = BlenderScene()

    part_location = (0, 0, 0)
    angle = np.radians(90)
    part_rotation = (0, 0, 0)

    part, pv_surf, spat_dim, components = scene.add_part(sim_data=sim_data)
    scene.set_part_location(part=part, location=part_location)
    scene.set_part_rotation(part=part, rotation=part_rotation)

    sensor_px = (2464, 2056)
    cam_position = (0, 0, 250)
    focal_length = 15.0
    cam_data_0 = CameraData(sensor_px=sensor_px,
                          position=cam_position,
                          focal_length=focal_length,
                          part_dimension=part.dimensions)
    cam_data_1 = cam_data_0
    calib_filepath = Path.cwd() / 'dev/lsdev/rendered_images/stereo_test/calib.txt'
    stereo_data = StereoData(cam_data_0=cam_data_0,
                             cam_data_1=cam_data_1,
                             base = 35.0,
                             angle_deg=10.0,
                             calib_file=True,
                             calib_filepath=calib_filepath)
    scene.add_stereo_system(stereo_data, scene)

    type = LightType.POINT
    light_position = (0, 0, 200)
    energy = 200 * (10)**3
    light_data = LightData(type=type,
                           position=light_position,
                           energy=energy,
                           part_dimension=part.dimensions)

    light = scene.add_light(light_data)

    mat_data = MaterialData()
    image_path = '/home/lorna/pyvale/src/pyvale/data/optspeckle_2464x2056px_spec5px_8bit_gblur1px.tiff'
    mat = scene.add_material(mat_data, part, image_path, cam_data_0)


    #---------------------------------------------------------------------------
    # Rendering images
    image_path = Path.cwd() / 'dev/lsdev/rendered_images/stereo_test'
    output_path = Path.cwd() / 'dev/lsdev/rendered_images/stereo_test/output.txt'


    render_data = RenderData(samples=1)

    cam_count = 0
    cam_data = [cam_data_0, cam_data_1]
    render_counter = 0
    render_name = 'test_stereo'
    for cam in [obj for obj in bpy.data.objects if obj.type == 'CAMERA']:
        bpy.context.scene.camera = cam
        cam_data_render = cam_data[cam_count]
        render = Render(render_data, image_path=image_path, output_path=output_path, cam_data=cam_data_render)

        # render.render_image(render_name, render_counter, part, cam_count)
        cam_count += 1


    scene.save_model(filepath)

if __name__ == "__main__":
    main()