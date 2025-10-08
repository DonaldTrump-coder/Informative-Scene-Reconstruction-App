import os
import shutil

def temp_images(temp_folder, image_list:list[str]):
    dir = os.path.join(temp_folder, "temp", "images") # the directory of temp images
    os.makedirs(dir, exist_ok=True)
    for index, image in enumerate(image_list):
        ext = os.path.splitext(image)[1]
        dest = os.path.join(dir, f'{index}{ext}')
        shutil.copy(image, dest)
    return dir