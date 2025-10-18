import arcpy
import os
import yaml
from etl.Assignment_11 import GSheetEtl

#setup
def setup():
    with open('config/wnvoutbreak.yaml') as f:
        config = yaml.safe_load(f)
    return config

#Buffer Analysis
def buffer_layer(layer_name, distance_ft, config_dict):

    # Define output name and path
    output_name = f"{layer_name}_buffer"
    output_path = os.path.join(config_dict['destination'], output_name)
    distance_str = f"{distance_ft} Feet"

    print(f"Buffering {layer_name} by {distance_str}")

    # Buffer analysis
    arcpy.Buffer_analysis(
        in_features=layer_name,
        out_feature_class=output_path,
        buffer_distance_or_field=distance_str,
        line_side="FULL",
        line_end_type="ROUND",
        dissolve_option="ALL"
    )

    print(f"Buffer created")
    return output_path

#Loop through layers
def buffer_loop(config_dict):
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

    for layer in layers:
        output_path = buffer_layer(layer, distance, config_dict)
        buffer_outputs.append(output_path)

    return buffer_outputs

#Intersect Analysis
def intersect_buffers(buffer_outputs, config_dict):

    response = input('Would you like to intersect the buffered layers?(yes/no): ').strip().lower()

    if response not in ['yes', 'y']:
        print ('Okie dokie pardner!')
        exit()

    output_name = input("Enter name for the intersect output layer: ")
    output_path = os.path.join(config_dict['destination'], output_name)

    print("Running intersect on buffer layers...")
    arcpy.Intersect_analysis(in_features=buffer_outputs, out_feature_class=output_path)

    print(f"Intersect complete: {output_path}")
    return output_path

#Spatial Join Intersect and Addresses
def spatial_join(intersect_layer, config_dict):
    address_layer = 'Addresses'
    output_name = "Addresses_At_Risk"
    output_path = os.path.join(config_dict['destination'], output_name)

    print("Running spatial join between addresses and intersected risk zone...")

    arcpy.analysis.SpatialJoin(
        target_features=address_layer,
        join_features=intersect_layer,
        out_feature_class=output_path,
        join_type="KEEP_COMMON",          # Keep all addresses
        match_option="INTERSECT"
    )

    print(f"Spatial join complete: {output_path}")
    return output_path

def count_at_risk_addresses(joined_fc):
    count = 0
    with arcpy.da.SearchCursor(joined_fc, ["Join_Count"]) as cursor:
        for row in cursor:
            if row[0] and row[0] >= 1:
                count += 1
    print(f"Number of addresses within the risk zone: {count}")

#ETL Function
def etl(config_dict):
    print('Start etl process...')

    etl_instance = GSheetEtl(config_dict)

    etl_instance.process()

#Erase Function
def erase_avoid_zones(intersect_fc, config_dict):
    avoid_buffer = os.path.join(config_dict['destination'],'Avoid_Points_buffer')
    output_name = 'Risk_Zone_Cleaned'
    output_path = os.path.join(config_dict['destination'], output_name)

    arcpy.analysis.Erase(
        in_features=intersect_fc,
        erase_features=avoid_buffer,
        out_feature_class=output_path
    )
    print(f"Erase complete!")
    return output_path

def main(config_dict):
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

    map_obj.addDataFromPath(intersect_result)
    map_obj.addDataFromPath(joined_result)
    project.save()

if __name__ == '__main__':
    config_dict = setup()
    print(config_dict)
    etl(config_dict)
    main(config_dict)




