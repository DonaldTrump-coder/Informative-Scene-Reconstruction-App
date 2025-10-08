import os
import pycolmap
from internal.Colmap.folder import temp_images

class constructor:
    def __init__(self, database):
        self.db = database # path to DataBase
        with open(self.db, 'w'):
            pass

    def add_images(self, image_list):
        if not image_list:
            raise ValueError("image_list 为空")
        
        dir = temp_images(os.path.dirname(self.db), image_list)
        # 提取文件夹和文件名
        pycolmap.import_images(
            database_path=self.db,
            image_path = dir
        )
        self.image_path = dir

    def sfm(self):
        os.makedirs(os.path.join(os.path.dirname(self.db),"output","sparse"))
        sift_options = pycolmap.SiftExtractionOptions(
            use_gpu=False,         # 是否使用 GPU
            num_threads=4          # 提取特征线程数
        )
        pycolmap.extract_features(database_path=self.db,
                                  image_path=self.image_path,
                                  sift_options=sift_options)
        pycolmap.match_sequential(self.db)
        reconstruction = pycolmap.incremental_mapping(
        database_path=self.db,
        image_path=self.image_path,
        output_path=os.path.join(os.path.dirname(self.db),"output","sparse")
    )
        
if __name__ == "__main__":
    cons = constructor("C:\\Users\\10527\\Desktop\\project.db")
    cons.add_images(["D:\\TanksandTemples\\Ballroom\\images\\00003.jpg"])