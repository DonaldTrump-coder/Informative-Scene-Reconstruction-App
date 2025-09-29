import torch
from internal.utils.gaussian_model_loader import GaussianModelLoader
import numpy as np

class CKPT_Parser:
    def __init__(self, filename):
        device = torch.device("cuda")
        ckpt = torch.load(filename, map_location="cpu", weights_only=False)
        self.model = GaussianModelLoader.initialize_model_from_checkpoint(
                                ckpt,
                                device=device)
        self.model.freeze()
        self.model.pre_activate_all_properties()

    def get_model(self):
        return self.model
    #get the model for rendering
    
    def get_points(self):
        # get xyz of 2DGS in the model
        points = self.model.gaussians["means"].detach().cpu().numpy()
        return points

    def get_params(self):
        # get all the parameters of the 2DGS model in a Tensor
        means = self.model.gaussians["means"].detach().cpu().numpy()
        opacities = self.model.gaussians["opacities"].detach().cpu().numpy()
        scales = self.model.gaussians["scales"].detach().cpu().numpy()
        rotations = self.model.gaussians["rotations"].detach().cpu().numpy()
        shs = self.model.gaussians["shs"].detach().cpu().numpy()
        return (means, opacities, scales, rotations, shs)

    def get_boundary(self):
        points = self.get_points()
        min_p = points.min(axis=0)
        max_p = points.max(axis=0)
        return min_p, max_p