import arcpy
import requests
import csv

arcpy.env.overwriteOutput = True

ADDRESSES_CSV = r"C:\Users\benlj\OneDrive\Documents\School\SpringSemester2025\ProgrammingForGIS\addresses.csv"
NEW_ADDRESSES_CSV = r"C:\Users\benlj\OneDrive\Documents\School\SpringSemester2025\ProgrammingForGIS\new_addresses.csv"
GDB = r"C:\Users\benlj\OneDrive\Documents\School\SpringSemester2025\ProgrammingForGIS\ProgrammingLabs\ProgrammingLabs.gdb"


def extract():
    url = (
        "https://docs.google.com/spreadsheets/d/e/"
        "2PACX-1vTDjitOlmILea7koCORJkq6QrUcwBJM7K3vy4guXB0mU_nWR6wsPn136bpH6ykoUxyYMW7wTwkzE37l/pub?output=csv"
    )
    r = requests.get(url)
    r.encoding = "utf-8"
    data = r.text

    with open(ADDRESSES_CSV, "w", encoding="utf-8", newline="") as output_file:
        output_file.write(data)


def transform():
    with open(NEW_ADDRESSES_CSV, "w", encoding="utf-8", newline="") as transformed_file:
        transformed_file.write("X,Y,Type\n")

        with open(ADDRESSES_CSV, "r", encoding="utf-8") as partial_file:
            csv_dist = csv.DictReader(partial_file, delimiter=",")
            for row in csv_dist:
                # Adjust key name if the column name is slightly different
                street = row["Street Address"]
                address = f"{street}, Boulder, CO"
                print(address)

                base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
                params = {
                    "address": address,
                    "benchmark": "2020",
                    "format": "json",
                }
                r = requests.get(base_url, params=params)

                if r.status_code != 200:
                    print(f"Request failed for: {address} (status {r.status_code})")
                    continue

                resp_dict = r.json()
                matches = resp_dict.get("result", {}).get("addressMatches", [])
                if not matches:
                    print(f"No match for: {address}")
                    continue

                coords = matches[0]["coordinates"]
                x = coords["x"]
                y = coords["y"]

                transformed_file.write(f"{x},{y},Residential\n")


def load():
    arcpy.env.workspace = GDB
    arcpy.env.overwriteOutput = True

    in_table = NEW_ADDRESSES_CSV
    out_feature_class = "avoid_points"
    x_coords = "X"
    y_coords = "Y"
    sr = arcpy.SpatialReference(4269)  # NAD 1983 (Census default)

    arcpy.management.XYTableToPoint(in_table, out_feature_class, x_coords, y_coords, coordinate_system=sr)
    print(arcpy.GetCount_management(out_feature_class))


if __name__ == "__main__":
    extract()
    transform()
    load()
