import numpy as np

def get_init_camera(point_min, point_max):
    center = (point_min+point_max)/2
    init_pos = np.array([center[0],center[1],point_max[2]])
    init_pos = init_pos + 0.6*(center-init_pos)

    z_axis= center - init_pos
    z_axis = z_axis / np.linalg.norm(z_axis)
    # 定义一个临时上方向（假设不与Z轴平行）
    temp_up = np.array([0, 1, 0])
    if np.abs(np.dot(z_axis, temp_up)) > 0.99:  # 如果几乎平行
        temp_up = np.array([0, 0, 1])
    # 计算相机X轴
    x_axis = np.cross(temp_up, z_axis)
    x_axis = x_axis / np.linalg.norm(x_axis)

    # 计算相机Y轴
    y_axis = np.cross(z_axis,x_axis) # right-handed
    y_axis = y_axis / np.linalg.norm(y_axis)

    R = np.column_stack((x_axis, y_axis,z_axis)).T
    T = -R @ init_pos
    return R, T