import os
import shutil

def temp_images(temp_folder, image_list:list[str]):
    dir = os.path.join(temp_folder, "temp", "images") # the directory of temp images
    os.makedirs(dir, exist_ok=True)
    keep = set()
    for index, image in enumerate(image_list):
        ext = os.path.splitext(image)[1]
        keep.add(f'{index}{ext}')
        
    for name in os.listdir(dir):
        if name not in keep:
            path = os.path.join(dir, name)
            if os.path.isfile(path):
                os.remove(path)
    
    for index, image in enumerate(image_list):
        ext = os.path.splitext(image)[1]
        dest = os.path.join(dir, f'{index}{ext}')
        src = os.path.normcase(os.path.abspath(image))
        dst = os.path.normcase(os.path.abspath(dest))
        if src != dst and not os.path.exists(dest):
            shutil.copy2(image, dest)
    return dir

def temp_sparse(temp_folder, sparse_folder):
    dir = os.path.join(temp_folder, "sparse") # the directory of temp sparse
    os.makedirs(dir, exist_ok=True)
    
    for name in os.listdir(sparse_folder):
        src_path = os.path.join(sparse_folder, name)
        dst_path = os.path.join(dir, name)
        if os.path.exists(dst_path):
            if os.path.isdir(dst_path):
                shutil.rmtree(dst_path)
            else:
                os.remove(dst_path)
            
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)