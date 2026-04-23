import numpy as np
import matplotlib.pyplot as plt
import os
import utils 
import fileutils

def sel_gnss():
    """
    选择部分gnss部分数据输出
    """
    # 设置参数
    tcver = ''
    tcver = 'topic_parse'
    basefold = '/mnt/d/dockers/rt/rtk_pvt/2026/0319'
    basefoldtc = basefold
    dataset = 'pvt_2026-02-27_13-57-11' 
    dataset = 'pvt_2026-02-27_14-38-39' 
    dataset = '' 
    selt = [392128.60+2460,392128.60+2528]
    
    # rtk和pvt文件路径
    tcpath = os.path.join(basefoldtc, dataset, tcver, 'pvt.csv')

    # 读取数据
    gnssindex = [1,-1,-1,8,5,6,7,2,3,4,10]
    helpindex = [14,15,16,9]
    tcs = fileutils.readfullcsv(tcpath,gnssindex,helpindex)
    
    # 根据时间范围筛选tcs数据（第一列是时间）
    if tcs is not None and len(tcs) > 0:
        tcs_first_col = tcs[:, 0]  # 获取第一列（时间）
        mask = (tcs_first_col >= selt[0]) & (tcs_first_col <= selt[1])
        tcs_selected = tcs[mask]
        
        print(f"原始数据行数: {len(tcs)}")
        print(f"筛选后数据行数: {len(tcs_selected)}")
        print(f"时间范围: {selt[0]} - {selt[1]}")
    else:
        print("错误: tcs数据为空")
        return
    
    # 创建clips文件夹（与原文件同目录）
    tc_dir = os.path.dirname(tcpath)
    clips_dir = os.path.join(tc_dir, 'clips')
    os.makedirs(clips_dir, exist_ok=True)
    
    # 生成新文件名（原文件名 + 时间范围）
    tc_filename = os.path.basename(tcpath)
    tc_name, tc_ext = os.path.splitext(tc_filename)
    time_range_str = f"_selt{selt[0]}-{selt[1]}"
    new_filename = tc_name + time_range_str + tc_ext
    new_filepath = os.path.join(clips_dir, new_filename)
    
    # 将筛选后的数据写入新文件
    np.savetxt(new_filepath, tcs_selected, delimiter=',', fmt='%.6f')
    
    print(f"数据已输出到: {new_filepath}")


if __name__ == "__main__":
    sel_gnss()
