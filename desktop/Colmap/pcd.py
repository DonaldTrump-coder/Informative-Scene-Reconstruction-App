from desktop.Colmap.read_write_model import read_cameras_binary, read_images_binary, read_points3D_binary
import numpy as np
import pyvista as pv

class PCD:
    def __init__(self, camera_file, image_file, point_file):
        self.camera_file = camera_file
        self.image_file = image_file
        self.point_file = point_file
        self.points3D = read_points3D_binary(self.point_file)
        self.points_xyz = np.array([point.xyz for point in self.points3D.values()])
        self.points_rgb = np.array([point.rgb for point in self.points3D.values()])
        self.camera_pos = None
        self.plotter = None
        self.plotter_set = False
        
    def get_extrinsics_init(self):
        self.center = self.points_xyz.mean(axis=0)
        max_range = np.linalg.norm(self.points_xyz.max(axis=0) - self.points_xyz.min(axis=0)) * 0.2
        eye = self.center + np.array([0, 0, max_range])
        lookat = self.center
        up = np.array([0,1,0])
        
        forward = (lookat - eye)
        forward /= np.linalg.norm(forward)
        right = np.cross(up, forward)
        right /= np.linalg.norm(right)
        true_up = np.cross(forward, right)
        
        R = np.stack([right, true_up, forward], axis=0)
        t = -R @ eye
        return R, t
        
    def set_camera(self, R, T, H, W, K):
        if not self.plotter_set:
            self.plotter = pv.Plotter(off_screen=True, window_size=(W, H))
            self.plotter_set = True
            
            # set points
            self.plotter.add_points(self.points_xyz, scalars=self.points_rgb, rgb=True, point_size=2)
            
        fy = K[1,1]
        cx = K[0,2]
        cy = K[1,2]
        wcx = -2*(cx - float(W)/2) / W
        wcy =  2*(cy - float(H)/2) / H
        fov_y = 2 * np.arctan(H / (2*fy))
        self.plotter.camera.view_angle = np.degrees(fov_y)
        self.plotter.camera.SetWindowCenter(wcx, wcy)
        C = -np.dot(R.T, T).reshape(3) # camera position in world coordinates
        forward = R.T @ np.array([0,0,1])
        focal_point = C + forward
        up = R.T @ np.array([0,1,0])
        self.plotter.camera_position = (C, focal_point, up)
        """Xc = (R @ self.points_xyz.T + T).T
        mask = Xc[:, 2] > 1e-6
        Xc = Xc[mask]
        colors = self.points_rgb[mask]
        uv = (K @ Xc.T).T
        uv[:, 0] /= uv[:, 2]
        uv[:, 1] /= uv[:, 2]
        u = np.round(uv[:, 0]).astype(int)
        v = np.round(uv[:, 1]).astype(int)
        z = Xc[:, 2]"""
        
    def render(self):
        self.plotter.render()
        return self.plotter.screenshot()
    
    def close(self):
        self.plotter.close()
        
if __name__ == '__main__':
    pcd = PCD("D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\output\\sparse\\0\\cameras.bin", "D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\output\\sparse\\0\\images.bin", "D:\\Projects\\Informative-Scene-Reconstruction-App\\data\\playroom\\output\\sparse\\0\\points3D.bin")