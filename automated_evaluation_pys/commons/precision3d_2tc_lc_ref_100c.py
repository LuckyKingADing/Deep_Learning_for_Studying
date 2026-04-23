#可用
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d
from readSensorDataTcSol import readSensorDataTcSol
from readSensorDataTcXkPk import readSensorDataTcXkPk
from load100ccsv import load100ccsv
import utils

def set_y_lim_to_x_range(xlim_range):
    """
    手动设置y轴范围以适应当前x轴范围内的数据
    """
    ax = plt.gca()
    all_y_data = []
    
    # 获取所有绘制的数据线
    for line in ax.get_lines():
        xdata, ydata = line.get_data()
        if len(xdata) > 0 and len(ydata) > 0:
            # 筛选在 xlim 范围内的数据点
            mask = (xdata >= xlim_range[0]) & (xdata <= xlim_range[1])
            if np.any(mask):
                all_y_data.extend(ydata[mask])
    
    if all_y_data:
        y_min, y_max = min(all_y_data), max(all_y_data)
        # 添加10%的边距
        if y_max != y_min:
            margin = (y_max - y_min) * 0.1
        else:
            margin = 1.0
        plt.ylim(y_min - margin, y_max + margin)

def outpre(outfile, diff_datalc, diff_datatc, tcstart):
    """
    输出精度分析结果
    :param outfile: 输出文件路径
    :param diff_datalc: LC差异数据
    :param diff_datatc: TC差异数据
    :param tcstart: TC起始索引
    """
    with open(outfile, 'w') as fid:
        # ===== LC部分 =====
        fid.write('        pitch   roll     yaw      ve     vn     vu       dlat    dlon    dalt\n')
        fid.write('LC:\n')

        # 按列计算均值和RMS
        mean_lc = np.mean(diff_datalc, axis=0)  # 按列计算均值
        rms_lc = np.sqrt(np.mean(diff_datalc**2, axis=0))  # 按列计算RMS
        max_lc = np.max(diff_datalc, axis=0)  # 按列计算最大值
        min_lc = np.min(diff_datalc, axis=0)  # 按列计算最小值

        # 逐列输出统计量
        fid.write('mean:\t')
        for val in mean_lc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')  # 换行结束当前统计量

        fid.write('rms:\t')
        for val in rms_lc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')  # 额外空行分隔不同部分
        fid.write('max:\t')
        for val in max_lc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')  # 额外空行分隔不同部分
        fid.write('min:\t')
        for val in min_lc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n\n')  # 额外空行分隔不同部分

        # ===== TC部分 =====
        fid.write('TC:\n')

        # 按列计算均值和RMS
        mean_tc = np.mean(diff_datatc[tcstart:, :], axis=0)  # 按列计算均值
        rms_tc = np.sqrt(np.mean(diff_datatc[tcstart:, :]**2, axis=0))  # 按列计算RMS
        max_tc = np.max(diff_datatc[tcstart:, :], axis=0)  # 按列计算最大值
        min_tc = np.min(diff_datatc[tcstart:, :], axis=0)  # 按列计算最小值

        # 逐列输出统计量
        fid.write('mean:\t')
        for val in mean_tc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')

        fid.write('rms:\t')
        for val in rms_tc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')
        fid.write('max:\t')
        for val in max_tc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')
        fid.write('min:\t')
        for val in min_tc:
            fid.write(f'{val:.4f}\t')
        fid.write('\n')

