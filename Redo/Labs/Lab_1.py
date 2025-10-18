import arcpy
import os

# Set environments
arcpy.env.workspace = r"C:\Users\benlj\OneDrive\Documents\School\SpringSemester2025\ProgrammingForGIS\Lab_1\Programming_Lab1\Programming_Lab1.gdb"
arcpy.env.overwriteOutput = True
project = arcpy.mp.ArcGISProject(r"C:\Users\benlj\OneDrive\Documents\School\SpringSemester2025\ProgrammingForGIS\Lab_1\Programming_Lab1\Programming_Lab1.aprx")
map_obj = project.listMaps()[0]

#Buffer Analysis
def buffer_layer(layer_name, distance_ft):

    # Define output name and path
    output_name = f"{layer_name}_buffer"
    output_path = os.path.join(arcpy.env.workspace, output_name)
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
def buffer_loop():
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
        output_path = buffer_layer(layer, distance)
        buffer_outputs.append(output_path)

    return buffer_outputs

#Intersect Analysis
def intersect_buffers(buffer_outputs):

    response = input('Would you like to intersect the buffered layers?(yes/no): ').strip().lower()

    if response not in ['yes', 'y']:
        print ('Okie dokie pardner!')
        exit()

    output_name = input("Enter name for the intersect output layer: ")
    output_path = os.path.join(arcpy.env.workspace, output_name)

    print("Running intersect on buffer layers...")
    arcpy.Intersect_analysis(in_features=buffer_outputs, out_feature_class=output_path)

    print(f"Intersect complete: {output_path}")
    return output_path

#Spatial Join Intersect and Addresses
def spatial_join(intersect_layer):
    address_layer = 'Addresses'
    output_name = "Addresses_At_Risk"
    output_path = os.path.join(arcpy.env.workspace, output_name)

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

buffer_outputs = buffer_loop()
intersect_result = intersect_buffers(buffer_outputs)
joined_result = spatial_join(intersect_result)
count_at_risk_addresses(joined_result)

map_obj.addDataFromPath(intersect_result)
map_obj.addDataFromPath(joined_result)

project.save()