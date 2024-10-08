import os
from osgeo import gdal

import params
import helpers as h

def maybe_generate_VRT():
    '''
    Create a VRT file from each folder that cointains tif images (tiles)
    '''
    cont = os.listdir(params.input_folder)
    for i in cont:
        finalpath = params.input_folder + os.sep + i
        for path, dirs, files in os.walk(finalpath):
            pathList = []
            filepath = params.tmp_folder + '\list.txt'
            with open(filepath, "w") as l:
                for file in files:
                    if(h.get_extension(file) in params.extensions):
                        tile_file_path = path + os.sep + file
                        l.write(tile_file_path + '\n')

            with open(filepath, 'r') as f:
                for line in f:
                    pathList.append(line.split('\n')[0])

            if (pathList):
                output = finalpath + '.vrt'
                vrt_options = gdal.BuildVRTOptions(allowProjectionDifference=True)
                gdal.BuildVRT(output, pathList, options=vrt_options)
