"""Developing stereo camera system
"""
from dataclasses import dataclass
import numpy as np
import math
import mathutils
from dev_blendercamera import CameraData, CameraBlender
# Notes
    # Can iterate through cameras and make active?
    # Just need to set camera as current camera - bpy.context.scene.camera = cam

@dataclass
class StereoData:
    cam_data_0: CameraData = CameraData
    cam_data_1: CameraData = CameraData
    base: float | None = 5
    angle_deg: float | None = 15
    calib_file: bool | None = False
    calib_filepath: str | None = None

class Stereo:
    def __init__(self, stereo_data: StereoData):
        self.stereo_data = stereo_data


    def add_stereo_system(self, scene):
        self.stereo_data.cam_data_0.name = 'cam_0'
        cam_0 = scene.add_camera(self.stereo_data.cam_data_0)

        cam_1_pos = list(self.stereo_data.cam_data_0.position)
        cam_1_pos[0] = cam_1_pos[0] + self.stereo_data.base
        self.stereo_data.cam_data_1.position = cam_1_pos

        self.stereo_data.cam_data_1.name = 'cam_1'
        cam_1 = scene.add_camera(self.stereo_data.cam_data_1)
        cam_1.rotation_mode = 'XYZ'
        cam_1.rotation_euler = (0, np.radians(self.stereo_data.angle_deg), 0)

        if self.stereo_data.calib_file:
            calib_filepath = self.stereo_data.calib_filepath
            self.stereo_calibration(cam_0, cam_1, calib_filepath)


    def stereo_calibration(self, cam0, cam1, calib_filepath):
        # Get rotation of cam0 to cam1
        cam0_orient = cam0.rotation_quaternion
        cam1_orient = cam1.rotation_quaternion
        q_x = [math.cos(np.pi / 2), math.sin(np.pi / 2), 0, 0]
        cam0_orient = self._rotate_quaternion(q_x, cam0_orient)
        cam1_orient = self._rotate_quaternion(q_x, cam1_orient)

        q_rot = self._quaternion_multiply(cam0_orient, self._quaternion_conjugate(cam1_orient))
        q_rot_conj = self._quaternion_conjugate(q_rot)
        q_rot = mathutils.Quaternion(q_rot)
        ang = q_rot.to_euler('XYZ')
        ang = [np.rad2deg(i) for i in ang]

        # Translation of cam0 to cam1 + rotate vector to orientation of cam1
        dist = cam0.location - cam1.location
        dist[2] *= -1
        dist[1] *= -1

        dist_rot =

        with open(calib_filepath, "w") as file:
            file.write("Cam1_Fx [pixels];" + f'{cam0.data.lens/cam0["px_size"][0]}\n')
            file.write("Cam1_Fy [pixels];" + f'{cam0.data.lens/cam0["px_size"][1]}\n')
            file.write("Cam1_Fs [pixels];0\n")
            file.write(f'Cam1_Kappa 1;{cam0["k1"]}\n')
            file.write(f'Cam1_Kappa 2;{cam0["k2"]}\n')
            file.write(f'Cam1_Kappa 3;{cam0["k3"]}\n')
            file.write(f'Cam1_P1;{cam0["p1"]}\n')
            file.write(f'Cam1_P2;{cam0["p2"]}\n')
            file.write(f'Cam1_Cx [pixels];{cam0["c0"]}\n')
            file.write(f'Cam1_Cy [pixels];{cam0["c1"]}\n')
            file.write("Cam2_Fx [pixels];" + f'{cam1.data.lens/cam1["px_size"][0]}\n')
            file.write("Cam2_Fy [pixels];" + f'{cam1.data.lens/cam1["px_size"][1]}\n')
            file.write("Cam2_Fs [pixels];0\n")
            file.write(f'Cam2_Kappa 1;{cam1["k1"]}\n')
            file.write(f'Cam2_Kappa 2;{cam1["k2"]}\n')
            file.write(f'Cam2_Kappa 3;{cam1["k3"]}\n')
            file.write(f'Cam2_P1;{cam1["p1"]}\n')
            file.write(f'Cam2_P2;{cam1["p2"]}\n')
            file.write(f'Cam2_Cx [pixels];{cam1["c0"]}\n')
            file.write(f'Cam2_Cy [pixels];{cam1["c1"]}\n')
            file.write(f"Tx [mm];{dist[0]}\n")
            file.write(f"Ty [mm];{dist[1]}\n")
            file.write(f"Tz [mm];{dist[2]}\n")
            file.write(f"Theta [deg];{ang[0]}\n")
            file.write(f"Phi [deg];{ang[1]}\n")
            file.write(f"Psi [deg];{ang[2]}")

    def _rotate_quaternion(self, q0 ,q1):
        # q2 = q1.q0.conj(q0)

        q0_conj = self._quaternion_conjugate(q0)
        q2 = self.quaternion_multiply(self._quaternion_multiply(q0, q1), q0_conj)
        return q2

    def _quaternion_conjugate(self, q0):
        if type(q0) is list or type(q0) is mathutils.Quaternion:
            q0_conj = [-j if i > 0 else j for i, j in enumerate(q0)]
        elif type(q0) is np.ndarray:
            q0_conj = np.array([-j if i > 0 else j for i, j in enumerate(q0)])
        return q0_conj

    def _quaternion_multiply(self, q0, q1):
        w0, x0, y0, z0 = q0
        w1, x1, y1, z1 = q1
        return np.array(
            [
                -x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0,
            ],
            dtype=np.float64,
        )

    def _rotate_vec(self, v, q):
        # v = q.v.conj(q)
        v = self.vec_to_quaternion(v)






