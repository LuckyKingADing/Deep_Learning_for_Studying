import numpy as np
import matplotlib.pyplot as plt
from readmsf_debug_state import readmsf_debug_state
from readSensorDataTcXkPk import readSensorDataTcXkPk
from readgnsstopic import readgnsstopic

def compare_2msfstate():
    """
    比较两个MSF状态
    """
    lcpath = 'D:/dockers/tcmsf/tmp_remote/msf_debug_state.csv'
    lcpath = 'D:/dockers/tcmsf/lastv/tcmsf_sol.csv'
    tcpath = 'D:/dockers/tcmsf/tmp/msf_debug_state.csv'
    dt = 1752798740.9025 - 433961.2
    # tcpath='D:/dockers/test1/d9_053266_20250702153315/tcmsf_7c846ff/tcmsf_sol.csv';
    # tcpath='D:/dockers/tcmsf/修改了零速期间方差传递old/tcmsf_sol.csv';
    # tcpath='D:/dockers/tcmsf/R0009/tcmsf_sol.csv';
    lcpkpath = 'D:/dockers/tcmsf/tcmsf_pk.csv'
    # lcpkpath='D:/dockers/tcmsf/lastv/tcmsf_pk.csv';
    tcpkpath = 'D:/dockers/tcmsf/tcmsf_pk.csv'
    # tcpkpath='D:/dockers/test1/d9_053266_20250702153315/tcmsf_7c846ff/tcmsf_pk.csv';

    lcxkpath = 'D:/dockers/test_e2e/2025-07-18_08-32-20/lc/tcmsf_xk.csv'
    tcxkpath = 'D:/dockers/tcmsf/tcmsf_xk.csv'
    plotxk = 0
    picrow = 2
    if plotxk == 1:
        picrow = 3

    gnsstopic = readgnsstopic('D:/dockers/test2/cornercase_hc25_6196_20250417/tcmsf_7c846ff/gnss.csv', [4, 5, 6, 7, 8, 9, 10, 11, 12, 13])

    lcs = readmsf_debug_state(lcpath, dt)
    tcs = readmsf_debug_state(tcpath, dt)
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
    xranges = [84, 86]
    xranges = [116, 118]
    xranges = [105, 120]
    xranges = [77.6, 85]
    xranges = [480, 492.1]
    xranges = [319.7, 330]
    xranges = [319, 330]
    xranges = [319, 322.1]
    xranges = [319, 350]
    xranges = [77.6, 80.6]
    xranges = [167.50, 170]
    xranges = [171.3, 171.5]
    xranges = [96.7, 97]
    xranges = [3450, 3650]
    xranges = [0, 1200]
    plotgnssstat = 0
    plotlaststat = 0
    plotstat = 0
    
    for si in range(1, 4):  # 1:3 对应Python中的range(1, 4)
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
            
            if plotgnssstat:
                plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
            
            if plotlaststat:
                plt.plot(lcs[:, 0] - t0, lcs[:, -1] / 10, "-o", linewidth=1, color='black', markersize=2)
            
            if plotstat:
                plt.plot(tcs[:, 0] - t0, tcs[:, -1] / 10, "-o", linewidth=1, color='magenta', markersize=2)
            
            if plotxk == 1:
                plt.subplot(picrow, 3, i + 6)
                plt.plot(lcx[:, 0] - t0, lcx[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
                plt.plot(tcx[:, 0] - t0, tcx[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1)
                plt.xlim(xranges)
            
            plt.legend(['lc', 'tc'])
            plt.grid(True)
    
    plt.show()

# 如果直接运行此脚本，则执行compare_2msfstate函数
if __name__ == "__main__":
    compare_2msfstate()
