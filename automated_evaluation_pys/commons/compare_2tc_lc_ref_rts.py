import numpy as np
import matplotlib.pyplot as plt
import os
from readmsf_debug_state import readmsf_debug_state
from read_rts_file import read_rts_file
from readSensorDataTcXkPk import readSensorDataTcXkPk
import utils 

def compare_tc_lc_ref_rts():
    """
    比较TC、LC和RTS数据与参考数据
    """
    # 设置参数
    tcver = 'tmp2'
    tcver = 'tmp10'
    tcver = 'tmp4'
    tcver = 'tmp_pre_lc'
    tcver = 'tmp6'
    tcver = 'tmp_r8'
    tcver = 'tmp_r133'
    tcver = 'tmp_r137'
    tcver = 'tmp_r141'
    tcver = 'tmp_r143'
    tcver = 'tmp_r150'
    tcver = 'tmp_r153'
    tcver = 'tmp_r154'
    tcver = 'tmp_r156'
    tcver = 'tmp_r1572'
    tcver = 'tmp_r1571'
    tcver = 'tmp_r1574'
    tcver = 'tc_test'
    tcver = 'tc_51e68cc6'
    tcver = 'tc_45ed4f5e_v3'
    tcver = 'tc_366e86a'
    tcver = 'tmp_r2'
    tcver = 'tmp_r3'
    tcver = 'tmp_r4_1'
    tcver = 'tmp_r4_3'
    tcver = 'tmp_r4_5'
    tcver = 'tc_366e86a_v2'
    tcver = 'tc_366e86a_v3'
    tcver = 'tc_e7c4af61'
    tcver = 'tc_e7c4af61_v2'
    tcver = 'tc_ebec524'#past stable
    tcver = 'tc_bc50b05_v8'
    tcver = 'tc_bc50b05_v7'
    tcver = 'tc_bc50b05_v9'
    tcver = 'tc_bc50b05_v5'
    tcver = 'tc_bc50b05_v11'
    tcver = '8255e68a'
    tcver = 'LC_9b3f565'
    tcver = 'tc_ebec524_v2'#past stable, bug fixed
    tcver = 'tmp'
    tcver = 'tmpB1c'
    tcver = 'tmp_un0'
    tcver = 'tmp1'
    tcver = 'TC_9b3f565_v3'
    
    tcver2 = 'tmp_pre_tc'
    tcver2 = 'tmp_r12'
    tcver2 = 'tmp_r132'
    tcver2 = 'tmp_r137'
    tcver2 = 'tmp_r141'
    tcver2 = 'tc_test'
    tcver2 = 'tc_51e68cc6_dev2'
    tcver2 = 'tc_45ed4f5e_v2'
    tcver2 = 'tc_45ed4f5e_v3'
    tcver2 = 'tc_366e86a'
    tcver2 = 'tmp_r3'
    tcver2 = 'tc_366e86a_v3'
    tcver2 = 'tc_ebec524_v2'
    tcver2 = 'tc_e7c4af61_v2'
    tcver2 = 'tc_d7b1489'
    tcver2 = 'TC_9b3f565_v4_3'
    tcver2 = 'tmp'
    tcver2 = 'TC_968e3ff7_v3'
    # tcver2 = 'tmp_r4_2'
    lcver = 'LC_968e3ff7'
    
    rtsver = 'rts_6304322df'
    rtsver = 'rts'
    rtsver = 'rts_2bf9a53'
    basefold = '/mnt/d/dockers/test'
    basefold = '/mnt/d/dockers/test/rts'  #e2e_chenshixiagu_2025一直有问题
    basefoldtc = basefold
    dataset = 'e2e_chenshixiagu_2025-08-30_08-48-26' #劣，无特别离谱处   半程优 tc_e7c4af61_v2：劣，比较离谱 tc_bc50b05_v2:前优后劣，最后有大误差
    dataset = 'e2e_guangzhou_waimao_2025-11-20_21-26-27' #优  半优 tc_e7c4af61_v2(bc50b05)：优，但也不完全理想 tc_bc50b05_v2:优
    dataset = 'e2e_jiaminggaojia_2025-07-18_08-31-11' #优 tc_e7c4af61_v2：优 tc_bc50b05_v2:整体更劣  也许是静态部分tc不合理？
    dataset = 'e2e_jiaminggaojia_2025-07-17_11-26-29' #劣，无特别离谱处 tc_e7c4af61_v2：劣，无特别离谱处 tc_bc50b05_v2:劣，比较离谱
    dataset = 'e2e_guangzhou_yiyi_2025-11-20_21-26-27' #劣，特别离谱 tc_e7c4af61_v2：劣，比较离谱 tc_bc50b05_v2:劣，比较离谱
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
    rtspath = os.path.join(basefold, dataset, rtsver, 'rts_result.csv')
    rts0 = read_rts_file(rtspath,1)

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

    # 读取数据
    lcs = readmsf_debug_state(lcpath, dt)
    tcs = readmsf_debug_state(tcpath, dt)
    tcs2 = readmsf_debug_state(tcpath2, dt)
    # lcp = readmsf_debug_state(lcpkpath, dt)
    # tcp = readmsf_debug_state(tcpkpath, dt)
    if plotlcxk == 1:
        lcxkpath = os.path.join(basefold, dataset, lcver, 'tcmsf_xk.csv')
        lcx = readSensorDataTcXkPk(lcxkpath, dt)
    if plottcxk == 1:
        tcxkpath = os.path.join(basefoldtc, dataset, tcver2, 'tcmsf_xk.csv')
        tcx2 = readSensorDataTcXkPk(tcxkpath, dt)
        tcx2[:,0] = tcx2[:,-1]

    # 坐标转换参数
    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        lcs[:, 7:9] = (lcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs[:, 7:9] = (tcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs2.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs2[:, 7:9] = (tcs2[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if rts0.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        rts0[:, 7:9] = (rts0[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    # RTS 插值
    tref = tcs[:,0]
    print(tref[0])
    print(tref[1])
    print(tref[2])
    rts = utils.InterpState(rts0, rts0[:,0], tref)
    tcstemp = tcs2
    tcs2 = utils.InterpState(tcstemp, tcstemp[:,0], tref)

    # 数据对齐
    aligned_data1, aligned_data2, common_timelc,idxlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifference(aligned_data1, aligned_data2)

    print(lcs[0, 0])
    print(rts[0, 0])
    
    aligned_data1, aligned_data2, common_timetc,idxtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifference(aligned_data1, aligned_data2)
    
    aligned_data1, aligned_data2, common_timetc2,idxtc2 = utils.alignDataByTimeTcSol(
        tcs2, tcs2[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
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
                    plt.plot(rts[:, 0] - t0, rts[:,pi_idx], "-o", linewidth=1, color='magenta', markersize=1)
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
            
            if plottcxk:
                plt.plot(tcx2[:,0] - t0, tcx2[:, pi_idx], "-o", linewidth=1, color='magenta', markersize=1, label='xk')
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
    # plt.plot(tcs2[:,0] - t0, tcs2[:, -1]/10, "-.", linewidth=1, color='black', markersize=1)#stat
    if plottcxk:
        p3dtc2 = np.sqrt(np.sum(tcx2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(tcx2[:,0] - t0, p3dtc2, "-o", linewidth=1, color='magenta', markersize=1)
        
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
    if plottcxk:
        p3dtc2 = np.sqrt(np.sum(tcx2[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(tcx2[:,0] - t0, p3dtc2, "-o", linewidth=2, color='red', markersize=1, label='xk')
    
    plt.legend()
    plt.grid(True)
    plt.xlim(xranges)
    utils.set_y_lim_to_x_range(xranges)
    
    
    plt.show()

def compare_tc_lc_ref_rts_with_plots(lcpath, tcpath, rtspath, save_dir):
    """
    比较TC、LC和RTS数据与参考数据，并绘制7副图，同时保存特定时间段的数据
    """
    os.makedirs(save_dir, exist_ok=True)
    # 读取数据
    lcs = readmsf_debug_state(lcpath, 0)
    tcs = readmsf_debug_state(tcpath, 0)
    rts0 = read_rts_file(rtspath, 1)
    
    lcs0 = lcs[:,7:9].copy()
    tcs0 = tcs[:,7:9].copy()

    # 坐标转换参数
    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        lcs[:, 7:9] = (lcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        tcs[:, 7:9] = (tcs[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if rts0.shape[1] >= 10 and rts0.shape[1] >= 10:  # 至少需要10列才能访问第8-9列（索引7-8）
        rts0[:, 7:9] = (rts0[:, 7:9] - rts0[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    # RTS 插值
    tref = tcs[:,0]
    # print(tref[0])
    # print(tref[1])
    # print(tref[2])
    rts = utils.InterpState(rts0, rts0[:,0], tref)

    # 数据对齐
    aligned_lc, aligned_data2, common_timelc,idlc = utils.alignDataByTimeTcSol(
        lcs, lcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datalc = utils.calculateDifference(aligned_lc, aligned_data2)

    print(diff_datalc[0, :])
    print(rts[0, 0])
    
    aligned_tc, aligned_data2, common_timetc,idtc = utils.alignDataByTimeTcSol(
        tcs, tcs[:, 0], rts, rts[:, 0], 1e-3, 1)  # 第1列 (Python索引0对应MATLAB的1)
    diff_datatc = utils.calculateDifference(aligned_tc, aligned_data2)

    lcs_cmn = lcs0[idlc,:]
    tcs_cmn = tcs0[idtc,:]
    
    print('idlc')
    print(idlc[0])
    print('lcs_cmn')
    print(lcs_cmn[0,:])
    print('tcs_cmn')
    print(tcs_cmn[0,:])
    
    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)

    plt.close('all')
    tilestr = ['att', 'vel', 'pos','eb ','db ','kod','mpe']
    
    # 读取数据长度
    ltc = tcs[-1, 0] - t0
    llc = lcs[-1, 0] - t0
    readlen = max([ltc, llc])
    xranges = [0, readlen * 1.1]
    
    # 存储超过阈值的时间段
    lc_high_norm_times = []
    tc_high_norm_times = []
    
    figlen = 8
    for si in range(1, figlen):  # 1:7 对应Python中的range(1, 8)，总共7个子图
        plt.figure(si, figsize=(12, 8))
        plt.suptitle(tilestr[si-1])  # tilestr(si,) 对应Python中的tilestr[si-1]

        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + i  # 

            plt.subplot(2, 3, i)
            # 检查数据维度是否足够
            if si < 4:
                if rts.shape[1] > pi:  # 改为 > 以确保索引有效
                    plt.plot(rts[:, 0] - t0, rts[:, pi], "-o", linewidth=1, color='magenta', markersize=1, label='RTS')
            if lcs.shape[1] > pi:  # 改为 > 以确保索引有效
                plt.plot(lcs[:, 0] - t0, lcs[:, pi], "-o", linewidth=1, color='red', markersize=1, label='LC')
            if tcs.shape[1] > pi:  # 改为 > 以确保索引有效
                plt.plot(tcs[:, 0] - t0, tcs[:, pi], "-o", linewidth=1, color='blue', markersize=1, label='TC')
            plt.xlim(xranges)
            plt.grid(True)
            plt.legend()
            
            # 绘制差值图
            if si < 4:
                plt.subplot(2, 3, i + 3)
                pi_idx = 3 * (si - 1) + 1  # 
                pie_idx = 3 * (si - 1) + 3  # 
                # 检查数据维度是否足够
                if diff_datalc.shape[1] > pi:
                    lc_diff_data = diff_datalc[:, pi]
                    print(diff_datalc[:, pi])
                    plt.plot(common_timelc - t0, lc_diff_data, "-o", linewidth=1, color='red', markersize=1, label='LC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        norm_values = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))
                        high_norm_mask = norm_values > 2.0
                        if np.any(high_norm_mask):
                            # 分别处理时间和数据
                            high_norm_times_list = (common_timelc[high_norm_mask] - t0).tolist()
                            high_norm_data_list = lcs_cmn[high_norm_mask,:].tolist()
                            
                            # 将时间和数据扁平化为单一列表
                            for time, data in zip(high_norm_times_list, high_norm_data_list):
                                flat_entry = [time] + (data if isinstance(data, list) else [data])
                                lc_high_norm_times.append(flat_entry)
                
                if diff_datatc.shape[1] > pi:
                    tc_diff_data = diff_datatc[:, pi]
                    plt.plot(common_timetc - t0, tc_diff_data, "-o", linewidth=1, color='blue', markersize=1, label='TC Diff')
                    
                    # 检查si=3时的norm是否大于2.0
                    if si == 3:  # 当si=3时，检查第3列
                        # 计算norm（假设是向量的模长）
                        norm_values = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))
                        high_norm_mask = norm_values > 2.0
                        if np.any(high_norm_mask):
                            # 分别处理时间和数据
                            high_norm_times_list = (common_timetc[high_norm_mask] - t0).tolist()
                            high_norm_data_list = tcs_cmn[high_norm_mask, :].tolist()
                            
                            # 将时间和数据扁平化为单一列表
                            for time, data in zip(high_norm_times_list, high_norm_data_list):
                                flat_entry = [time] + (data if isinstance(data, list) else [data])
                                tc_high_norm_times.append(flat_entry)

                plt.grid(True)
                plt.xlim(xranges)
                plt.legend()
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'{tilestr[si-1]}_comparison.png'))
        plt.close()
    
    plt.figure(figlen + 1)
    si = 3
    pi_idx = 3 * (si - 1) + 1  # 
    pie_idx = 3 * (si - 1) + 3  # 
    if diff_datalc.shape[1] >= pie_idx:
        p3dlc = np.sqrt(np.sum(diff_datalc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timelc - t0, p3dlc, "-o", linewidth=1, color='red', markersize=1, label='LC Diff')
    if diff_datatc.shape[1] >= pie_idx:
        p3dtc = np.sqrt(np.sum(diff_datatc[:, pi_idx:pie_idx]**2, axis=1))  # pi_idx-2:pie_idx-1 (Python切片)
        plt.plot(common_timetc - t0, p3dtc, "-o", linewidth=1, color='blue', markersize=1, label='TC Diff')
        
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f'hor_comparison.png'))
    plt.close()
    # 保存超过阈值的时间段到文件
    if lc_high_norm_times:
        with open(os.path.join(save_dir, 'lc_high_norm_times.txt'), 'w') as f:
            for entry in lc_high_norm_times:
                f.write(','.join(map(str, entry)) + '\n')
    
    if tc_high_norm_times:
        with open(os.path.join(save_dir, 'tc_high_norm_times.txt'), 'w') as f:
            for entry in tc_high_norm_times:
                f.write(','.join(map(str, entry)) + '\n')


# 如果直接运行此脚本，则执行compare_tc_lc_ref_100c函数
if __name__ == "__main__":
    if 1:
        compare_tc_lc_ref_rts()
    else:
        tcver = 'tc_ebec524'
        lcver = 'rts_2bf9a53'
        basefold = '/mnt/d/dockers/test/rts'
        basefoldtc = basefold
        
        dataset = 'e2e_chenshixiagu_2025-08-30_08-48-26'
        dataset = 'e2e_guangzhou_yiyi_2025-11-20_21-26-27'
        dataset = 'e2e_jiaminggaojia_2025-07-18_08-31-11'

        # LC和TC文件路径
        lcpath = os.path.join(basefold, dataset, lcver, 'msf_debug_state.csv')
        tcpath = os.path.join(basefoldtc, dataset, tcver, 'msf_debug_state.csv')

        # 参考数据文件路径
        # RTS文件路径
        rtspath = os.path.join(basefold, dataset, lcver, 'rts_result.csv')
        save_dir = os.path.join(basefold, dataset, tcver, 'detail_plots')
        compare_tc_lc_ref_rts_with_plots(lcpath,tcpath,rtspath,save_dir)
