import numpy as np
import matplotlib.pyplot as plt
import os
from readSensorDataTcSol import readSensorDataTcSol
from readgnsstopic import readgnsstopic

def compare_tc_lc_mul():
    """
    比较多个TC和LC数据
    """
    lcpath = 'D:/dockers/test/20250429_huizhan/tcmsf_d022fcd77_v2/tcmsf_sol.csv'
    tcpath1 = lcpath  # 'D:/dockers/tcmsf/unelg/tcmsf_sol.csv'
    tcpath2 = lcpath  # 'D:/dockers/tcmsf/pre/tcmsf_sol.csv'
    tcpath3 = 'D:/dockers/huiguan_res/TCMSF_interface_0909_b0506d0_v3/20250429_huizhan/tcmsf_lm/tcmsf_sol.csv'
    tcpath4 = 'D:/dockers/huiguan_res/TCMSF_interface_0909_b0506d0_v3/20250429_huizhan/tcmsf/tcmsf_sol.csv'

    picrow = 2

    lcs = readSensorDataTcSol(lcpath, 0)
    tcs1 = readSensorDataTcSol(tcpath1, 0)
    tcs2 = readSensorDataTcSol(tcpath2, 0)
    tcs3 = readSensorDataTcSol(tcpath3, 0)
    tcs4 = readSensorDataTcSol(tcpath4, 0)
    gnsstopic = readgnsstopic('D:/dockers/tcmsf/gnss.csv', list(range(4, 14)))  # 4:13 对应Python中的range(4, 14)

    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    pos0 = tcs1[0, 7:9]  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    lcs[:, 7:9] = (lcs[:, 7:9] - pos0) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs1[:, 7:9] = (tcs1[:, 7:9] - pos0) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs2[:, 7:9] = (tcs2[:, 7:9] - pos0) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs3[:, 7:9] = (tcs3[:, 7:9] - pos0) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs4[:, 7:9] = (tcs4[:, 7:9] - pos0) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)

    t0 = tcs1[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos', 'gyb', 'acb', 'kod']
    xranges = [100, 200]
    plotgnssstat = 0
    plotlaststat = 0
    plotstat = 1
    
    for si in range(1, 4):  # 1:3 对应Python中的range(1, 4)
        plt.figure(si)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]
        
        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + 1 + i  # pi=3*(si-1)+1+i
            pi_idx = pi - 1  # 转换为Python的0基索引
            
            # 单个子图
            plt.subplot(1, 3, i)
            plt.plot(lcs[:, 0] - t0, lcs[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
            # plt.plot(tcs1[:, 0] - t0, tcs1[:, pi_idx], "-o", linewidth=1, color='blue', markersize=2)
            plt.plot(tcs2[:, 0] - t0, tcs2[:, pi_idx], "-o", linewidth=1, color='black', markersize=2)
            plt.plot(tcs3[:, 0] - t0, tcs3[:, pi_idx], "-o", linewidth=1, color='magenta', markersize=2)
            plt.plot(tcs4[:, 0] - t0, tcs4[:, pi_idx], "-o", linewidth=1, color='green', markersize=2)
            
            if plotgnssstat:
                plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
            
            plt.xlim(xranges)
            plt.grid(True)
            plt.legend(['lc', 'tc_c1', 'tc_c2', 'tc_c3'])
    
    plt.show()

# 如果直接运行此脚本，则执行compare_tc_lc_mul函数
if __name__ == "__main__":
    compare_tc_lc_mul()
