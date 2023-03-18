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
import pathlib


def well_name_to_position(well_name):
    """
    Translates a well name (e.g. A1, B2, etc) to row and column position in a 384-well plate.
    Returns a tuple of integers (row, column).
    """
    rows = 'ABCDEFGHIJKLMNOP'
    row = rows.index(well_name[0])
    column = int(well_name[1:]) - 1
    return (row, column)



def load_pipeline(pipe_dir):
    pipeline = cellprofiler_core.pipeline.Pipeline()
    pipeline.load(pipe_dir)

    return pipeline


def get_save_image_module_indices(pipeline):
    """ ChatGPT"""
    save_image_module_indices = []
    for module in pipeline.modules():
        if module.module_name == "SaveImages":
            save_image_module_indices.append(module.module_num)
    if not save_image_module_indices:
        raise ValueError("Pipeline does not contain any SaveImages modules.")

    return save_image_module_indices


def adjust_pipeline(pipeline, overwrite_results, output_file_format):
    """ChatGPT"""
    # Remove first 4 modules: Images, Metadata, NamesAndTypes, Groups...
    # Those will be replaced by InjectImage module
    for i in range(4):
        print('Remove module: ', pipeline.modules()[0].module_name)
        pipeline.remove_module(1)

    # Find all export modules:
    export_module = [mod for mod in pipeline.modules() if mod.module_name == "ExportToSpreadsheet"]
    # Adjust export modules:
    for mod in export_module:
        for setting in mod.settings():
            if setting.text == "Overwrite existing files without warning?":
                setting.set_value(overwrite_results)
            if setting.text == "Output file location":
                setting.set_value("Default Output Folder|")

    # Find all saving modules:
    saving_modules = [mod for mod in pipeline.modules() if mod.module_name == "SaveImages"]
    # Overwriting files and saving format
    for mod in saving_modules:
        for setting in mod.settings():
            if setting.text == "Overwrite existing files without warning?":
                setting.set_value(overwrite_results)
            if setting.text == "Saved file format":
                setting.set_value(output_file_format)

    print('Pipeline modules:')
    for module in pipeline.modules():
        print(module.module_num, module.module_name)

    return pipeline


def update_save_images_module_setting(pipeline, image_id):
    for module in pipeline.modules():
        if module.module_name == "SaveImages":
            for setting in module.settings():
                if setting.text == "Enter single file name":
                    apendix = setting.get_value()
                    new_file_name = f"{image_id}_{apendix}"
                    setting.set_value(new_file_name)
                    #print(f"Updated SaveImages module setting: {setting.text} = {new_file_name}")

    return pipeline


def update_export_module_setting(pipeline, image_id):
    for module in pipeline.modules():
        if module.module_name == "ExportToSpreadsheet":
            for setting in module.settings():
                if setting.text == "Add a prefix to file names?":
                    setting.set_value("Yes")
                elif setting.text == "Filename prefix":
                    new_prefix = f"{image_id}_"
                    setting.set_value(new_prefix)
                    #print(f"Updated ExportToSpreadsheet module setting: {setting.text} = {new_prefix}")
    return pipeline


def upload_images_to_omero(saving_path, output_file_format, results_dataset, conn, OMEROWEB):
    

    for img_path in pathlib.Path(saving_path).glob((f"*{output_file_format}")):
        try:
            parent_id, image = load_result_image_from_disk(img_path)
            image_link = f"Original Image: {OMEROWEB}?show=image-{parent_id}"
            omero_image = upload_image_from_npseq(image, img_path, conn, results_dataset, image_link)

        except Exception as e:
            print(f"Upload failed for {img_path}: {e}")
            
    return omero_image


def retrieve_selected_export_measurements(pipeline):

    for mod in range(len(pipeline.modules())):
        if pipeline.modules()[mod].module_name == "ExportToSpreadsheet":
            for set in range(len(pipeline.modules()[mod].settings())):
                selected_measurements = pipeline.modules()[i].setting(14).get_value()   #Make generic

    return selected_measurements




def load_result_image_from_disk(img_path):
    """ Loads the image from disk using cv2, prepares the image axes and axis order to zctyx order that is expected by omero.
    Returns parent_id, and the image."""

    # TO DO: include loading multiple images with different tags

    _, tail = os.path.split(img_path)
    parent_id = os.path.splitext(tail)[0].split("_")[0]
    print("Parent image id:", parent_id)
    image = cv2.imread(img_path.__str__(), -1)  # TO DO: Adjust to different file formats

    # TO DO: include check how many axes are there

    image = np.expand_dims(image, axis=-1)  # adds axes to 2D images
    image = np.expand_dims(image, axis=-1)
    image = image.swapaxes(0, 3).swapaxes(1, 4).swapaxes(0, 1).swapaxes(1, 2) # Re-organise array from xyczt to zctyx order expected by OMERO

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
            data = image.swapaxes(0, 3).swapaxes(1, 4).swapaxes(0, 1).swapaxes(1,
                                                                               2)  # Re-organise array from xyczt to zctyx order expected by OMERO
        else:
            print(f"Image {parent_id} dimensions do not fit the requirements.")

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



def upload_image_from_npseq(image, image_path, conn, dataset, image_link):

    def plane_gen():
        """
        Set up a generator of 2D numpy arrays.
        The createImage method below expects planes in the order specified here
        (for z.. for c.. for t..)
        """

        for z in range(image.shape[0]):  # all Z sections data.shape[0]
            for c in range(image.shape[1]):  # all channels
                for t in range(image.shape[2]):  # all time-points
                    yield image[z][c][t]

    image_name = str(image_path).rsplit("\\")[-1]  # New Image name # TO DO: Include correct tag
    omero_image = conn.createImageFromNumpySeq(plane_gen(), image_name, image.shape[0],
                                                   image.shape[1], image.shape[2], description=image_link, dataset=dataset)


    print("Image uploaded:", omero_image.id, ":", image_name)

    return omero_image


def add_images_to_well(conn, images, plate_id, column, row, remove_from=None):
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


def add_images_to_plate(omero_images, plate_id, results_plate_id, conn, results_dataset):
    
    plate = conn.getObject("Plate", plate_id)
    dict_id_position = {}
    dict_position_id = {}
    for well in plate.listChildren():
        index = well.countWellSample()
        id_list = []
        for index in range(0, index):
            id_list.append(well.getImage(index).getId())
            dict_id_position[well.getImage(index).getId()] = (well.row, well.column)
        dict_position_id[(well.row, well.column)] = id_list
    for (row, column) in dict_position_id:
        omero_images_select = [omero_image for omero_image in omero_images if int(omero_image.name.split("_")[0]) in dict_position_id[(row,column)]]
        success = add_images_to_well(conn, omero_images_select, results_plate_id, column, row, remove_from=results_dataset)
        if success:
            print(f"You succesfully uploaded all images to the new plate {results_plate_id}.")
        if not success:
            print("Upload failed.")