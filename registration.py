"""
Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator.
"""

import attr
from nipype.interfaces.base import (
    Directory,
    File,
    InputMultiPath,
    OutputMultiPath,
    traits,
)
from pydra import ShellCommandTask
from pydra.engine.specs import SpecInfo, ShellSpec
import pydra


class BRAINSResample:
    def __init__(self, name="BRAINSResample"):
        self.name = name
    """
    title: Resample Image (BRAINS)
    category: Registration
    description: This program collects together three common image processing tasks that all involve resampling an image volume: Resampling to a new resolution and spacing, applying a transformation (using an ITK transform IO mechanisms) and Warping (using a vector image deformation field).  Full documentation available here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSResample.
    version: 5.2.0
    documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSResample
    license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt
    contributor: This tool was developed by Vincent Magnotta, Greg Harris, and Hans Johnson.
    acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.
    """
    def get_task(self):
        input_fields = [
            (
                "inputVolume",
                attr.ib(
                    type=File,
                    metadata={"argstr": "--inputVolume ", "help_string": "Image To Warp"},
                ),
            ),
            (
                "referenceVolume",
                attr.ib(
                    type=File,
                    metadata={
                        "argstr": "--referenceVolume ",
                        "help_string": "Reference image used only to define the output space. If not specified, the warping is done in the same space as the image to warp.",
                    },
                ),
            ),
            (
                "outputVolume",
                attr.ib(
                    type=File,
                    metadata={
                        "argstr": "--outputVolume ",
                        "help_string": "Resulting deformed image",
                    },
                ),
            ),
            (
                "pixelType",
                attr.ib(
                    type=traits.Enum,
                    metadata={
                        "argstr": "--pixelType ",
                        "help_string": "Specifies the pixel type for the input/output images.  The 'binary' pixel type uses a modified algorithm whereby the image is read in as unsigned char, a signed distance map is created, signed distance map is resampled, and then a thresholded image of type unsigned char is written to disk.",
                    },
                ),
            ),
            (
                "deformationVolume",
                attr.ib(
                    type=File,
                    metadata={
                        "argstr": "--deformationVolume ",
                        "help_string": "Displacement Field to be used to warp the image (ITKv3 or earlier)",
                    },
                ),
            ),
            (
                "warpTransform",
                attr.ib(
                    type=File,
                    metadata={
                        "argstr": "--warpTransform ",
                        "help_string": "Filename for the BRAINSFit transform (ITKv3 or earlier) or composite transform file (ITKv4)",
                    },
                ),
            ),
            (
                "interpolationMode",
                attr.ib(
                    type=traits.Enum,
                    metadata={
                        "argstr": "--interpolationMode ",
                        "help_string": "Type of interpolation to be used when applying transform to moving volume.  Options are Linear, ResampleInPlace, NearestNeighbor, BSpline, or WindowedSinc",
                    },
                ),
            ),
            (
                "inverseTransform",
                attr.ib(
                    type=traits.Bool,
                    metadata={
                        "argstr": "--inverseTransform ",
                        "help_string": "True/False is to compute inverse of given transformation. Default is false",
                    },
                ),
            ),
            (
                "defaultValue",
                attr.ib(
                    type=traits.Float,
                    metadata={
                        "argstr": "--defaultValue ",
                        "help_string": "Default voxel value",
                    },
                ),
            ),
            (
                "gridSpacing",
                attr.ib(
                    type=InputMultiPath,
                    metadata={
                        "argstr": "--gridSpacing ",
                        "help_string": "Add warped grid to output image to help show the deformation that occured with specified spacing.   A spacing of 0 in a dimension indicates that grid lines should be rendered to fall exactly (i.e. do not allow displacements off that plane).  This is useful for makeing a 2D image of grid lines from the 3D space",
                        "sep": ",",
                    },
                ),
            ),
            (
                "numberOfThreads",
                attr.ib(
                    type=traits.Int,
                    metadata={
                        "argstr": "--numberOfThreads ",
                        "help_string": "Explicitly specify the maximum number of threads to use.",
                    },
                ),
            ),
        ]
        output_fields = [
            (
                "outputVolume",
                attr.ib(
                    type=pydra.specs.File,
                    metadata={
                        "help_string": "Resulting deformed image",
                        "output_file_template": "{outputVolume}",
                    },
                ),
            ),
        ]
    
        input_spec = SpecInfo(name="Input", fields=input_fields, bases=(ShellSpec,))
        output_spec = SpecInfo(
            name="Output", fields=output_fields, bases=(pydra.specs.ShellOutSpec,)
        )
    
        task = ShellCommandTask(
            name=self.name,
            executable="BRAINSResample",
            input_spec=input_spec,
            output_spec=output_spec,
        )
        return task
