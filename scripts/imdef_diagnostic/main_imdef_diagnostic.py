"""
================================================================================
pyvale: the python computer aided validation engine

License: MIT
Copyright (C) 2024 The Computer Aided Validation Team
================================================================================
"""
import time
import pickle
from pprint import pprint
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import mooseherder as mh

from pyvale.imagesim.imagedefopts import ImageDefOpts
from pyvale.imagesim.cameradataimagedef import CameraImageDef
import pyvale.imagesim.imagedef as sid
import pyvale.imagesim.imagedefdiags as idd

def main() -> None:
    print()
    print('='*80)
    print('PYVALE EXAMPLE: IMAGE DEFORMATION 2D DIAGNOSTIC')
    print('='*80)

    #---------------------------------------------------------------------------
    # Load image - expects a *.tiff or *.bmp that is grayscale
    im_path = Path('data/speckleimages')
    #im_file = 'OptimisedSpeckle_500_500_width3.0_16bit_GBlur1.tiff'
    im_file = 'OptimisedSpeckle_2464_2056_width5.0_8bit_GBlur1.tiff'
    im_path = im_path / im_file
    print('\nLoading speckle image from path:')
    print(im_path)

    input_im = sid.load_image(im_path)

    #---------------------------------------------------------------------------
    # Load simulation data - expects a mooseherder.SimData object
    # Read a pickled one or get one from an exodus
    read_exodus = True

    sim_path = Path.cwd()
    if read_exodus:
        case_str = 'case14'
        sim_path = Path(f'simcases/{case_str}')
        sim_file = f'{case_str}_out.e'

        print(f'\nLoading SimData from exodus in path:\n{sim_path}')

        exodus_reader = mh.ExodusReader(sim_path / sim_file)
        sim_data = exodus_reader.read_all_sim_data()

    else:
        sim_path = Path('scripts/imdef_cases/imdefcase8_RampRigidBodyMotion_5_0px')
        sim_file = 'sim_data.pkl'

        print(f'\nLoading pickled SimData from path:\n{sim_path}')

        with open(sim_path / sim_file,'rb') as sim_load_file:
            sim_data = pickle.load(sim_load_file)

    if sim_data.coords is not None:
        coords = sim_data.coords
    if sim_data.node_vars is not None:
        disp_x = sim_data.node_vars['disp_x']
        disp_y = sim_data.node_vars['disp_y']
    del sim_data

    DIAG_FRAME = disp_x.shape[1]

    #---------------------------------------------------------------------------
    # INIT IMAGE DEF OPTIONS AND CAMERA
    print('')
    print('='*80)
    print('INIT. IMAGE DEF. OPTIONS AND CAMERA')
    print('')

    #---------------------------------------------------------------------------
    # CREATE IMAGE DEF OPTS
    id_opts = ImageDefOpts()
    id_opts.save_path = sim_path / 'deformed_images'

    # If the input image is just a pattern then the image needs to be masked to
    # show just the sample geometry. This setting generates this image.
    id_opts.mask_input_image = True
    # Set this to True for holes and notches and False for a rectangle
    id_opts.def_complex_geom = False

    # If the input image is much larger than needed it can also be cropped to
    # increase computational speed.
    id_opts.crop_on = True
    id_opts.crop_px = np.array([500,500])

    # Calculates the m/px value based on fitting the specimen/ROI within the camera
    # FOV and leaving a set number of pixels as a border on the longest edge
    id_opts.calc_res_from_fe = True
    id_opts.calc_res_border_px = 10

    # Set this to true to create an undeformed masked image
    if read_exodus:
        id_opts.add_static_ref = 'off'
    else:
        id_opts.add_static_ref = 'pad_disp'

    print('-'*80)
    print('ImageDefOpts:')
    pprint(vars(id_opts))
    print('-'*80)
    print('')

    #---------------------------------------------------------------------------
    # CREATE CAMERA OBJECT
    camera = CameraImageDef()
    # Need to set the number of pixels in [X,Y], the bit depth and the m/px

    # Assume the camera has the same number of pixels as the input image unless we
    # are going to crop/mask the input image
    camera.num_px = np.array([input_im.shape[1],input_im.shape[0]])
    if id_opts.crop_on:
        camera.num_px = id_opts.crop_px

    # Based on the max grey level work out what the bit depth of the image is
    camera.bits = 8
    if max(input_im.flatten()) > (2**8):
        camera.bits = 16

    # Assume 1mm/px to start with, can update this to fit FE data within the FOV
    # using the id_opts above. Or set this manually.
    camera.m_per_px = 1.0e-3 # Overwritten by id_opts.calc_res_from_fe = True

    # Can manually set the ROI location by setting the above to false and setting
    # the camera.roi_loc as the distance from the origin to the bottom left
    # corner of the sample [X,Y]: camera.roi_loc = np.array([1e-3,1e-3])

    # Default ROI is the whole FOV but we want to set this to be based on the
    # furthest nodes, this is set in FE units 'meters' and does not change FOV
    camera.roi_len = sid.calc_roi_from_nodes(camera,coords)

    # If we are masking an image we might want to set an optimal resolution based
    # on leaving a specified number of pixels free on each image edge, this will
    # change the FOV in 'meters'
    if id_opts.calc_res_from_fe:
        camera.m_per_px = sid.calc_res_from_nodes(camera,coords, #type: ignore
                                                id_opts.calc_res_border_px)

    # Default ROI is the whole FOV but we want to set this to be based on the
    # furthest nodes, this is set in FE units 'meters' and does not change FOV
    camera.roi_len = sid.calc_roi_from_nodes(camera,coords)

    print('-'*80)
    print('CameraData:')
    pprint(vars(camera))
    print('-'*80)
    print('')

    #---------------------------------------------------------------------------
    # PRE-PROCESSING
    print('')
    print('='*80)
    print('IMAGE AND DATA PRE-PROCESSING')
    print('')

    idd.plot_diag_image('Raw input image',input_im,idd.I_CMAP)

    # Run all processes that only need to be called once before deforming the
    # images - includes image masking, cropping and upsampling
    # Returns
    (upsampled_image,
     image_mask,
     input_im,
     disp_x,
     disp_y) = sid.preprocess(input_im,
                                coords,
                                disp_x,
                                disp_y,
                                camera,
                                id_opts,
                                print_on = True)

    idd.plot_diag_image('Pre-processed image', input_im, idd.I_CMAP)
    idd.plot_diag_image('Upsampled Image',upsampled_image,idd.I_CMAP)
    if image_mask is not None:
        idd.plot_diag_image('Undef. Image Mask',image_mask,idd.I_CMAP)

    #---------------------------------------------------------------------------
    # DEFORM IMAGES
    print('')
    print('='*80)
    print('DEFORMING IMAGES')

    num_frames = disp_x.shape[1]
    ticl = time.perf_counter()

    for ff in range(num_frames):
        ticf = time.perf_counter()
        print('')
        print(f'DEFORMING FRAME: {ff}')

        (def_image,
        def_image_subpx,
        subpx_disp_x,
        subpx_disp_y,
        def_mask) = sid.deform_one_image(upsampled_image,
                                    camera,
                                    id_opts,
                                    coords,
                                    np.array((disp_x[:,ff],disp_y[:,ff])).T,
                                    image_mask=image_mask,
                                    print_on=True)

        if ff == (DIAG_FRAME-1):
            (subpx_grid_xm,subpx_grid_ym) = sid.get_subpixel_grid(camera,
                                                                  id_opts.subsample)
            idd.plot_all_diags(def_image,
                                def_mask,
                                def_image_subpx,
                                subpx_disp_x,
                                subpx_disp_y,
                                subpx_grid_xm,
                                subpx_grid_ym)

        save_file = id_opts.save_path / str(f'{id_opts.save_tag}_'+
                f'{sid.get_image_num_str(im_num=ff,width=4)}'+
                '.tiff')
        sid.save_image(save_file,def_image,camera.bits)


        tocf = time.perf_counter()
        print(f'DEFORMING FRAME: {ff} took {tocf-ticf:.4f} seconds')

    tocl = time.perf_counter()
    print('')
    print('-'*50)
    print(f'Deforming all images took {tocl-ticl:.4f} seconds')
    print('-'*50)

    # COMPLETE
    plt.show()
    print('')
    print('='*80)
    print('COMPLETE\n')

if __name__ == '__main__':
    main()