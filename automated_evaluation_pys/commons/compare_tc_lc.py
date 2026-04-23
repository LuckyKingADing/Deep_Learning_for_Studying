import numpy as np
import matplotlib.pyplot as plt
import os
from readSensorDataTcSol import readSensorDataTcSol
from readSensorDataTcXkPk import readSensorDataTcXkPk
from readgnsstopic import readgnsstopic

def compare_tc_lc():
    """
    比较TC和LC数据
    """
    # 设置路径参数
    basefold = 'D:/dockers/huiguan_res/956c7de5/'
    dataset = '20251205_demo'
    lcver = 'tcmsf_bfopt'
    tcver = 'tcmsf'

    lcpath = os.path.join(basefold, dataset, lcver, 'tcmsf_sol.csv')
    lcpkpath = os.path.join(basefold, dataset, lcver, 'tcmsf_pk.csv')
    lcxkpath = os.path.join(basefold, dataset, tcver, 'tcmsf_sol.csv')

    tcpath = os.path.join(basefold, dataset, tcver, 'tcmsf_sol.csv')
    tcpkpath = os.path.join(basefold, dataset, tcver, 'tcmsf_pk.csv')
    tcxkpath = os.path.join(basefold, dataset, tcver, 'tcmsf_pk.csv')

    plotxk = 0
    picrow = 2
    if plotxk == 1:
        picrow = 3

    plotgnssstat = 0
    if plotgnssstat:
        gnsstopic = readgnsstopic('D:/dockers/tcmsf/gnss.csv', list(range(4, 14)))  # 4:13 对应Python中的range(4, 14)

    lcs = readSensorDataTcSol(lcpath, 0)
    tcs = readSensorDataTcSol(tcpath, 0)
    lcp = readSensorDataTcXkPk(lcpkpath, 0)
    tcp = readSensorDataTcXkPk(tcpkpath, 0)
    if plotxk == 1:
        lcx = readSensorDataTcXkPk(lcxkpath, 0)
        tcx = readSensorDataTcXkPk(tcxkpath, 0)

    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    lcs[:, 7:9] = (lcs[:, 7:9] - tcs[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs[:, 7:9] = (tcs[:, 7:9] - tcs[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos', 'gyb', 'acb', 'kod']
    xranges = [0, 2400]
    plotstat = 0
    plotlaststat = 0
    
    for si in range(1, 7):  # 1:6 对应Python中的range(1, 7)
        plt.figure(si)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]
        
        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + 1 + i  # pi=3*(si-1)+1+i
            pi_idx = pi - 1  # 转换为Python的0基索引
            
            # 第一行子图
            plt.subplot(picrow, 3, i)
            plt.plot(lcs[:, 0] - t0, lcs[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
            plt.plot(tcs[:, 0] - t0, tcs[:, pi_idx], "-o", linewidth=1, color='blue', markersize=2)
            plt.xlim(xranges)
            plt.grid(True)
            
            # 第二行子图
            plt.subplot(picrow, 3, i + 3)
            plt.plot(lcp[:, 0] - t0, lcp[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
            plt.plot(tcp[:, 0] - t0, tcp[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1)
            plt.xlim(xranges)
            plt.grid(True)
            
            szcl = tcs.shape[1]  # 获取列数
            
            if plotgnssstat:
                plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
            
            if plotlaststat:
                plt.plot(lcs[:, 0] - t0, lcs[:, szcl-2] / 10, "-o", linewidth=1, color='black', markersize=2)  # szcl-1变为szcl-2（Python索引）
            
            if plotstat:
                plt.plot(tcs[:, 0] - t0, tcs[:, szcl-3] / 10, "-o", linewidth=1, color='magenta', markersize=2)  # szcl-2变为szcl-3（Python索引）
            
            if plotxk == 1:
                plt.subplot(picrow, 3, i + 6)
                plt.plot(lcx[:, 0] - t0, lcx[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
                plt.plot(tcx[:, 0] - t0, tcx[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1)
                plt.xlim(xranges)
            
            plt.legend(['lc', 'tc'])
            plt.grid(True)
    
    plt.show()

# 如果直接运行此脚本，则执行compare_tc_lc函数
if __name__ == "__main__":
    compare_tc_lc()
