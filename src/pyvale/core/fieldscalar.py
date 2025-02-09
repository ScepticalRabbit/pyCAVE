"""
================================================================================
pyvale: the python validation engine
License: MIT
Copyright (C) 2024 The Computer Aided Validation Team
================================================================================
"""
import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation
import mooseherder as mh

from pyvale.core.field import IField
from pyvale.core.fieldconverter import conv_simdata_to_pyvista
from pyvale.core.fieldsampler import sample_pyvista_grid

class FieldScalar(IField):
    """Class for sampling (interpolating) scalar fields from simulations to
    provide sensor values at specified locations and times.

    Implements the `IField` interface.
    """
    __slots__ = ("_field_key","_spat_dims","_sim_data","_pyvista_grid",
                 "_pyvista_vis")

    def __init__(self,
                 sim_data: mh.SimData,
                 field_key: str,
                 spat_dims: int) -> None:
        """Initialiser for the `FieldScalar` class.

        Parameters
        ----------
        sim_data : mh.SimData
            Simulation data object containing the mesh and field to interpolate.
        field_key : str
            String key for the scalar field component in the `SimData` object.
        spat_dims : int
            Number of spatial dimensions (2 or 3) used for identifying element
            types.
        """

        self._field_key = field_key
        self._spat_dims = spat_dims

        self._sim_data = sim_data
        (self._pyvista_grid,self._pyvista_vis) = conv_simdata_to_pyvista(
            self._sim_data,
            (self._field_key,),
            self._spat_dims
        )

    def set_sim_data(self, sim_data: mh.SimData) -> None:
        """Sets the `SimData` object that will be interpolated to obtain sensor
        values. The purpose of this is to be able to apply the same sensor array
        to an array of different simulations by setting a different `SimData`.

        Parameters
        ----------
        sim_data : mh.SimData
            Mooseherder SimData object. Contains a mesh and a simulated
            physical field.
        """
        self._sim_data = sim_data
        (self._pyvista_grid,self._pyvista_vis) = conv_simdata_to_pyvista(
            sim_data,
            (self._field_key,),
            self._spat_dims
        )

    def get_sim_data(self) -> mh.SimData:
        """Gets the simulation data object associated with this field. Used by
        pyvale visualisation tools to display simulation data with simulated
        sensor values.

        Returns
        -------
        mh.SimData
            Mooseherder SimData object. Contains a mesh and a simulated
            physical field.
        """
        return self._sim_data

    def get_time_steps(self) -> np.ndarray:
        """Gets a 1D array of time steps from the simulation data.

        Returns
        -------
        np.ndarray
            1D array of simulation time steps. shape=(num_time_steps,)
        """
        return self._sim_data.time

    def get_visualiser(self) -> pv.UnstructuredGrid:
        """Gets a pyvista unstructured grid object for visualisation purposes.

        Returns
        -------
        pv.UnstructuredGrid
            Pyvista unstructured grid object containing only a mesh without any
            physical field data attached.
        """
        return self._pyvista_vis

    def get_all_components(self) -> tuple[str, ...]:
        """Gets the string key for the component of the physical field. A scalar
        field only has a single component so a tuple of length 1 is returned.

        Returns
        -------
        tuple[str,...]
            Tuple containing the string key for the physical field.
        """
        return (self._field_key,)

    def get_component_index(self, comp: str) -> int:
        """Gets the index for a component of the physical field. Used for
        getting the index of a component in the sensor measurement array.

        Parameters
        ----------
        component : str
            String key for the field component (e.g. 'temperature' or 'disp_x').

        Returns
        -------
        int
            Index for the selected field component
        """
        return 0 # scalar fields only have one component!

    def sample_field(self,
                    points: np.ndarray,
                    times: np.ndarray | None = None,
                    angles: tuple[Rotation,...] | None = None,
                    ) -> np.ndarray:
        """Samples (interpolates) the simulation field at the specified
        positions, times, and angles.

        Parameters
        ----------
        points : np.ndarray
            Spatial points to be sampled with the rows indicating the point
            number of the columns indicating the X,Y and Z coordinates.
        times : np.ndarray | None, optional
            Times to sample the underlying simulation. If None then the
            simulation time steps are used and no temporal interpolation is
            performed, by default None.
        angles : tuple[Rotation,...] | None, optional
            Angles to rotate the sampled values into with rotations specified
            with respect to the simulation world coordinates. If a single
            rotation is specified then all points are assumed to have the same
            angle and are batch processed for speed. If None then no rotation is
            performed, by default None.

        Returns
        -------
        np.ndarray
            An array of sampled (interpolated) values with the following
            dimensions: shape=(num_points,num_components,num_time_steps).
        """
        return sample_pyvista_grid((self._field_key,),
                                self._pyvista_grid,
                                self._sim_data.time,
                                points,
                                times)

