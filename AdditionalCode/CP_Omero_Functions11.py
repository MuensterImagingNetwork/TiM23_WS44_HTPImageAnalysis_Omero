#Imports

#Cellprofiler
import cellprofiler_core.pipeline
import cellprofiler_core.preferences
import cellprofiler_core.utilities.java
import cellprofiler_core.image
import cellprofiler_core.measurement
import cellprofiler_core.object
import cellprofiler_core.workspace
import ezomero

import omero

#Other
import os
import numpy as np
import cv2
from omero.model import OriginalFileI, PlateI, ScreenPlateLinkI, ScreenI
from omero.rtypes import rint, rlong, rstring, robject, unwrap






def load_pipeline(pipe_dir):
    pipeline = cellprofiler_core.pipeline.Pipeline()
    pipeline.load(pipe_dir)

    return pipeline

def get_saving_mods(pipeline):
    saving_modules = []
    for i in range(len(pipeline.modules())):
        if pipeline.modules()[i].module_name == "SaveImages":
            saving_modules.append(i)

    return saving_modules




def adjust_pipeline(pipeline, overwrite_results, output_file_format):
    # Remove first 4 modules: Images, Metadata, NamesAndTypes, Groups...
    # (replaced by InjectImage module below)
    for i in range(4):
        print('Remove module: ', pipeline.modules()[0].module_name)
        pipeline.remove_module(1)

    # Adjust export modules:
    export_modules = []
    for i in range(len(pipeline.modules())):
        if pipeline.modules()[i].module_name == "ExportToSpreadsheet":
            export_modules.append(i)
    # Change export modules:
    for mod in export_modules:
        for set in range(len(pipeline.modules()[mod].settings())):
            # print(pipeline.modules()[mod].setting(set).text)
            if pipeline.modules()[mod].setting(set).text == "Overwrite existing files without warning?":
                pipeline.modules()[mod].setting(set).set_value(overwrite_results)
            if pipeline.modules()[mod].setting(set).text == "Output file location":
                pipeline.modules()[mod].setting(set).set_value("Default Output Folder|")
            #if pipeline.modules()[mod].setting(set).text == "Press button to select measurements:":
                #selected_measurements = pipeline.modules()[mod].setting(set).get_value()

        #   Possibly add "Add a prefix to file names?"

    # Find all saving modules:
    saving_modules = []
    for i in range(len(pipeline.modules())):
        if pipeline.modules()[i].module_name == "SaveImages":
            saving_modules.append(i)
    # Overwriting files
    for mod in saving_modules:
        for set in range(len(pipeline.modules()[mod].settings())):
            #print(pipeline.modules()[mod].setting(set).text)
            if pipeline.modules()[mod].setting(set).text == "Overwrite existing files without warning?":
                pipeline.modules()[mod].setting(set).set_value(overwrite_results)
    # Saving format
    for mod in saving_modules:
        for set in range(len(pipeline.modules()[mod].settings())):
            #print(pipeline.modules()[mod].setting(set).text)
            if pipeline.modules()[mod].setting(set).text == "Saved file format":
                pipeline.modules()[mod].setting(set).set_value(output_file_format)
            #if pipeline.modules()[mod].setting(set).text == "Output file location":
                #pipeline.modules()[mod].setting(set).set_value("Default Output Folder")

    print('Pipeline modules:')
    for module in pipeline.modules():
        print(module.module_num, module.module_name)

    return pipeline

def retrieve_selected_export_measurements(pipeline):

    for mod in range(len(pipeline.modules())):
        if pipeline.modules()[mod].module_name == "ExportToSpreadsheet":
            for set in range(len(pipeline.modules()[mod].settings())):
                selected_measurements = pipeline.modules()[i].setting(14).get_value()   #Make generic

    return selected_measurements


def load_images_from_disk(saving_path):

    return list(saving_path.glob('*.png'))


def load_result_image_from_disk(img):
    """ Loads the image from disk using cv2, prepares the image axes and axis order to zctyx order that is expected by omero.
    Returns parent_id, and the image."""

    # TO DO: include loading multiple images with different tags

    _, tail = os.path.split(img)
    parent_id = os.path.splitext(tail)[0].split("_")[0]
    print("Parent image id:", parent_id)
    image = cv2.imread(img.__str__(), -1)  # TO DO: Adjust to different file formats

    # TO DO: include check how many axes are there

    image = np.expand_dims(image, axis=-1)  # adds axes to 2D images
    image = np.expand_dims(image, axis=-1)
    image= image.swapaxes(0, 3).swapaxes(1, 4).swapaxes(0, 1).swapaxes(1, 2) # Re-organise array from xyczt to zctyx order expected by OMERO

    return parent_id, image


