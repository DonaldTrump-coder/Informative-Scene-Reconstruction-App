import os
import pycolmap
from desktop.Colmap.folder import temp_images

class constructor:
    def __init__(self, database):
        self.db = database # path to DataBase
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

    def sfm(self):
        os.makedirs(os.path.join(os.path.dirname(self.db), "sparse"))
        sift_options = pycolmap.FeatureExtractionOptions(
            use_gpu=False,         # 是否使用 GPU
            num_threads=4          # 提取特征线程数
        )
        pycolmap.extract_features(database_path=self.db,
                                  image_path=self.image_path,
                                  reader_options=self.reader_options,
                                  extraction_options=sift_options
                                  )
        pycolmap.match_sequential(self.db)
        reconstruction = pycolmap.incremental_mapping(
        database_path=self.db,
        image_path=self.image_path,
        output_path=os.path.join(os.path.dirname(self.db), "sparse")
        )
        
    def sfm_test(self):
        os.makedirs(os.path.join(os.path.dirname(self.db), "ourput", "sparse"), exist_ok=True)
        sift_options = pycolmap.SiftExtractionOptions(
            num_threads=4          # 提取特征线程数
        )
        pycolmap.extract_features(database_path=self.db,
                                  image_path=self.image_path,
                                  sift_options=sift_options,
                                  camera_model = 'PINHOLE'
                                  )
        pycolmap.match_sequential(self.db)
        reconstruction = pycolmap.incremental_mapping(
        database_path=self.db,
        image_path=self.image_path,
        output_path=os.path.join(os.path.dirname(self.db), "ourput", "sparse")
        )
        
if __name__ == "__main__":
    cons = constructor("D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\project.db")
    cons.add_image_folder("D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\images")
    cons.sfm_test()