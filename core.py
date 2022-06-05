'''Core library functions, including GEE extraction, image saving, conversion 
functions, etc.
'''


import time
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
import ee

from util import trim_slash_from_path


def extract_geotiff_from_gee(dataset_name: str, 
                             bands: list, 
                             start_date: str, 
                             end_date: str,
                             output_dir: str, 
                             desc: str, 
                             mpp: int, 
                             xmin: float, 
                             ymin: float, 
                             xmax: float, 
                             ymax: float
                            ) -> None: 
    # initializes the GEE instance
    ee.Initialize()

    geometry = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])

    dataset = ee.ImageCollection(dataset_name) \
            .filter(ee.Filter.date(start_date, end_date));

    # select bands and geometry of final image                  
    image = dataset.select(bands) \
                .mean();

    # export 
    output_dir = output_dir
    fname_root = desc
    task = ee.batch.Export.image.toDrive(**{
        'image': image, 
        'description': fname_root,
        'folder': output_dir,
        # smaller scale means better resolution
        'scale': mpp,  
        'region': geometry,
    })
    task.start()

    print('Working on export task (id: {}).'.format(task.id))
    while task.active(): 
        time.sleep(1)
    print(f'Export complete. File available in Drive at /{output_dir}/{fname_root}.tif')


# TODO: allow for file paths to Google Drive files and local files
def arr_from_geotiff(fname: str, 
                     r_channel: int = 1, 
                     g_channel: int = 2,
                     b_channel: int = 3,
                    ) -> Image: 
    """Converts a geotiff to an np.ndarray.
    
    Args: 
        fname (str): Filepath for the 
        r_channel (int): Channel of image data to assign to Red (1-indexed). Defaults to 1.
        g_channel (int): Channel of image data to assign to Green (1-indexed). Defaults to 2.
        b_channel (int): Channel of image data to assign to Blue (1-indexed). Defaults to 3.
    
    Returns a PIL.Image in rgb format.
    """

    # Read raster bands directly to Numpy arrays.
    if not fname.endswith('.tif'): 
        fname += '.tif'

    with rasterio.open(fname) as src:
        r = src.read(r_channel)
        g = src.read(g_channel)
        b = src.read(b_channel)

    img_arr = np.zeros((r.shape[0], r.shape[1], 3), dtype=np.uint8)
    img_arr[:,:,0] = r
    img_arr[:,:,1] = g
    img_arr[:,:,2] = b

    return Image.fromarray(img_arr)


# TODO: allow output to be Google Drive paths 
def save_img(img_arr: np.ndarray,
             name: str,
             format: str = 'png', 
             output_dir: str = "out/", 
            ) -> None:
    """Saves an image np.ndarray in the specified format. 

    Args: 
        img_arr (np.ndarray): 
        name (str): Name of the image.  
        format (:obj: `str`, Optional): File type of output. Defaults to 'png'. 
        output_dir (:obj: `str`, Optional): Output directory. Defaults to 'out/'. 
            If the directory does not exist, it is created.  
    """

    output_dir = trim_slash_from_path(output_dir)
    fname = f"{output_dir}/{name}.{format}"

    # make sure output dir exists (create it if it doesn't)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    img_arr.save(fname)

