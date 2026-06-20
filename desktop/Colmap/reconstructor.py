import os
import pycolmap
from desktop.Colmap.folder import temp_images
import shutil

class constructor:
    def __init__(self, database):
        self.db = database # path to DataBase
        self.running = True
        with open(self.db, 'w'):
            pass

    def add_images(self, image_list):
        if not image_list:
            raise ValueError("image_list 为空")
        
        dir = temp_images(os.path.dirname(self.db), image_list)
        
        self.reader_options = pycolmap.ImageReaderOptions(
            camera_model = "PINHOLE"
        )
        
        pycolmap.import_images(
            database_path=self.db,
            image_path = dir,
            options = self.reader_options
        )
        self.image_path = dir
    
    def add_image_folder(self, folder):
        self.image_path = folder
        self.reader_options = pycolmap.ImageReaderOptions(
            camera_model = "PINHOLE"
        )
        pycolmap.import_images(
            database_path=self.db,
            image_path = self.image_path,
            options = self.reader_options
        )

    def sfm(self, progress_callback=None):
        total_steps = 4
        step = 0
        
        if self.running:
            sparse_path = os.path.join(os.path.dirname(self.db), "output", "sparse")
            if os.path.exists(sparse_path):
                shutil.rmtree(sparse_path)
            os.makedirs(sparse_path)
            step += 1
        else:
            return
        if progress_callback:
            progress_callback(step, total_steps)
        
        if self.running:
            sift_options = pycolmap.FeatureExtractionOptions(
                use_gpu=False,
                num_threads=4
            )
            pycolmap.extract_features(database_path=self.db,
                                  image_path=self.image_path,
                                  reader_options=self.reader_options,
                                  extraction_options=sift_options
                                  )
            step += 1
        else:
            return
        if progress_callback:
            progress_callback(step, total_steps)
            
        if self.running:
            pycolmap.match_sequential(self.db)
            step += 1
        else:
            return
        if progress_callback:
            progress_callback(step, total_steps)
            
        if self.running:
            pycolmap.incremental_mapping(
            database_path=self.db,
            image_path=self.image_path,
            output_path=os.path.join(os.path.dirname(self.db), "output", "sparse")
            )
            step += 1
        else:
            return
        if progress_callback:
            progress_callback(step, total_steps)
        
if __name__ == "__main__":
    cons = constructor("D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\project.db")
    cons.add_image_folder("D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\images")
    #cons.sfm_test()