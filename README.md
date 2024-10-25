# Spatial Photogrammetry Optimization Tools - SPOT

Python script to process and optimize material created from spatial photogrammetry (from software such as Pix4D Mapper, Pix4D Matic, Agisoft Metashape, Drone Deploy, etc.) to facilitate uploading to the web, downloading, viewing from the browser and on the desktop , incorporation to geoservers and more. It can process both RGB and MDE orthomosaics, as 3D models or point clouds.

The script creates the following files:

- to upload to the geoserver
  - .tif in intermediate quality (with pyramid overviews/render at different scales), EPSG:3857
  - .geojson with the outline of the image to upload to the wms, with the gsd, srs, registryid and date fields (if it exists)
- to upload to the cloud:
  - raster .tif in low quality to use as preview (w:650px), original EPSG
  - raster .tif in high quality, ideal for importing from [QGis](https://www.qgis.org/), original EPSG
  - raster .tif in medium quality, ideal for use in AutoCAD or Civil 3D, original EPSG
  - world file .tfw with the geospatial information (to use when importing into AutoCAD, for example)
- for download or viewing in the browser:
  - 3d model .glb to open with any 3d model viewer (with compression [draco](https://google.github.io/draco/))
  - .laz point cloud to open with point cloud viewer (with optimization [COPC](https://copc.io/), to open on the web with [Potree](https://github.com/potree/potree/) or on the desktop with [QGis](https://www.qgis.org/))

## Installation

### Using requeriments and Python 3.12
- Create an virtual enviroment `python3.12 -m venv .venv`
- Load the enviroment `.venv/Scripts/activate`
- Install the requeriments `pip install requeriments.txt`
- Manually install an npm package to compress the 3d models: `npm install -g gltf-pipeline`: [gltf-pipeline](https://github.com/CesiumGS/gltf-pipeline)

### Manual installation (windows)
- If you what to use another python version, or install manually al the components, use:
- Download [GDAL](https://github.com/cgohlke/geospatial-wheels/releases/), selecting the newest version of GDAL, and the appropriate one according to the version of Python installed and the processor. If you are using Python 3.7, for example, download and then install using `pip install GDAL-3.3.1-cp37-cp37m-win_amd64.whl` (always adjusting according to the downloaded version).
- Download [Rasterio](https://github.com/cgohlke/geospatial-wheels/releases/), selecting a version analogous to GDAL, and install in the same way.
- To be able to use the installed package from the console, configure environment variables (putting the full path depending on where the package is installed and the python version):
  - `GDAL_DATA`: '...\Python\Python37\Lib\site-packages\osgeo\data\gdal'
  - `PROJ_LIB`: '...\Python\Python37\Lib\site-packages\osgeo\data\proj'
  - Add to the `Path` variable the path '...\Python\Python37\Lib\site-packages\osgeo'
  - Check `gdalinfo --version` in console.
- Install the libraries:
  - [Numpy](https://numpy.org/)
  - [PIL](https://python-pillow.org/) (for creating previews) 
  - To process point clouds:
    - [laspy](https://laspy.readthedocs.io/en/latest/index.html)
  - To process 3d models:
    - [trimesh](https://trimesh.org/index.html):
    - [pygltflib](https://pypi.org/project/pygltflib/)
    - [gltf-pipeline](https://github.com/CesiumGS/gltf-pipeline) (NodeJS): `npm install -g gltf-pipeline`

## Use

- Place the .tif/.tiff orthomosaics in the highest resolution available in the `input` folder. If the orthomosaic to be processed is in tiles format, create a containing folder with all the corresponding images.
- If you want to process a 3D model, place the .obj and its corresponding texture and mtl loosely in the same `input` folder.
- Name the complete orthomosaics (or the containing folder in the case of tiles, or objs) the audiovisual record number to which they belong (this data will be incorporated as metadata in the processed files). NOTE: in case a record has more than one mapping, add a hyphen and the number to the end of each file name; `-1`, `-2`, etc.
- If you wish to process a MDE (Digital Elevation Model) geotiff file, enter the suffix `_mde` after the audiovisual registration number, leaving a structure analogous to `12345678_mde.tif`.
- If you reprocess an existing orthomosaic (or add new elements), and want to preserve the same MapId, you must enter the file name obtained from the original processing as the file name (and if it is a mde, add the suffix `_mde` at the end), remaining similar to `12345678_MapId-123445_mde.tif`.
- Run `python process.py` to start the conversion. The processed files will be created in the `output` folder.

## Configuration

- If necessary, modify the `params.py` file according to export formats, metadata and folders.