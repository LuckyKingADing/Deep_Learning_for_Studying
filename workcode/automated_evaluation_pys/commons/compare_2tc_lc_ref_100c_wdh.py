import numpy as np
import matplotlib.pyplot as plt
import os
from readmsf_debug_state import readmsf_debug_state
from read_rts_file import read_rts_file
from readSensorDataTcXkPk import readSensorDataTcXkPk
import utils 
import fileutils

def process_sensor_data(filepath, refdata, pos0, tthreshod, statetype, dt, data_type):
    """
    处理传感器数据(LC或TC)
    
    Args:
        filepath: 数据文件路径
        refdata: 参考数据
        tthreshod: 时间阈值
        statetype: 状态文件类型 0-tcmsf_sol.csv 1-msf_debug_state.csv
        dt: 时间偏移
        data_type: 数据类型名称('LC'或'TC'),用于打印信息
        
    Returns:
        data: 处理后的数据
        diff_data: 差值数据
        common_time: 公共时间点
    """
    print(f"\n读取{data_type}数据: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"  警告: {data_type}文件不存在: {filepath}")
        return None, None, None
    
    # 读取数据
    if statetype == 0:
        data = readSensorDataTcXkPk(filepath, 0)
    else:
        data0 = readmsf_debug_state(filepath, dt)
        data0[:,0] = data0[:,87]
        # 赋值tref: data0[:,0]起点和终点范围内的refdata[:, 0]元素
        tref = refdata[(refdata[:, 0] >= data0[0, 0]) & (refdata[:, 0] <= data0[-1, 0]), 0]
        data = utils.InterpState(data0, data0[:,0], tref)
    
    print(f"  数据维度: {data.shape}")
    print(f"  时间范围: {data[0, 0]:.2f}s ~ {data[-1, 0]:.2f}s")
    
    # 坐标转换：将经纬度转换为米
    data[:, 7:9] = utils.dpos2den(data[:, 7:9],pos0)
    
    # 时间对齐
    print(f"\n进行{data_type}时间对齐...")
    aligned_data1, aligned_data2, common_time, _ = utils.alignDataByTimeTcSol(
        data, data[:, 0], refdata, refdata[:, 0], tthreshod)
    diff_data = utils.calculateDifference(aligned_data1, aligned_data2)
    print(f"  对齐后数据点数: {len(common_time)}")
    
    return data, diff_data, common_time


def compare_tc_lc_ref_rts():
    """
    比较TC、LC和RTS数据与参考数据
    """
    # 设置参数
    tcver = 'tmp2'
    tcver = 'tmp10'
    tcver = 'tmp4'
    tcver = 'tc_366e86a'
    tcver = 'tc_ebec524_v2'#past stable, bug fixed
    tcver = 'tmp'
    tcver = 'tmpB1c'
    tcver = 'tmp1'
    tcver = 'tmpTC_vcpb'
    
    tcver2 = 'tmp_r141'
    tcver2 = 'tc_d7b1489'
    tcver2 = 'TC_9b3f565_v4_3'
    tcver2 = 'tmp'
    tcver2 = 'tmpTC_vcpb'
    
    lcver = 'tmpLC_vcpb'
    
    rtsver = 'rts_6304322df'
    rtsver = 'rts'
    rtsver = 'rts_2bf9a53'
    basefold = '/mnt/d/dockers/test'
    basefold = '/mnt/d/dockers/test/rts'  #e2e_chenshixiagu_2025一直有问题
    basefold = '/mnt/d/dockers/rt/rtk_pvt/2026/0319'
    basefoldtc = basefold
    dataset = 'e2e_chenshixiagu_2025-08-30_08-48-26' #劣，无特别离谱处   半程优 tc_e7c4af61_v2：劣，比较离谱 tc_bc50b05_v2:前优后劣，最后有大误差
    dataset = 'e2e_guangzhou_waimao_2025-11-20_21-26-27' #优  半优 tc_e7c4af61_v2(bc50b05)：优，但也不完全理想 tc_bc50b05_v2:优
    dataset = 'e2e_jiaminggaojia_2025-07-18_08-31-11' #优 tc_e7c4af61_v2：优 tc_bc50b05_v2:整体更劣  也许是静态部分tc不合理？
    dataset = 'e2e_jiaminggaojia_2025-07-17_11-26-29' #劣，无特别离谱处 tc_e7c4af61_v2：劣，无特别离谱处 tc_bc50b05_v2:劣，比较离谱
    dataset = 'e2e_guangzhou_yiyi_2025-11-20_21-26-27' #劣，特别离谱 tc_e7c4af61_v2：劣，比较离谱 tc_bc50b05_v2:劣，比较离谱
    dataset = ''
    refsubfold = ''
    #既然如此，可以试试优化一半的效果
    #tc_bc50b05_v5   目前整体最佳s
    #tc_bc50b05_v6与tc_bc50b05_v5这几组数据无区别
    #tc_bc50b05_v7 优：e2e_chenshixiagu_2025-08-30_08-48-26、e2e_jiaminggaojia_2025-07-18_08-31-11 劣：e2e_jiaminggaojia_2025-07-17_11-26-29 
    # e2e_guangzhou_yiyi_2025-11-20_21-26-27【持续系统偏】
    #e2e_guangzhou_waimao_2025-11-20_21-26-27不好评价，解决了之前的极大误差，但是又引入了系统小偏差似的【怀疑跟重置有关，重置在了无fix解的时候】
    #tc_bc50b05_v8差于v7:理论上不应该
    #tc_bc50b05_v11整体应该是优于tc_bc50b05_v5，不过有些地方系统偏太显著，还有极值跳变等。。。感觉也不适合作为一个打结版本。。。【对比之前稳定版本】
    
    #重置的影响非常大
    

    # LC和TC文件路径
    lcpath = os.path.join(basefold, dataset, lcver, 'msf_debug_state.csv')
    tcpath = os.path.join(basefoldtc, dataset, tcver, 'msf_debug_state.csv')
    tcpath2 = os.path.join(basefoldtc, dataset, tcver2, 'msf_debug_state.csv')

    # 参考数据文件路径
    # RTS文件路径
    reffile = os.path.join(basefold, refsubfold, 'ref_02.txt')

    if 1:
        # 读取列: [0:time, 6:lat, 7:lon, 5:height, 15:ve, 14:vn, 16:vu, 2:roll, 3:pitch, 4:yaw, -1:quality]
        # ref数据中14,15,16对应NEU速度，调整为15,14后存储后的索引4,5,6对应ENU速度
        refdata = fileutils.readfullcsv(reffile,[0,6,7,5,15,14,16,2,3,4,-1])
    else:
        refdata = []
        
    pos0 = refdata[0, 7:9].copy()
    refdata[:, 7:9] = utils.dpos2den(refdata[:, 7:9],pos0)
    
    # 其他参数
    readlen = 100
    ussetlen = 0
    dt = 0
    picrow = 3
    plotxk = 0
    plottcstat = 1
    tstart = 140
    tstart = 0
    plotlcxk = 0
    plottcxk = 1

    statetype = 1
    tthreshod = 1e-3
    
    # 读取LC数据
    lcs = None
    diff_datalc = None
    common_timelc = None
    lcs, diff_datalc, common_timelc = process_sensor_data(
        lcpath, refdata, pos0, tthreshod, statetype, dt, lcver)
    
    # 读取TC数据
    tcs = None
    diff_datatc = None
    common_timetc = None
    tcs, diff_datatc, common_timetc = process_sensor_data(
        tcpath, refdata, pos0, tthreshod, statetype, dt, tcver)
    
    tcs2 = None
    diff_datatc2 = None
    common_timetc2 = None
    tcs2, diff_datatc2, common_timetc2 = process_sensor_data(
        tcpath2, refdata, pos0, tthreshod, statetype, dt, tcver2)

    # 坐标转换参数
    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 数据对齐
    aligned_data1, aligned_data2, common_timelc,idxlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifference(aligned_data1, aligned_data2)
    
    aligned_data1, aligned_data2, common_timetc,idxtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifference(aligned_data1, aligned_data2)
    
    aligned_data1, aligned_data2, common_timetc2,idxtc2 = utils.alignDataByTimeTcSol(
        tcs2, tcs2[:, 0], refdata, refdata[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc2 = utils.calculateDifference(aligned_data1, aligned_data2)

    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)
    print('t0 = {%.4f}' % t0)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos','eb ','db ','kod','mpe']
    
    if ussetlen == 0:
        ltc=tcs[-1,0]-t0
        llc=lcs[-1,0]-t0
        readlen = max([ltc,llc])
    xranges = [tstart, readlen*1.1]
    
    figurelen = 7
    pkoffset = 20
    for si in range(1, figurelen):  # 限制为1:3 对应Python中的range(1, 4)，避免索引越界
        plt.figure(si)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]

        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + 1 + i  # pi=3*(si-1)+1+i
            pi_idx = pi - 1  # 转换为Python的0基索引
            pki_idx = pi - 3 + pkoffset

            plt.subplot(picrow, 3, i) #plot pk
            plt.plot(lcs[:, 0] - t0, lcs[:,pki_idx], "-o", linewidth=1, color='red', markersize=1)
            plt.plot(tcs[:, 0] - t0, tcs[:,pki_idx], "-o", linewidth=1, color='blue', markersize=1)
            plt.plot(tcs2[:, 0] - t0, tcs2[:,pki_idx], "-o", linewidth=1, color='green', markersize=1)
            plt.xlim(xranges)
            plt.grid(True)
            utils.set_y_lim_to_x_range(xranges)
            
            plt.subplot(picrow, 3, i + 3)
            # 检查数据维度是否足够
            if si < 4:
                if lcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                    plt.plot(refdata[:, 0] - t0, refdata[:,pi_idx], "-o", linewidth=1, color='magenta', markersize=1)
            if lcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(lcs[:, 0] - t0, lcs[:,pi_idx], "-o", linewidth=1, color='red', markersize=1)
            if tcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(tcs[:, 0] - t0, tcs[:,pi_idx], "-o", linewidth=1, color='blue', markersize=1)
            if tcs2.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(tcs2[:, 0] - t0, tcs2[:,pi_idx], "-o", linewidth=1, color='green', markersize=1)
            plt.xlim(xranges)
            plt.grid(True)
            utils.set_y_lim_to_x_range(xranges)
            # print(diff_datalc[:, pi_idx])
            if si < 4:
                plt.subplot(picrow, 3, i + 6)
                # 检查数据维度是否足够
                if diff_datalc.shape[1] > pi_idx:
                    plt.plot(common_timelc - t0, diff_datalc[:, pi_idx], "-o", linewidth=1, color='red', markersize=1, label='dff_lc')
                if diff_datatc.shape[1] > pi_idx:
                    plt.plot(common_timetc - t0, diff_datatc[:, pi_idx], "-o", linewidth=1, color='blue', markersize=1, label='dff_tc')
                if diff_datatc2.shape[1] > pi_idx:
                    plt.plot(common_timetc2 - t0, diff_datatc2[:, pi_idx], "-o", linewidth=1, color='green', markersize=1, label='dff_tc2')
            if (si < 4 or si > 6) and plottcstat:
                plt.plot(tcs2[:,0] - t0, tcs2[:, -1]/10, "-.", linewidth=1, color='black', markersize=1, label='stat')
                plt.grid(True)
                plt.xlim(xranges)
            
            plt.legend()  # 更新图例
            utils.set_y_lim_to_x_range(xranges)
        
        plt.grid(True)
    
    plt.figure(figurelen + 1)
    si = 3
    pi_idx = 3 * (si - 1) + 1  # pi=3*(si-1)+1 + 1
    pie_idx = 3 * (si - 1) + 3  # pie=3*(si-1)+1 + 2  改为3
    if diff_datalc.shape[1] >= pie_idx:
        p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1, label='lc')
    if diff_datatc.shape[1] >= pie_idx:
        p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1, label='tc')
    if diff_datatc2.shape[1] >= pie_idx:
        p3dtc2 = np.sqrt(np.sum(diff_datatc2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc2 - t0, p3dtc2, "-o", linewidth=1, color='green', markersize=1, label='tc2')
    
    utils.set_y_lim_to_x_range(xranges)
        
    plt.plot(tcs2[:,0] - t0, tcs2[:, -9]+0.05, "s-", linewidth=1, color='black', markersize=4, label='lt')#pre lc or tc
    plt.xlim(xranges)
    utils.set_y_lim_to_x_range(xranges)
    plt.legend()
    
        
    plt.figure(figurelen + 2) 
    if diff_datatc.shape[1] >= pie_idx:
        p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc - t0, p3dtc, "o-", linewidth=1, color='blue', markersize=1, label='old')
    if diff_datatc2.shape[1] >= pie_idx:
        p3dtc2 = np.sqrt(np.sum(diff_datatc2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc2 - t0, p3dtc2, "-o", linewidth=1, color='green', markersize=1, label='tc')
    plt.plot(tcs2[:,0] - t0, tcs2[:, -1]/10, "-.", linewidth=1, color='black', markersize=1, label='stat')#stat
    plt.plot(tcs2[:,0] - t0, tcs2[:, -2], "o-", linewidth=1, color='black', markersize=1, label='case')#case
    plt.plot(tcs2[:,0] - t0, tcs2[:, -5], "-.", linewidth=1, color='red', markersize=2, label='obs')#obs
    plt.plot(tcs2[:,0] - t0, tcs2[:, -4], "-.", linewidth=1, color='magenta', markersize=2, label='pre')#pre
    plt.plot(tcs2[:,0] - t0, tcs2[:, -6]/100+0.1, "s", linewidth=1, color='blue', markersize=3, label='kRaito')#pre
    # plt.plot(tcs2[:,0] - t0, tcs2[:, -7], "o-", linewidth=1, color='black', markersize=4, label='env')#pre
    # plt.plot(tcs2[:,0] - t0, tcs2[:, -8]+0.05, "s-", linewidth=1, color='magenta', markersize=4, label='fb')#pre
    # plt.plot(tcs2[:,0] - t0, tcs2[:, -3], "-.", linewidth=1, color='yellow', markersize=1)#obs/pre
    
    plt.legend()
    plt.grid(True)
    plt.xlim(xranges)
    utils.set_y_lim_to_x_range(xranges)
    
    
    plt.show()

# 如果直接运行此脚本，则执行compare_tc_lc_ref_100c函数
if __name__ == "__main__":
    compare_tc_lc_ref_rts()
