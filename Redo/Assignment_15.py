import csv
import os
import arcpy.management
import requests


class SpatialEtl:
    """
    A base class for performing ETL (Extract, Transform, Load) operations for spatial data.

    Attributes:
        config_dict (dict): Configuration parameters loaded from YAML.
        remote (str): URL of the remote dataset.
        local_dir (str): Path to the local working directory.
        data_format (str): Data format (e.g., 'csv').
        destination (str): Path to output geodatabase.
        geocoder_prefix_url (str): URL prefix for the geocoding service.
        geocoder_suffix_url (str): URL suffix for the geocoding service.
    """
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.remote = config_dict['remote_url']
        self.local_dir = config_dict['proj_dir']
        self.data_format = config_dict['data_format']
        self.destination = config_dict['destination']
        self.geocoder_prefix_url = config_dict['geocoder_prefix_url']
        self.geocoder_suffix_url = config_dict['geocoder_suffix_url']
    def extract(self):
        print(f"Extracting data from {self.remote} to {self.local_dir}")
    def transform(self):
        print(f"Transforming {self.data_format}")
    def load(self):
        print(f"Loading {self.destination}")

#from SpatialEtl import SpatialEtl

class GSheetEtl(SpatialEtl):
    """
    Specialized ETL class to extract data from a Google Sheet, geocode it, and convert it to GIS format.
    """
    def __init__(self, config_dict):
        super().__init__(config_dict)

    def extract(self):
        """
        Downloads CSV data from the remote Google Sheets URL and saves it locally.
        """
        print(f"Extracting addresses from google sheets")
        r = requests.get(
            self.remote
        )
        r.encoding = 'utf-8'
        data = r.text

        output_file_path = os.path.join(self.local_dir, 'addresses.csv')
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(data)

        self.local_path = output_file_path

    def transform(self):
        """
        Extracts address from the CSV and then geocodes the addresses.
        """
        print(f"Transform addresses via geocoding")
        input_csv = self.local_path
        output_csv = os.path.join(self.local_dir, 'geocoded_addresses.csv')
        self.transformed_path = output_csv

        with open(input_csv, 'r', encoding='utf-8') as infile, \
            open(output_csv, 'w', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile)
            writer = csv.writer(outfile)
            writer.writerow(['X', 'Y', 'Type'])

            for row in reader:
                address = row['Address'] + ' Boulder CO'
                print (f'Geocoding: {address}')

                geocode_url = self.geocoder_prefix_url + f"?address={address}" + self.geocoder_suffix_url

                r = requests.get(geocode_url)
                try:
                    resp = r.json()
                    match = resp['result']['addressMatches'][0]
                    x = match['coordinates']['x']
                    y = match['coordinates']['y']
                    writer.writerow([x, y, "Residential"])
                except (IndexError, KeyError):
                    print("No match for:", address)

    def load(self):
        """
        Creates a point layer inside ArcPro from the geocoded addresses.
        """
        print(f'Loading geocoded addresses')

        arcpy.env.workspace =self.destination
        arcpy.env.overwriteOutput = True

        in_table = self.transformed_path
        out_feature_class = 'avoid_points'
        x_field = 'X'
        y_field = 'Y'
        spatial_ref = arcpy.SpatialReference(104124)

        arcpy.management.XYTableToPoint(
            in_table=in_table,
            out_feature_class=out_feature_class,
            x_field=x_field,
            y_field=y_field,
            coordinate_system=spatial_ref
        )
        print(arcpy.GetCount_management(out_feature_class))

        avoid_buffer = os.path.join(self.destination, 'Avoid_Points_buffer')
        arcpy.Buffer_analysis('avoid_points', avoid_buffer, '1500 Feet', 'FULL', 'ROUND', 'ALL')

    def process(self):
        self.extract()
        self.transform()
        self.load()