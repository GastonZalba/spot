import subprocess
import trimesh
from pygltflib import GLTF2
import numpy as np

import params

def export3DModelGLB(self, filepath):
    mesh = trimesh.load(filepath, force='mesh')
    tmp_gltf = f'{params.tmp_folder}\\model.gltf'
    
    # rotate the modal to be over the floor
    #rotation_matrix = trimesh.transformations.rotation_matrix(np.radians(-90), [1, 0, 0])
    #mesh.apply_transform(rotation_matrix)
    mesh.export(tmp_gltf)
    
    # Cargar el archivo GLTF generado
    gltf = GLTF2().load(tmp_gltf)
    
    # Crear la estructura de la extensión KHR_lights_punctual
    gltf.extensions = gltf.extensions or {}
    gltf.extensions["KHR_lights_punctual"] = {
        "lights": [
            {
                "type": "directional", # Tipo de luz: 'directional', 'point', o 'spot'
                "intensity": 15.0,  # Intensidad de la luz
                "color": [1.0, 1.0, 1.0],  # Color de la luz (RGB)
                "name": "DirectionalLight"
            },
            {
                "type": "point", # Tipo de luz: 'directional', 'point', o 'spot'
                "intensity": 50.0,  # Intensidad de la luz
                "color": [0.8, 0.8, 1.0],  # Color de la luz (RGB)
                "name": "PointLight"
            }
        ]
    }

    # Crear un nuevo nodo para contener la luz
    light_node = {
        "extensions": {
            "KHR_lights_punctual": {
                "light": 0  # El índice de la luz en la lista de luces
            }
        }
    }

    # Añadir el nuevo nodo a la lista de nodos de la escena
    gltf.nodes.append(light_node)

    # Añadir el nodo a la escena
    gltf.scenes[0].nodes.append(len(gltf.nodes) - 1)
    # Guardar el archivo GLTF modificado con la luz
    gltf.save(tmp_gltf)

    output = f'{self.outputFolder}\\{self.outputFilename}.glb'
    subprocess.run(f'gltf-pipeline -i {tmp_gltf} -o {output} --draco.compressMeshes', shell=True, check=True)