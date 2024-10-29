import sys
import os
import shutil
from pathlib import Path
import math
import struct

import params
import helpers as h
import vrt

from export_formats.storageRGB import exportStorageRGB
from export_formats.storageDEM import exportStorageDEM
from export_formats.geoserverDEM import exportGeoserverDEM
from export_formats.geoserverRGB import exportGeoserverRGB
from export_formats.previews import exportStoragePreview
from export_formats.quantities import exportQuantities
from export_formats.outlines import exportOutline
from export_formats.model3d import export_3d_model_glb

from version import __version__

try:
    from osgeo import gdal
except:
    sys.exit('ERROR: osgeo module was not found')


class main:
    '''
    Some helpful docs:
    https://pcjericks.github.io/py-gdalogr-cookbook/
    https://docs.geoserver.geo-solutions.it/edu/en/raster_data/advanced_gdal/example5.html
    https://gdal.org/tutorials/raster_api_tut.html
    https://gdal.org/python/osgeo.gdal-module.html
    https://gdal.org/api/python.html

    '''

    def __init__(self):
        
        print('''
███████ ██████   ██████  ████████ 
██      ██   ██ ██    ██    ██    
███████ ██████  ██    ██    ██    
     ██ ██      ██    ██    ██    
███████ ██       ██████     ██                                
''')
        
        print(f'SPOT Version: {__version__}')
        
        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print(f'GDAL Version: {version_num}')

        print('OPERATION STARTED')

        # Allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')

        self.check_directories()
        self.process_files()
        self.clean_temp_folder()

        print('OPERATION FINISHED')

    def check_directories(self):
        '''
        Create output folders and remove older files
        '''

        if params.clean_output_folder:
            if os.path.exists(params.output_folder):
                print('-> Removing older files')
                shutil.rmtree(Path(params.output_folder))

        print('-> Creating folders')

        h.createFolder(params.tmp_folder)

        h.createFolder(params.output_folder_database)

        h.createFolder(params.output_folder_database_jsondata)

        h.createFolder(params.output_folder_database_mdevalues)

        h.createFolder(params.output_folder_database_outlines)

        h.createFolder(params.output_folder_storage)

        # geoserver folders
        h.createFolder(params.geoserverRGB['output_folder'])
        h.createFolder(params.geoserverDEM['output_folder'])
        h.createFolder(params.geoserverDEMRGB['output_folder'])

    def process_files(self):

        if(os.listdir(params.input_folder)):
            vrt.maybe_generate_VRT()

        processed = {}

        # Find files in the input folder
        for subdir, dirs, files in os.walk(params.input_folder):
            is_subdir = subdir != params.input_folder
            
            if(is_subdir):
                continue

            for file in files:
                filepath = subdir + os.sep + file
                try:
                    filename_has_mapid = params.filename_prefix in file

                    if (h.get_extension(file) in params.raster_extensions):
                        print(f'--> PROCESSING FILE {file} <--')

                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                        # Number of bands
                        bands_count = file_ds.RasterCount
                        self.is_dem = bands_count <= 2

                        last_band = file_ds.GetRasterBand(bands_count)
                        # https://github.com/rasterio/rasterio/issues/100
                        self.has_alpha = (last_band.GetColorInterpretation() == 6)
                        
                        self.no_data_value = last_band.GetNoDataValue()  # take any band

                        # Pix4DMatic injects an erroneous 'nan' value as noData attribute
                        if ((self.no_data_value != None) and (math.isnan(self.no_data_value))):
                            self.no_data_value = 0

                        if (self.is_dem):

                            print(f'-> File {file} is DEM type')

                            # Generating output filename for DME case
                            self.mapId = h.removeExtension(file.split(
                                params.filename_prefix)[1].split(params.dem_suffix)[0]) if filename_has_mapid else h.createMapId()

                            if(not filename_has_mapid):
                                h.checkFileProcessed(
                                    self, True, processed, file)

                            self.registroid = file.split(
                                params.filename_prefix)[0] if filename_has_mapid else h.cleanFilename(h.removeExtension(file.split(params.dem_suffix)[0]))
                        else:

                            print(f'-> File {file} is RGB type')

                            self.mapId = h.removeExtension(
                                file.split(params.filename_prefix)[1]) if filename_has_mapid else h.createMapId()

                            if(not filename_has_mapid):
                                h.checkFileProcessed(
                                    self, False, processed, file)

                            self.registroid = file.split(
                                "_")[0] if filename_has_mapid else h.cleanFilename(h.removeExtension(file))

                        output = f'{self.registroid}{params.filename_prefix}{self.mapId}'

                        # Create parent folder for mapId
                        self.outputFolder = f'{params.output_folder_storage}/{output}'
                        h.createFolder(self.outputFolder)

                        self.outputFilename = output if not self.is_dem else '{}{}'.format(
                            output, params.dem_suffix)

                        print(
                            f'-> Files for {self.outputFilename} will be exported')

                        # File GSD
                        gt = file_ds.GetGeoTransform()
                        self.pixelSizeX = gt[1]
                        self.pixelSizeY = -gt[5]
                        
                        print(f'-> Pixel size: {self.pixelSizeX} x {self.pixelSizeY}')

                        self.pixel_area = self.pixelSizeX * abs(self.pixelSizeY)                        
                        
                        if (self.has_alpha):
                            # generate an ultralight version to calculate the area
                            xsmall_version = gdal.Translate(
                                params.tmp_folder + "\\tmpArea.vrt",
                                file_ds,
                                **{                         
                                    'format': 'GTiff',
                                    'xRes': 20,
                                    'yRes': 20
                                }
                            )
                            
                            xsmall_version_lastBand = xsmall_version.GetRasterBand(bands_count)

                            BandType = gdal.GetDataTypeName(xsmall_version_lastBand.DataType)
                            fmttypes = {'Byte':'B', 'UInt16':'H', 'Int16':'h', 'UInt32':'I', 'Int32':'i', 'Float32':'f', 'Float64':'d'}
                            
                            self.pixel_num = 0

                            for y in range(xsmall_version_lastBand.YSize):
                            
                                scanline = xsmall_version_lastBand.ReadRaster(0, y, xsmall_version_lastBand.XSize, 1, xsmall_version_lastBand.XSize, 1, xsmall_version_lastBand.DataType)
                                values = struct.unpack(fmttypes[BandType] * xsmall_version_lastBand.XSize, scanline)
                            
                                for value in values:
                                    if value > 0:
                                        self.pixel_num = self.pixel_num + 1
                            gt = xsmall_version.GetGeoTransform()
                            pixelSizeX = gt[1]
                            pixelSizeY = -gt[5]
                            pixel_area = pixelSizeX * abs(pixelSizeY)
                            self.area = self.pixel_num * (pixel_area / 10000)
                            xsmall_version = None
                            
                        else:
                            # entire geotiff area (including alpha and nodata)
                            self.pixel_num = file_ds.RasterXSize * file_ds.RasterYSize                        
                            self.area = self.pixel_num * (self.pixel_area / 10000)
                        
                        print('-> Area in ha:', self.area)

                        # file's GSD: get average x and y values
                        self.originalGsd = round(
                            (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

                        # File Projection
                        self.epsg = h.getEPSGCode(file_ds)

                        self.date = h.getDateFromMetadata(file_ds)

                        self.extra_metadata = params.metadata

                        self.extra_metadata.append(
                            'registroId={}'.format(self.registroid))

                        self.extra_metadata.append(
                            'mapId={}'.format(self.mapId))

                        self.exportStorageFiles(file_ds)

                        if ((self.is_dem and (params.geoserverDEM['enabled'] or params.geoserverDEMRGB['enabled'])) or params.geoserverRGB['enabled']):
                            self.exportGeoserverFiles(file_ds, file)

                        # Once we're done, close properly the dataset
                        file_ds = None
          
                    elif (bool(params.model3d['enabled']) and (h.get_extension(file) in params.model3d['extensions'])):
                        self.registroid = file.split(
                                "_")[0] if filename_has_mapid else h.cleanFilename(h.removeExtension(file))
                        self.mapId = h.removeExtension(
                                file.split(params.filename_prefix)[1]) if filename_has_mapid else h.createMapId()

                        output = f'{self.registroid}{params.filename_prefix}{self.mapId}'

                        # Create parent folder for mapId
                        self.outputFolder = f'{params.output_folder_storage}/{output}'
                        h.createFolder(self.outputFolder)

                        self.outputFilename = output
                        
                        export_3d_model_glb(self, filepath)                        
                        
                except RuntimeError as e:
                    print(f'ERROR: Unable to process {filepath}')
                    print(e)
                    sys.exit(1)
                    
    def exportStorageFiles(self, file_ds):
        '''
        Export high and low res files
        '''

        print('EXPORTING STORAGE FILES')

        # creates and low res for some fast operations
        if params.storageDEM['enabled'] or params.previews['enabled'] or params.storageDEM['quantities']:
            compressedGeotiff = h.getLightVersion(self, file_ds)

        if (self.is_dem):
            if params.storageDEM['enabled'] or params.previews['enabled'] or params.storageDEM['quantities']:
                self.colorValues = h.calculateDEMColorValues(
                    self, compressedGeotiff)
            
            if params.storageDEM['enabled']:
                exportStorageDEM(self, file_ds)

            if params.storageDEM['quantities']:
                exportQuantities(self)

        else:
            if (params.outlines['enabled']):
                exportOutline(self, compressedGeotiff)

            if params.storageRGB['enabled']:
                exportStorageRGB(self, file_ds)

        if (params.previews['enabled']):
            exportStoragePreview(self, compressedGeotiff)

        compressedGeotiff = None

    def exportGeoserverFiles(self, file_ds, file):

        print('EXPORTING GEOSERVER FILES')

        if (self.is_dem):
            if (params.geoserverDEM['enabled'] or params.geoserverDEMRGB['enabled']):
                exportGeoserverDEM(self, file_ds, file)
        else:
            if (params.geoserverRGB['enabled']):
                exportGeoserverRGB(self, file_ds)

    def clean_temp_folder(self):
        if os.path.exists(params.tmp_folder):
            print('-> Removing temp folder')
            shutil.rmtree(params.tmp_folder)


if __name__ == "__main__":
    main()
