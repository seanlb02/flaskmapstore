from flask import Flask, jsonify
from flask import flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
from flask import render_template
import geopandas as gpd
import io
from fiona.io import ZipMemoryFile
import fiona
import tempfile
from fiona.io import ZipMemoryFile
import zipfile
import copy
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
ALLOWED_EXTENSIONS = {'zip', 'shp', 'cpg', 'prj', '.sbn', '.shx', '.xml', '.qmd', '.qix', 'sbx'}

@app.route('/', methods=['POST'])
def index():
    if request.method == 'POST':        
                # retrieve the file sent via post request (the 'input' element name is data_zip_file)
        file = request.files['data_zip_file']
            # result dicts get stored in this list to be iterated in the html table via jinja
        res_list = []
        try:

                # Sanitize first input (.zip)
            if file and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                file_like_object = file.stream._file  
                data = file_like_object.read()
                zipfile_ob = zipfile.ZipFile(file_like_object)
                file_names = zipfile_ob.namelist()
                # Sanitize files WITHIN the zip folder
                for item in file_names: 
                    try:
                        if item.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                            raise fiona.errors.DriverError
                    except:
                            raise fiona.errors.DriverError
                    else:
                        with ZipMemoryFile(data) as zip:
                            for shapefile in file_names:
                                if shapefile.rsplit('.', 1)[1].lower() == 'shp':
                                    res_item = {}
                                    layer_name = shapefile[:-4]
                                    geometry = ""
                                    projection = ""
                                    corr_file = ""
                                    no_attr = ""
                                    geo_err = ""
                                    topo_err = ""
                                        # with zip.open(f'{file_names[0][:-4]}.shp') as collection:
                                    with zip.open(f'{shapefile}') as collection:
                                        gdf = gpd.GeoDataFrame.from_features([feature for feature in collection], crs=collection.crs)
                                    gdf.sindex
                                    geometry = str(gdf.geom_type[0])
                                    projection = gdf.crs.name
                                    # geom err check:
                                    if False in gdf.is_valid.values:
                                        geom_error = "Yes"
                                    else: 
                                        geom_error = "No"
                                    
                                    # corrupt geometry check:
                                    corr_file = ""
                                    if True in gdf.is_empty.values:
                                        corr_file = "Yes"
                                    else:
                                        corr_file= "No"
                                    # empty attribute table:
                                    if gdf.shape[1] >= 4:
                                        no_attr = "Present"
                                    else:
                                        no_attr = "None"
                                    # Topology check
                                    # We only check Topology/Geometry errors for polygons and multilines
                                    if 'Point' in gdf.geom_type:
                                        pass
                                    else:
                                        # new dummy dataframe to host any overlapping layers
                                        sdf = gdf.sindex.query(gdf.geometry, predicate='overlaps')
                                        # if there are any:
                                        if sdf.size != 0:
                                            topo_error = "Yes"
                                        else:
                                            topo_error = "No"
                                    res_list = [*res_list, [layer_name, geometry, projection, corr_file, no_attr, geom_error, topo_error]]
            
        except fiona.errors.DriverError: 
            pass

        return str(res_list)

@app.route('/get', methods=['GET'])
def getlayer():
    if request.method == 'GET':
        return jsonify({"hello": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
