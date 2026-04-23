import numpy as np
import matplotlib.pyplot as plt
import os
from readSensorData import readSensorData
from load100ccsv import load100ccsv

def compare_tc_lc_ref_100c():
    """
    比较TC和LC数据与参考数据
    """
    lcpath = 'D:/dockers/test/20250429_rapid_road/lc/tcmsf_sol.csv'
    tcpath = 'D:/dockers/tcmsf/tcmsf_sol.csv'
    lcpkpath = 'D:/dockers/test/20250429_rapid_road/lc/tcmsf_pk.csv'
    tcpkpath = 'D:/dockers/tcmsf/tcmsf_pk.csv'

    utctime0 = 1745912239.5336
    gpst0 = 200293.2
    dt = utctime0 - gpst0
    readlen = 100
    gpste = gpst0 + readlen
    reread = 1

    if reread:
        reffile = 'D:/datas/202504/0429/后处理结果/20250429_span_stdref.csv'
        refdata = load100ccsv(reffile, gpst0, gpste)

    lcxkpath = 'D:/dockers/test/20250326_100c/lc/tcmsf_xk.csv'
    tcxkpath = 'D:/dockers/tcmsf/tcmsf_xk.csv'
    plotxk = 0
    picrow = 2
    if plotxk == 1:
        picrow = 3

    lcs = readSensorData(lcpath, dt)
    tcs = readSensorData(tcpath, dt)
    lcp = readSensorData(lcpkpath, dt)
    tcp = readSensorData(tcpkpath, dt)
    if plotxk == 1:
        lcx = readSensorData(lcxkpath, dt)
        tcx = readSensorData(tcxkpath, dt)

    r2m = 6378137
    lcs[:, 7:9] = (lcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    tcs[:, 7:9] = (tcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if reread:
        refdata[:, 7:9] = (refdata[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)

    for i in range(len(lcs)):
        if lcs[i, 3] < 0:  # 第4列 (Python索引3对应MATLAB的4)
            lcs[i, 3] = lcs[i, 3] + 360

    for i in range(len(tcs)):
        if tcs[i, 3] < 0:  # 第4列 (Python索引3对应MATLAB的4)
            tcs[i, 3] = tcs[i, 3] + 360

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos', 'gyb', 'acb', 'kod']
    xranges = [60, readlen]
    
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
            plt.plot(refdata[:, 0] - t0, refdata[:, pi_idx], "-.", linewidth=1, color='black', markersize=2)
            plt.xlim(xranges)
            plt.grid(True)
            
            # 第二行子图
            plt.subplot(picrow, 3, i + 3)
            plt.plot(lcp[:, 0] - t0, lcp[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
            plt.plot(tcp[:, 0] - t0, tcp[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1)
            plt.xlim(xranges)
            plt.grid(True)
            
            if plotxk == 1:
                plt.subplot(picrow, 3, i + 6)
                plt.plot(lcx[:, 0] - t0, lcx[:, pi_idx], "-o", linewidth=1, color='red', markersize=1)
                plt.plot(tcx[:, 0] - t0, tcx[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1)
                plt.xlim(xranges)
            
            plt.legend(['lc', 'tc', 'ref'])
            plt.grid(True)
    
    plt.show()

# 如果直接运行此脚本，则执行compare_tc_lc_ref_100c函数
if __name__ == "__main__":
    compare_tc_lc_ref_100c()