def load_multiple_result_images(image_paths):
    result_images = []
    for img in image_paths:
        _, tail = os.path.split(img)
        parent_id = os.path.splitext(tail)[0].split("_")[0]
        print("Parent image id:", parent_id)
        image = cv2.imread(img.__str__(), -1)  # TO DO: Adjust to different file formats

        if image.ndim == 3:
            image = np.expand_dims(image, axis=-1)  # adds axes to 2D images
            image = np.expand_dims(image, axis=-1)
            data = image.swapaxes(0, 4).swapaxes(1, 3).swapaxes(0, 1).swapaxes(1,
                                                                               2)  # Re-organise array from xyczt to zctyx order expected by OMERO
        else:
            print(f"Your image dimensions do not fit the requirements.")

        result_images.append(data)

    return parent_id, result_images

def print_obj(obj, indent=0):
    """
    Helper method to display info about OMERO objects.
    Not all objects will have a "name" or owner field.
    """
    print("""%s%s:%s  Name:"%s" (owner=%s)""" % (
        " " * indent,
        obj.OMERO_CLASS,
        obj.getId(),
        obj.getName(),
        obj.getOwnerOmeName()))


def get_parent_well(parent_id):
    """ Retrieves the well of the parent image.
    Returns the parent image object, and row and column number."""

    parent_image = conn.getObject("Image", parent_id)
    for wellsample in parent_image.listParents():
        parent_well = wellsample.getParent(withlinks=False)
        parent_well_id = parent_well.getId()
        result_row = parent_well.row
        result_column = parent_well.column

    return parent_image, result_row, result_column


def upload_image_from_npseq(image, image_path, conn, dataset):

    def plane_gen():
        """
        Set up a generator of 2D numpy arrays.
        The createImage method below expects planes in the order specified here
        (for z.. for c.. for t..)
        """
        size_z = image.shape[0] - 1
        for z in range(image.shape[0]):  # all Z sections data.shape[0]
            print('z: %s/%s' % (z, size_z))
            for c in range(image.shape[1]):  # all channels
                for t in range(image.shape[2]):  # all time-points
                    yield image[z][c][t]

    image_name = str(image_path).rsplit("\\")[-1]  # New Image name # TO DO: Include correct tag
    omero_image = conn.createImageFromNumpySeq(plane_gen(), image_name, image.shape[0],
                                                   image.shape[1], image.shape[2], description=None, dataset=dataset)


    print("Image uploaded:", omero_image.id, ":", image_name)

    return omero_image


"""def upload_image_using_ezomero(image, image_path, conn, dataset, parent_id):

    image_name = str(image_path).rsplit("\\")[-1]  # New Image name # TO DO: Include correct tag
    omero_image = ezomero.post_image(conn, image, image_name, dim_order= "xyczt", dataset_id=dataset, source_image_id = parent_id)

    print("Image uploaded:", omero_image.id, ":", image_name)

    return omero_image"""


def add_images_to_plate(conn, images, plate_id, column, row, remove_from=None):
    """
    Add the Images to a Plate, creating a new well at the specified column and
    row
    NB - This will fail if there is already a well at that point
    https://github.com/ome/omero-scripts/blob/develop/omero/util_scripts/Dataset_To_Plate.py

    """
    update_service = conn.getUpdateService()

    well = omero.model.WellI()
    well.plate = omero.model.PlateI(plate_id, False)
    well.column = rint(column)
    well.row = rint(row)

    try:
        for image in images:
            ws = omero.model.WellSampleI()
            ws.image = omero.model.ImageI(image.id, False)
            ws.well = well
            well.addWellSample(ws)
        update_service.saveObject(well)
    except Exception:
        return False

    # remove from Dataset
    for image in images:
        if remove_from is not None:
            links = list(image.getParentLinks(remove_from.id))
            link_ids = [l.id for l in links]
            conn.deleteObjects('DatasetImageLink', link_ids)
    return True

