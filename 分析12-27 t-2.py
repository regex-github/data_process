# 2023年1月24日21:54:15
# ISL分析  12-27 reactive_shell_2_12_27_1min 轨道面内
# 2023年1月25日 优化altitude筛选代码 提高计算效率


import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.geometry import LineString

# 读取邻接关系
adj_list_byTime = np.load("/root/llx/data/2023/topo/reactive_shell_2_12_27_1min.npy", allow_pickle=True)
# 卫星
tle_dict = np.load("/root/llx/data/2023/tle/tle_2022_12_27_1min.npy", allow_pickle=True).item()
# 遮挡物高度列表 需要使用altitude进行粗略筛选
earth_radius = 6371
trash_altitude_path = "/root/oyl/003/data/trash_altitude/2022-12-27/trash_altitude.csv"
trash_altitude_pd = pd.read_csv(trash_altitude_path, index_col=0)
trash_altitude_pd['altitude'] = trash_altitude_pd['altitude'] - earth_radius
# 遮挡物半径信息
trash_shape_path = "/root/oyl/003/data/trash_shape/trash_shape_radius.csv"
trash_radius_pd = pd.read_csv(trash_shape_path, index_col=0)
# 遮挡物位置信息
trash_object_path = "/root/oyl/003/data/trash_object/2022-12-27/"

# 筛选遮挡物高度在区间内的遮挡物id
trash_filtered_pd = trash_altitude_pd.loc[
    (trash_altitude_pd['altitude'] >= 540-20) & (trash_altitude_pd['altitude'] <= 570+20), 'satno'
]

analyse_list = []
time_range = 60
# 每一个时刻
for i in range(2, time_range):
    # 这个时刻的全部邻居关系
    print("time id:", i)
    adj = adj_list_byTime[i]
    for sat_id_a in adj.keys():
        #         邻居关系里的每一个主卫星id
        #         print(tle_dict[sat_id_a]["lat_long"][i])
        for isl_type in adj[sat_id_a]:
            # 每一个isl类型 对应的从属卫星id
            sat_id_b = adj[sat_id_a][isl_type]
            if sat_id_b == 0:
                # 邻居是他自己 跳过
                continue
            # 2023年1月25日 不要下面的每次都筛选，将altitude筛选统一放到for外面
            # 两卫星的此时高度 对高度进行排序 并延拓筛选遮挡物区间左右各 20 km
            # altitude_a = tle_dict[sat_id_a]["lat_long"][i][-1]
            # altitude_b = tle_dict[sat_id_b]["lat_long"][i][-1]
            # if altitude_a < altitude_b:
            #     pass
            # else:
            #     temp = altitude_a
            #     altitude_a = altitude_b
            #     altitude_b = temp
            # altitude_a = altitude_a - 20
            # altitude_b = altitude_b + 20
            print(sat_id_a, sat_id_b, isl_type, "log")
            for trash_id in trash_filtered_pd.values:
                # 排除建立ISL卫星自身
                if trash_id == sat_id_a or trash_id == sat_id_b:
                    continue
                # 构造ISL空间线段
                line_ab = LineString([tle_dict[sat_id_a]["pos"][i], tle_dict[sat_id_b]["pos"][i]])
                # 读取遮挡物的传播星历pos
                trash_file_name = trash_object_path + "Propagation_" + str(trash_id) + ".csv"
                try:
                    trash_pos_pd = pd.read_csv(trash_file_name, index_col=0)
                except Exception:
                    raise Exception
                # 构造遮挡物空间点
                point_t = Point([trash_pos_pd.loc[i, 'x'], trash_pos_pd.loc[i, 'y'], trash_pos_pd.loc[i, 'z']])
                # 把单位换算成米
                distance = point_t.distance(line_ab) * 1000

                if not trash_radius_pd.loc[trash_radius_pd['satno'] == trash_id].empty:
                    # 如果disco web有这个数据，即非空 使用disco数据
                    t_radius = trash_radius_pd.loc[trash_radius_pd['satno'] == trash_id, 'radius'].iloc[0]
                else:
                    t_radius = 0.05

                if distance < t_radius:
                    analyse_list.append([
                        sat_id_a, sat_id_b, isl_type, trash_id, distance, t_radius
                    ])
                    print(sat_id_a, sat_id_b, isl_type, trash_id, distance, t_radius, "attention")
                else:
                    pass

                # print(sat_id_a, sat_id_b, isl_type, trash_id, distance, t_radius)
                

analyse_pd = pd.DataFrame(analyse_list)
analyse_pd.columns = ["sat_id_a", "sat_id_b", "isl_type", "trash_id", "distance", "t_radius"]
analyse_pd.to_csv("analyse_12-27.csv")