import logging
import arcpy
import os
import yaml
from etl.Assignment11_SpatialEtl import GSheetEtl
"""
Final Project: West Nile Virus Outbreak Simulation
GIS 3005
May 2025

This script buffers potential mosquito breeding sites, intersects them to find high-risk zones, erases spraying sensitive areas,
geocodes address data, performs spatial joins, and exports the results to a map layout.

"""
#setup
def setup():
    """
        Loads the YAML configuration file and sets up logging for the project.

        Returns:
            dict: Configuration settings loaded from YAML.
        """
    with open('../config/wnvoutbreak.yaml') as f:
        config = yaml.safe_load(f)

    # Configure logging — writes to your project directory
    log_path = os.path.join(config['proj_dir'], 'wnv.log')
    logging.basicConfig(
        filename=str(log_path),
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.debug("Entered setup function")
    logging.debug("Exited setup function")
    return config

#Buffer Analysis
def buffer_layer(layer_name, distance_ft, config_dict):
    """Buffers a given input layer by a specified distance.

    Args:
        layer_name (str): Name of the layer to buffer.
        distance_ft (float): Buffer distance in feet.
        config_dict (dict): Configuration dictionary containing output paths.

    Returns:
        str: Path to the buffered output feature class.
    """
    try:

        logging.debug(f'Entered buffer_layer for {layer_name}')

        # Define output name and path
        output_name = f"{layer_name}_buffer"
        output_path = os.path.join(config_dict['destination'], output_name)
        distance_str = f"{distance_ft} Feet"

        arcpy.Buffer_analysis(
            in_features=layer_name,
            out_feature_class=output_path,
            buffer_distance_or_field=distance_str,
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="ALL"
        )

        logging.info(f"Buffer created for {layer_name}")
        logging.debug(f'Exiting buffer_layer for {layer_name}')

        return output_path

    except Exception as e:
        logging.error(f'Error in buffer_layer: {e}')
        print('An error occurred in buffer_layer.')

#Loop through layers
def buffer_loop(config_dict):
    """
    Prompts the user for a buffer distance and applies that buffer to a predefined list of layers.

    This function loops through a list of potential mosquito breeding site layers,
    applies a uniform buffer to each using the `buffer_layer()` function, and collects the output paths.

    Args:
        config_dict (dict): Configuration dictionary containing project paths and workspace settings.

    Returns:
        list: A list of paths to the buffered output feature classes.
    """

    layers = [
        "Mosquito_Larval_Sites",
        "Wetlands",
        "Lakes_and_Reservoirs___Boulder_County",
        "OSMP_Properties"
    ]

    while True:
        try:
            distance = float(input("Enter buffer distance in feet for all layers: "))
            break
        except ValueError:
            print("Please enter a valid number.")

    buffer_outputs = []
    try:
        for layer in layers:
            output_path = buffer_layer(layer, distance, config_dict)
            buffer_outputs.append(output_path)

        logging.debug(f'Entered buffer_loop')

        return buffer_outputs
    except Exception as e:
        logging.error(f'Error in buffer_loop: {e}')
        print('An error occurred in buffer_loop.')

#Intersect Analysis
def intersect_buffers(buffer_outputs, config_dict):
    """
      Intersects multiple buffered feature layers into a single feature class.

      Args:
          buffer_outputs (list): List of buffered feature class paths.
          config_dict (dict): Configuration dictionary with output destination.

      Returns:
          str: Path to the output intersected feature class.
      """

    output_name = input("Enter name for the intersect output layer: ")
    output_path = os.path.join(config_dict['destination'], output_name)

    logging.info("Running intersect on buffer layers...")
    try:
        arcpy.Intersect_analysis(in_features=buffer_outputs, out_feature_class=output_path)

        logging.info(f"Intersect complete: {output_path}")
        logging.debug(f"Exiting Intersect")

        return output_path

    except Exception as e:
        logging.error(f'Error in intersect_buffers: {e}')
        print('An error occurred in intersect_buffers.')

#Spatial Join Intersect and Addresses
def spatial_join(intersect_layer, config_dict):
    """
     Performs a spatial join between the address layer and a high-risk zone layer.

     Args:
         intersect_layer (str): Path to the intersected polygon layer.
         config_dict (dict): Configuration dictionary with output destination.

     Returns:
         str: Path to the joined output feature class.
     """
    address_layer = 'Addresses'
    output_name = "Addresses_At_Risk"
    output_path = os.path.join(config_dict['destination'], output_name)

    logging.debug("Running spatial join between addresses and intersected risk zone...")
    try:

        arcpy.analysis.SpatialJoin(
            target_features=address_layer,
            join_features=intersect_layer,
            out_feature_class=output_path,
            join_type="KEEP_COMMON",          # Keep all addresses
            match_option="INTERSECT"
        )

        logging.info(f"Spatial join complete: {output_path}")
        logging.debug(f'Exiting Spatial Join')
        return output_path

    except Exception as e:
        logging.error(f'Error in spatial_join: {e}')
        print('An error occurred in spatial_join.')
def count_at_risk_addresses(joined_fc):
    """
      Counts and logs the number of addresses that fall within the joined high-risk area.

      Args:
          joined_fc (str): Path to the spatially joined feature class.
      """
    try:
        count = 0
        with arcpy.da.SearchCursor(joined_fc, ["Join_Count"]) as cursor:
            for row in cursor:
                if row[0] and row[0] >= 1:
                    count += 1
        logging.info(f"Number of addresses within the risk zone: {count}")

    except Exception as e:
        logging.error(f'Error in count_at_risk_addresses: {e}')
        print('An error occurred in count_at_risk_addresses.')

#ETL Function
def etl(config_dict):
    """
        Runs the ETL (Extract, Transform, Load) process using the GSheetEtl class.

        Args:
            config_dict (dict): Configuration dictionary containing data sources and destinations.
        """
    logging.debug('Start etl process...')
    try:
        etl_instance = GSheetEtl(config_dict)

        etl_instance.process()

    except Exception as e:
        logging.error(f'Error in etl: {e}')
        print('An error occurred in etl.')

#Erase Function
def erase_avoid_zones(intersect_fc, config_dict):
    """
     Removes areas around sensitive locations (e.g. schools) from the risk zone layer.

        Args:
            intersect_fc (str): Path to the intersected buffer feature class.
            config_dict (dict): Configuration dictionary with output destination.

        Returns:
            str: Path to the cleaned risk zone feature class after erasing avoid areas.
        """
    avoid_buffer = os.path.join(config_dict['destination'],'Avoid_Points_buffer')
    output_name = 'Risk_Zone_Cleaned'
    output_path = os.path.join(config_dict['destination'], output_name)
    try:
        arcpy.analysis.Erase(
            in_features=intersect_fc,
            erase_features=avoid_buffer,
            out_feature_class=output_path
        )
        logging.info(f"Erase complete")
        logging.debug('Analysis Complete!')

        return output_path

    except Exception as e:
        logging.error(f'Error in erase_avoid_zones: {e}')
        print('An error occurred in erase_avoid_zones.')

def spatial_join_to_final(cleaned_layer, config_dict):
    """
    Performs a spatial join between addresses and the cleaned risk zone to get final targets.

    Args:
        cleaned_layer (str): Path to the cleaned (erased) risk zone feature class.
        config_dict (dict): Configuration dictionary with output destination.

    Returns:
        str: Path to the output feature class with only target addresses.
    """
    output_name = "Target_Addresses"
    output_path = os.path.join(config_dict['destination'], output_name)
    try:

        arcpy.analysis.SpatialJoin(
            target_features="Addresses",
            join_features=cleaned_layer,
            out_feature_class=output_path,
            join_type="KEEP_COMMON",
            match_option="INTERSECT"
        )

        return output_path
    except Exception as e:
        logging.error(f"Error in spatial_join_to_final: {e}")
        print("An error occurred in spatial_join_to_final.")

def exportMap(config_dict):
    """
        Prompts for a map subtitle, updates the layout, and exports it as a PDF.

        Args:
            config_dict (dict): Configuration dictionary containing the project directory.
        """
    logging.debug("Entered exportMap function")

    try:
        # Get project
        aprx_path = os.path.join(config_dict['proj_dir'], 'Programming_Lab1.aprx')
        aprx = arcpy.mp.ArcGISProject(aprx_path)

        # Get layout
        lyt = aprx.listLayouts('Layout3')[0]

        # Ask for user subtitle
        subtitle = input("Enter a subtitle for your map layout: ")

        # Update the title element
        for elm in lyt.listElements("TEXT_ELEMENT"):
            if "Text" in elm.name:
                logging.debug(f"Found title element: {elm.name}")
                elm.text += f"\n{subtitle}"
                logging.info(f"Updated map title with subtitle: {subtitle}")

        # Export the layout to a PDF
        output_pdf = os.path.join(config_dict['proj_dir'], 'WestNileOutbreakMap.pdf')
        lyt.exportToPDF(output_pdf)

        logging.info(f"Exported map to PDF at: {output_pdf}")
        logging.debug("Exiting exportMap function")

    except Exception as e:
        logging.error(f"Error in exportMap: {e}")
        print("An error occurred in exportMap.")

def main(config_dict):
    def main(config_dict):
        """
        Runs the full geoprocessing workflow:
        - Buffers all layerss
        - Intersects buffered layers
        - Erases avoid areas
        - Joins addresses within the risk zone
        - Applies symbolization, definition query, and saves project

        Args:
            config_dict (dict): Configuration dictionary with paths, layers, and workspace settings.
        """

    try:
        logging.info("Starting West Nile Virus Simulation")

        # Set workspace
        arcpy.env.workspace = config_dict['destination']
        arcpy.env.overwriteOutput = True

        # Load map
        project_path = os.path.join(config_dict['proj_dir'], 'Programming_Lab1.aprx')
        project = arcpy.mp.ArcGISProject(project_path)
        map_obj = project.listMaps()[0]

        # Run geoprocessing
        buffer_outputs = buffer_loop(config_dict)
        intersect_result = intersect_buffers(buffer_outputs, config_dict)
        cleaned_result = erase_avoid_zones(intersect_result, config_dict)
        joined_result = spatial_join(cleaned_result, config_dict)
        count_at_risk_addresses(joined_result)

        target_result = spatial_join_to_final(cleaned_result, config_dict)
        map_obj.addDataFromPath(target_result)

        target_layer = map_obj.listLayers("Target_Addresses")[0]
        target_layer.definitionQuery = "Join_Count = 1"

        map_obj.addDataFromPath(intersect_result)
        map_obj.addDataFromPath(joined_result)
        map_obj.addDataFromPath(target_result)

        final_layer = map_obj.listLayers("Risk_Zone_Cleaned")[0]

        sym = final_layer.symbology
        sym.updateRenderer('SimpleRenderer')

        sym.renderer.symbol.applySymbolFromGallery("Polygon")
        sym.renderer.symbol.color = {'RGB': [255, 0, 0, 127]}
        sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 255]}

        final_layer.symbology = sym
        project.save()

    except Exception as e:
        logging.error(f"Error in main: {e}")
        print("An error occurred in main().")

if __name__ == '__main__':
    try:
        config_dict = setup()
        logging.debug(f"Loaded config: {config_dict}")
        etl(config_dict)
        main(config_dict)
        exportMap(config_dict)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("An error occurred. Check the log file for details.")
