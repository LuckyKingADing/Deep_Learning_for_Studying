import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d
from readSensorDataTcSol import readSensorDataTcSol
from readSensorDataTcXkPk import readSensorDataTcXkPk
from load100ccsv import load100ccsv

from att_diff_adjust import att_diff_adjust
from read_rts_file import read_rts_file
import utils 

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

# def InterpState(state, t, t_ref):
#     state_ = np.zeros([t_ref.shape[0], state.shape[1]])
#     for i in range(state.shape[1]):
#         state_[:, i] = np.interp(t_ref, t, state[:, i])
#     return state_

def precision3d_tc_lc_ref_100c_():
    """
    3D精度分析：TC、LC与RTS参考数据对比
    """
    tcver = 'tcmsf_2146687'
    lcver = 'lc_de359b4'
    basefold = '/mnt/d/dockers/test/'
    basefoldtc = basefold
    dataset = '20250429_huishen'
    dataset = '20250429_huizhan'
    dataset = '20250429_huanlegu'
    dataset = '20250429_yanhai'
    dataset = '20250430_dameisha'
    dataset = '20250428_gaojia3'
    dataset = '20250428_gaojia2'
    dataset = '20250428_gaojia1'
    
    reffile = '/mnt/d/dockers/datas/202504/0429/postprocessresult/20250429_span_stdref_02.csv'
    reffile = '/mnt/d/dockers/datas/202504/0430/postprocessresult/20250430_span_stdref_02.csv'
    reffile = '/mnt/d/dockers/datas/202504/0428/postprocessresult/20250428_span_stdref_02.csv'
    refdata = load100ccsv(reffile, 0, 0)

    lcpath = os.path.join(basefold, dataset, lcver, 'tcmsf_sol.csv')
    lcpkpath = os.path.join(basefold, dataset, lcver, 'tcmsf_pk.csv')

    rtspath = os.path.join(basefold, dataset, 'rts_35c1a60b', 'rts_result.csv')
    rts0 = read_rts_file(rtspath)
    rtspath2 = os.path.join(basefold, dataset, 'rts_6304322df', 'rts_result.csv')
    rts02 = read_rts_file(rtspath2)

    plotgnssstat = 0
    plottc = 0
    plotlc = 0
    plotrts0 = 1
    plotrts2 = 1
    
    
    if plotgnssstat:
        gnssfile = os.path.join('/mnt/d/dockers/test', dataset, tcver, 'gnss.csv')
        gnsstopic = readgnsstopic(gnssfile, list(range(1, 14)))  # 1:13 -> range(1, 14)

    tcpath = os.path.join(basefoldtc, dataset, tcver, 'tcmsf_sol.csv')
    tcpkpath = os.path.join(basefoldtc, dataset, tcver, 'tcmsf_pk.csv')

    tcconv = 400
    readlen = 4800
    readlen = 2000
    #gaojia3
    readlen = 3200
    #huishen
    readlen = 2500
    ussetlen = 0
    dt = 0

    plotprecision = 1
    picrow = 1
    if plotprecision == 1:
        picrow = 2

    lcs = readSensorDataTcSol(lcpath, dt)
    tcs = readSensorDataTcSol(tcpath, dt)
    lcp = readSensorDataTcXkPk(lcpkpath, dt)
    tcp = readSensorDataTcXkPk(tcpkpath, dt)

    print(lcs[0,:])
    print('{%.3f}'%rts0[0,0])

    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        lcs[:, 7:9] = (lcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs[:, 7:9] = (tcs[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if rts0.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        rts0[:, 7:9] = (rts0[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if rts02.shape[1] >= 10 and refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        rts02[:, 7:9] = (rts02[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    #rts 插值
    tref = np.round(rts0[:,0] / 0.01) * 0.01 #需根据数据的实际情况来设置，10hz数据，就归化到0.1s；100hz，归化到0.01s
    rts = utils.InterpState(rts0, rts0[:,0], tref)
    tref2 = np.round(rts02[:,0] / 0.1) * 0.1
    rts2 = utils.InterpState(rts02, rts02[:,0], tref2)

    print(rts[0:10,0])
    print(rts2[0:10,0])
    
    if refdata.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        refdata[:, 7:9] = (refdata[:, 7:9] - refdata[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)

    aligned_data1, aligned_data2, common_timelc,idxlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datalc = att_diff_adjust(diff_datalc)

    aligned_data1, aligned_data2, common_timerts,idxrts = utils.alignDataByTimeTcSol(
        rts, rts[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datarts = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datarts = att_diff_adjust(diff_datarts)
    
    aligned_data1, aligned_data2, common_timerts2,idxrts2 = utils.alignDataByTimeTcSol(
        rts2, rts2[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datarts2 = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datarts2 = att_diff_adjust(diff_datarts2)
    
    # 计算diff_datarts和diff_datarts2的指定列的RMS值
    # 指定列：2-3列(norm)、4列、5-6列、7列、8-9列(norm)、10列 (Python索引为1-2, 3, 4-5, 6, 7-8, 9)
    columns_to_process = [(1, 2), 3, (4, 5), 6, (7, 8), 9]  # Python索引
    
    # 计算diff_datarts各列的RMS值
    rms_values_datarts = []
    for col in columns_to_process:
        if isinstance(col, tuple):
            # 处理多列（norm计算）
            start_col, end_col = col
            # 计算多列的向量范数（平方和再开根号）
            norm_values = np.sqrt(np.sum(diff_datarts[:, start_col:end_col+1]**2, axis=1))
            # 计算RMS
            rms = np.sqrt(np.mean(norm_values**2))
            rms_values_datarts.append(rms)
        else:
            # 单列计算RMS
            rms = np.sqrt(np.mean(diff_datarts[:, col]**2))
            rms_values_datarts.append(rms)
    
    # 计算diff_datarts2各列的RMS值
    rms_values_datarts2 = []
    for col in columns_to_process:
        if isinstance(col, tuple):
            # 处理多列（norm计算）
            start_col, end_col = col
            # 计算多列的向量范数（平方和再开根号）
            norm_values = np.sqrt(np.sum(diff_datarts2[:, start_col:end_col+1]**2, axis=1))
            # 计算RMS
            rms = np.sqrt(np.mean(norm_values**2))
            rms_values_datarts2.append(rms)
        else:
            # 单列计算RMS
            rms = np.sqrt(np.mean(diff_datarts2[:, col]**2))
            rms_values_datarts2.append(rms)
    
    # 计算RMS值的2倍和3倍
    rms_2x_datarts = [rms * 2 for rms in rms_values_datarts]
    rms_3x_datarts = [rms * 3 for rms in rms_values_datarts]
    rms_2x_datarts2 = [rms * 2 for rms in rms_values_datarts2]
    rms_3x_datarts2 = [rms * 3 for rms in rms_values_datarts2]
    
    # 输出结果到文件，文件存储在rtspath2的父目录下
    parent_dir = os.path.dirname(rtspath2)
    output_file_path = os.path.join(parent_dir, 'rms_results.txt')
    
    with open(output_file_path, 'w') as f:
        f.write("RMS Analysis Results for diff_datarts and diff_datarts2\n")
        f.write("="*50 + "\n")
        f.write("Columns processed: 2-3(norm), 4, 5-6, 7, 8-9(norm), 10\n")
        f.write("-"*30 + "\n")
        
        f.write("diff_datarts RMS values:\n")
        for i, rms in enumerate(rms_values_datarts):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
        
        f.write("\ndiff_datarts RMS * 2:\n")
        for i, rms in enumerate(rms_2x_datarts):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
            
        f.write("\ndiff_datarts RMS * 3:\n")
        for i, rms in enumerate(rms_3x_datarts):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
        
        f.write("\n" + "-"*30 + "\n")
        
        f.write("diff_datarts2 RMS values:\n")
        for i, rms in enumerate(rms_values_datarts2):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
        
        f.write("\ndiff_datarts2 RMS * 2:\n")
        for i, rms in enumerate(rms_2x_datarts2):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
            
        f.write("\ndiff_datarts2 RMS * 3:\n")
        for i, rms in enumerate(rms_3x_datarts2):
            f.write(f"  Column group {i+1}: {rms:.6f}\n")
    
    print(f"RMS analysis results saved to: {output_file_path}")
    
    aligned_data1, aligned_data2, common_timetc,idxtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)
    diff_datatc = att_diff_adjust(diff_datatc)

    if plotgnssstat:
        aligned_data1, aligned_data2, common_timegnss,idxgnss = utils.alignDataByTimeTcSol(
            gnsstopic, gnsstopic[:, 3], refdata, refdata[:, 0], 10e-3, 1)  # 第4列 (Python索引3对应MATLAB的4)
        diff_datagnss = utils.calculateDifferenceTcSol(aligned_data1, aligned_data2)

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    print(t0)
    print(common_timetc[-1])
    print(common_timerts[-1])
    plt.close('all')
    tilestr = ['att', 'vel', 'pos']
    if ussetlen == 0:
        ltc=common_timetc[-1]-t0
        llc=common_timelc[-1]-t0
        lrc=common_timerts[-1]-t0
        lrc2=common_timerts2[-1]-t0
        readlen = max([ltc,llc,lrc,lrc2])

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
        # if rts.shape[1] >= pie_idx:
        #     p3drts = np.sqrt(np.sum(rts[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
        #     plt.plot(rts[:, 0] - t0, p3drts, "-o", linewidth=1, color='green', markersize=1)  # 改为绿色以便区分
        plt.xlim(xranges)
        plt.grid(True)
        
        if si < 4:
            plt.subplot(picrow, 1, 2)
            # 检查数据维度是否足够
            if diff_datalc.shape[1] >= pie_idx and plotlc:
                p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1)
            if diff_datatc.shape[1] >= pie_idx and plottc:
                p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1)
            if diff_datarts.shape[1] >= pie_idx and plotrts0:
                p3drts = np.sqrt(np.sum(diff_datarts[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timerts - t0, p3drts, "-o", linewidth=1, color='magenta', markersize=1)  # 改为绿色以便区分
            if diff_datarts2.shape[1] >= pie_idx and plotrts2:
                p3drts2 = np.sqrt(np.sum(diff_datarts2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timerts2 - t0, p3drts2, "-o", linewidth=1, color='green', markersize=1)  # 改为绿色以便区分

            if plotgnssstat:
                plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
                # 检查数据维度是否足够
                if diff_datagnss.shape[1] >= pie_idx-1 and common_timegnss.shape[1] > 0:
                    p3dlc = np.sqrt(np.sum(diff_datagnss[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                    plt.plot(common_timegnss[:, 0] - t0, p3dlc, "-o", linewidth=1, color='yellow', markersize=2)

            szcl = tcs.shape[1]  # 获取列数
            if plotlaststat and szcl >= 3:  # 最新的为24列，旧的为23列
                plt.plot(lcs[:, 0] - t0, lcs[:, szcl - 3] / 10, "-o", linewidth=1, color='black', markersize=2)  # szcl-2变为szcl-3（Python索引）

            if plotstat and szcl >= 3:
                plt.plot(tcs[:, 0] - t0, tcs[:, szcl - 3] / 10, "-o", linewidth=1, color='magenta', markersize=2)  # szcl-2变为szcl-3（Python索引）

            plt.xlim(xranges)
            if si == 3 and plotgnssstat and limity:
                plt.ylim([0, 3])
        if plottc and plotlc and plotrts0 and plotrts2:
            plt.legend(['lc', 'tc', 'rtsold', 'rtsnew'])  # 更新图例
        elif plottc and plotlc and plotrts0:
            plt.legend(['lc', 'tc', 'rtsold'])  # 更新图例
        elif plotlc and plotrts0 and plotrts2:
            plt.legend(['lc', 'rtsold', 'rtsnew'])  # 更新图例
        elif plotrts0 and plotrts2:
            plt.legend(['rtsold', 'rtsnew'])  # 更新图例
        plt.grid(True)
    
    for si in range(1, 4):  # 1:3 对应Python中的range(1, 4)
        plt.figure(si + 3)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]

        pi_idx = 3 * (si - 1) + 3   # pi=3*(si-1)+1 + 1
        pie_idx = 3 * (si - 1) + 4  # pie=3*(si-1)+1 + 2
        
        plt.subplot(picrow, 1, 1)
        # 检查数据维度是否足够
        if lcp.shape[1] >= pie_idx:
            p3dlc = np.sqrt(np.sum(lcp[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
            plt.plot(lcp[:, 0] - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1)
        if tcp.shape[1] >= pie_idx:
            p3dtc = np.sqrt(np.sum(tcp[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
            plt.plot(tcp[:, 0] - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1)
        # if rts.shape[1] >= pie_idx:
        #     p3drts = np.sqrt(np.sum(rts[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-1:pie_idx (Python切片)
        #     plt.plot(rts[:, 0] - t0, p3drts, "-o", linewidth=1, color='green', markersize=1)  # 改为绿色以便区分
        plt.xlim(xranges)
        plt.grid(True)
        
        if si < 4:
            plt.subplot(picrow, 1, 2)
            # 检查数据维度是否足够
            if diff_datalc.shape[1] >= pie_idx and plotlc:
                p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1)
            if diff_datatc.shape[1] >= pie_idx and plottc:
                p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1)
            if diff_datarts.shape[1] >= pie_idx and plotrts0:
                p3drts = np.sqrt(np.sum(diff_datarts[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timerts - t0, p3drts, "-o", linewidth=1, color='magenta', markersize=1)  # 改为绿色以便区分
            if diff_datarts2.shape[1] >= pie_idx and plotrts2:
                p3drts2 = np.sqrt(np.sum(diff_datarts2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                plt.plot(common_timerts2 - t0, p3drts2, "-o", linewidth=1, color='green', markersize=1)  # 改为绿色以便区分

            if plotgnssstat:
                plt.plot(gnsstopic[:, 0] - t0, gnsstopic[:, -1] / 2, "-o", linewidth=1, color='black', markersize=1)
                # 检查数据维度是否足够
                if diff_datagnss.shape[1] >= pie_idx-1 and common_timegnss.shape[1] > 0:
                    p3dlc = np.sqrt(np.sum(diff_datagnss[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
                    plt.plot(common_timegnss[:, 0] - t0, p3dlc, "-o", linewidth=1, color='yellow', markersize=2)

            szcl = tcs.shape[1]  # 获取列数
            if plotlaststat and szcl >= 3:  # 最新的为24列，旧的为23列
                plt.plot(lcs[:, 0] - t0, lcs[:, szcl - 3] / 10, "-o", linewidth=1, color='black', markersize=2)  # szcl-2变为szcl-3（Python索引）

            if plotstat and szcl >= 3:
                plt.plot(tcs[:, 0] - t0, tcs[:, szcl - 3] / 10, "-o", linewidth=1, color='magenta', markersize=2)  # szcl-2变为szcl-3（Python索引）

            plt.xlim(xranges)
            if si == 3 and plotgnssstat and limity:
                plt.ylim([0, 3])
        if plottc and plotlc and plotrts0 and plotrts2:
            plt.legend(['lc', 'tc', 'rtsold', 'rtsnew'])  # 更新图例
        elif plottc and plotlc and plotrts0:
            plt.legend(['lc', 'tc', 'rtsold'])  # 更新图例
        elif plotlc and plotrts0 and plotrts2:
            plt.legend(['lc', 'rtsold', 'rtsnew'])  # 更新图例
        elif plotrts0 and plotrts2:
            plt.legend(['rtsold', 'rtsnew'])  # 更新图例
        plt.grid(True)
    
    plt.show()

# 如果直接运行此脚本，则执行precision3d_tc_lc_ref_100c_函数
if __name__ == "__main__":
    precision3d_tc_lc_ref_100c_()