def precision3d_tc_lc_ref_100c_():
    """
    3D精度分析：TC、LC与RTS参考数据对比 TC_61ad095
    """
    tcver = 'TC_ebec52475_dev'
    tcver = 'TC_61ad095'
    tcver = 'TC_8255e68a' #tcmsf_biased 打结版本
    tcver = 'TC_9b3f565'
    tcver = 'TC_9b3f565_v3'
    tcver2 = 'TC_9b3f565' #此版本的性能8组真值数据优于tcmsf_biased 打结版本；但是存在一些较差的点。
    tcver2 = 'TC_9b3f565_v5'
    tcver = 'TC_9b3f565_v3'
    lcver = 'LC_b8d7f45'#e2e分支开发版本 #得用开发版本的结果。开发版本需保证LC的结果与主线版本一致。
    basefold = '/mnt/d/dockers/test/'
    basefoldtc = basefold
    dataset = '20250428_gaojia3'
    dataset = '20250428_gaojia2'
    dataset = '20250428_gaojia1'
    dataset = '20250429_yanhai' #差，不可接受  也许是偶然。多拿数据对比吧。
    dataset = '20250429_huizhan'
    dataset = '20250430_dameisha'#差的地方不可接受
    dataset = '20250429_huishen'
    dataset = '20250429_huanlegu'
    
    reffile = '/mnt/d/dockers/datas/202504/0428/postprocessresult/20250428_span_stdref_02.csv'
    reffile = '/mnt/d/dockers/datas/202504/0430/postprocessresult/20250430_span_stdref_02.csv'
    reffile = '/mnt/d/dockers/datas/202504/0429/postprocessresult/20250429_span_stdref_02.csv'
    refdata = load100ccsv(reffile, 0, 0)

    lcpath = os.path.join(basefold, dataset, lcver, 'tcmsf_sol.csv')
    lcpkpath = os.path.join(basefold, dataset, lcver, 'tcmsf_pk.csv')
    
    plotgnssstat = 0
    if plotgnssstat:
        gnssfile = os.path.join('/mnt/d/dockers/test', dataset, tcver, 'gnss.csv')
        # gnsstopic = readgnsstopic(gnssfile, list(range(1, 14)))  # 1:13 -> range(1, 14)

    tcpath = os.path.join(basefoldtc, dataset, tcver, 'tcmsf_sol.csv')
    tcpkpath = os.path.join(basefoldtc, dataset, tcver, 'tcmsf_pk.csv')
    tcpath2 = os.path.join(basefoldtc, dataset, tcver2, 'tcmsf_sol.csv')
    tcpkpath2 = os.path.join(basefoldtc, dataset, tcver2, 'tcmsf_pk.csv')

    tcconv = 400
    readlen = 4800
    readlen = 2000
    #gaojia3
    readlen = 3200
    #huishen
    readlen = 200
    ussetlen = 0
    dt = 0

    plotprecision = 1
    picrow = 1
    if plotprecision == 1:
        picrow = 2

    lcs = readSensorDataTcSol(lcpath, dt)
    tcs = readSensorDataTcSol(tcpath, dt)
    tcs2 = readSensorDataTcSol(tcpath2, dt)
    lcp = readSensorDataTcXkPk(lcpkpath, dt)
    tcp = readSensorDataTcXkPk(tcpkpath, dt)
    tcp2 = readSensorDataTcXkPk(tcpkpath2, dt)

    print(lcs[0,:])
    print(refdata[0,:])

    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        lcs[:, 7:9] = (lcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs[:, 7:9] = (tcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs2.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs2[:, 7:9] = (tcs2[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    if refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        refdata[:, 7:9] = (refdata[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)

    aligned_data1, aligned_data2, common_timelc,idxlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    print(common_timelc)
    
    aligned_data1, aligned_data2, common_timetc,idxtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    
    aligned_data1, aligned_data2, common_timetc2,idxtc2 = utils.alignDataByTimeTcSol(
        tcs2, tcs2[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc2 = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)

    # if plotgnssstat:
    #     aligned_data1, aligned_data2, common_timegnss,idxgnss = utils.alignDataByTimeTcSol(
    #         gnsstopic, gnsstopic[:, 3], refdata, refdata[:, 0], 10e-3, 1)  # 第4列 (Python索引3对应MATLAB的4)
    #     diff_datagnss = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    print(t0)
    
    plt.close('all')
    tilestr = ['att', 'vel', 'pos']
    if ussetlen == 0:
        ltc=common_timetc[-1]-t0
        llc=common_timelc[-1]-t0
        readlen = max([ltc,llc])

    xranges = [0, readlen*1.1]
    plotlaststat = 0
    plotstat = 0
    limity = 0
    
    for si in range(1, 4):  # 1:3 对应Python中的range(1, 4)
        plt.figure(si)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]

        pi_idx = 3 * (si - 1) + 1   # pi=3*(si-1)+1 + 1
        pie_idx = 3 * (si - 1) + 3  # pie=3*(si-1)+1 + 2
        
        plt.subplot(picrow, 1, 1)
        # 检查数据维度是否足够
        if lcp.shape[1] >= pie_idx:
            p3dlc = np.sqrt(np.sum(lcp[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
            plt.plot(lcp[:, 0] - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1)
        if tcp.shape[1] >= pie_idx:
            p3dtc = np.sqrt(np.sum(tcp[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
            plt.plot(tcp[:, 0] - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1)
        if tcp2.shape[1] >= pie_idx:
            p3dtc = np.sqrt(np.sum(tcp2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
            plt.plot(tcp2[:, 0] - t0, p3dtc, "-o", linewidth=1, color='black', markersize=1)
        plt.xlim(xranges)
        set_y_lim_to_x_range(xranges)
        plt.grid(True)
        
        if si < 4:
            plt.subplot(picrow, 1, 2)
            # 检查数据维度是否足够
            if diff_datalc.shape[1] >= pie_idx:
                p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1, label='lc')
            if diff_datatc.shape[1] >= pie_idx:
                p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1, label='tc')
            if diff_datatc2.shape[1] >= pie_idx:
                p3dtc = np.sqrt(np.sum(diff_datatc2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timetc2 - t0, p3dtc, "-o", linewidth=1, color='black', markersize=1, label='tc2')

            # if plotgnssstat:
            #     plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
            #     # 检查数据维度是否足够
            #     if diff_datagnss.shape[1] >= pie_idx-1 and common_timegnss.shape[1] > 0:
            #         p3dlc = np.sqrt(np.sum(diff_datagnss[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
            #         plt.plot(common_timegnss[:, 0] - t0, p3dlc, "-o", linewidth=1, color='yellow', markersize=2)

            szcl = tcs.shape[1]  # 获取列数
            if plotlaststat and szcl >= 3:  # 最新的为24列，旧的为23列
                plt.plot(lcs[:, 0] - t0, lcs[:, szcl - 3] / 10, "-o", linewidth=1, color='black', markersize=2, label='lc_stat')  # szcl-2变为szcl-3（Python索引）

            if plotstat and szcl >= 3:
                plt.plot(tcs[:, 0] - t0, tcs[:, szcl - 3] / 10, "-o", linewidth=1, color='magenta', markersize=2, label='tc_stat')  # szcl-2变为szcl-3（Python索引）

            plt.xlim(xranges)
            if si == 3 and plotgnssstat and limity:
                plt.ylim([0, 3])
            else:
                set_y_lim_to_x_range(xranges)
        
        plt.legend()  # 更新图例
        plt.grid(True)
    
    plt.show()

# 如果直接运行此脚本，则执行precision3d_tc_lc_ref_100c_函数
if __name__ == "__main__":
    precision3d_tc_lc_ref_100c_()
