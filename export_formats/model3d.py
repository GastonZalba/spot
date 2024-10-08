import subprocess
import trimesh
from pygltflib import GLTF2
import numpy as np

import params

def export_3d_model_glb(self, filepath):
    '''
    Export and compress an .obj model (with texture .jpg and material .mtl) to a 
    single and cloud optimized .glb file. 
    
    The model is rotated to face upwards, and it's material is normalized to mantain an uniform
    lightning value across all possilbe sources.
    
    Sources tested: Pix4d Mapper, Pix4d Matic, Agisoft Metashape.
       
    This model can be loaded in the browser using https://www.npmjs.com/package/@google/model-viewer
    
    NOTE: The model exported is not geolocated.
    '''
    
    print(f'-> Exporting 3d model {filepath}')

    mesh = trimesh.load(filepath, force='mesh')
    tmp_gltf = f'{params.tmp_folder}\\model.gltf'
    angle_in_radians = np.deg2rad(-90)

    rotation_matrix = trimesh.transformations.rotation_matrix(
    angle=angle_in_radians, 
        direction=[1, 0, 0] # Rotar alrededor del eje X
    )
    mesh.apply_transform(rotation_matrix)
    
    # firt, export the model to gltf format to allow be opened by GLTF2 and gltf-pipeline
    mesh.export(tmp_gltf)
    
    gltf = GLTF2().load(tmp_gltf)
    
    # normalize all materials from diferrents sources
    for material in gltf.materials:
        print(material)
        pbr = material.pbrMetallicRoughness
        
        pbr.baseColorFactor = [1.0, 1.0, 1.0, 1.0]  # Blanco
        
        if pbr.metallicFactor is None:
            pbr.metallicFactor = 0.0
        
        if pbr.roughnessFactor is None:
            pbr.roughnessFactor = 1.0
            
    # Configure some base defaults lights
    gltf.extensions = {}
    gltf.extensions["KHR_lights_punctual"] = {
        "lights": [
            {
                "type": "directional", # 'directional', 'point', or 'spot'
                "intensity": 9.0,
                "color": [1.0, 1.0, 1.0],
                "name": "DirectionalLight"
            },
            {
                "type": "point", # 'directional', 'point', or 'spot'
                "intensity": 35.0,
                "color": [0.7, 0.7, 1.0],
                "name": "PointLight"
            }
        ]
    }

    ## add light to the scene
    gltf.nodes.append({
        "extensions": {
            "KHR_lights_punctual": {
                "light": 0  # El índice de la luz en la lista de luces
            }
        }
    })

    gltf.scenes[0].nodes.append(len(gltf.nodes) - 1)
    
    # Save file with light configured
    gltf.save(tmp_gltf)

    output = f'{self.outputFolder}\\{self.outputFilename}.glb'
    
    # add compression to the model and export it in gbl format using the javascript library "gltf-pipeline"
    args = [
        'gltf-pipeline',
        f'-i {tmp_gltf}',
        f'-o {output}',
        '--stats',
        '--draco.compressMeshes',
        '--draco.compressionLevel 5',
        '--draco.quantizeColorBits 4',
        '--draco.quantizePositionBits 0',
    ]
    
    subprocess.run(" ".join(args), shell=True, check=True)