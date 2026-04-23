import numpy as np
import matplotlib.pyplot as plt
import os
import utils 
import fileutils
from readmsf_debug_state import readmsf_debug_state

def two_version_cmp():
    """
    比较两个版本的结果差异，主要用于需要几乎完全一致的版本对比评估
    """
    # 设置参数
    lcver = 'LC_d74ddee'
    lcver = 'LC_b8d7f45'
    lcver = 'tmp1'
    lcver = 'tmpbase'
    tcver = 'tmp_fl'
    tcver = 'LC_e2e'
    tcver = '8255e68a'
    tcver = 'tmp'
    basefold = '/mnt/d/dockers/test/'
    basefoldtc = basefold 
    dataset = '20250428_gaojia2' 
    dataset = '20250428_gaojia3' 
    dataset = '20250429_huanlegu' #be:因K值未赋值影响结果的
    dataset = '20250429_yanhai' #be
    dataset = '20250429_huishen' 
    dataset = '20250429_huizhan' 
    dataset = '20250430_dameisha' 
    dataset = '20250428_gaojia1' 
    
    lcpath = os.path.join(basefold, dataset, lcver, 'msf_debug_state.csv')#new
    tcpath = os.path.join(basefoldtc, dataset, tcver, 'msf_debug_state.csv')#old

    # 其他参数
    readlen = 150
    ussetlen = 0
    dt = 0
    picrow = 2
    plotxk = 0
    plottcstat = 1
    tstart = 140
    tstart = 0
    plotlcxk = 0
    plottcxk = 1

    # 读取数据
    gnssindex = [1,-1,-1,8,5,6,7,12,13,4,10]
    helpindex = [14,15,16,9]
    
    dt = 0
    tcs = readmsf_debug_state(tcpath, dt)
    lcs = readmsf_debug_state(lcpath, dt)

    # 坐标转换参数
    pi = 3.14159265358979
    d2r = pi / 180
    r2m = d2r * 6378137
    
    print(lcs[0, :])
    # 检查数据维度是否足够进行坐标转换
    if lcs.shape[1] >= 10 :
        lcs[:, 7:9] = (lcs[:, 7:9] - tcs[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    if tcs.shape[1] >= 10 :
        tcs[:, 7:9] = (tcs[:, 7:9] - tcs[0, 7:9]) * r2m  # 第8-9列 (Python索引7-8对应MATLAB的8-9)
    
    # 数据对齐
    diff_datalc = utils.calculateDifference(tcs[:,0:10],lcs[:,0:10])
    common_timelc = tcs[:,0]
    
    t0 = tcs[0, 0]  # 第1列 (Python索引0对应MATLAB的1)
    print('t0 = {%.4f}' % t0)
    # ind=83073
    # print(tcs[ind,1:4])
    # print(lcs[ind,1:4])
    # print(lcs[ind,1:4]-tcs[ind,1:4])
    # print(diff_datalc[ind,1:4])
    # mask = diff_datalc[:, 3] < -1.8
    # indices = np.where(mask)[0]
    # print(indices)
    # print(diff_datalc[indices,0:4])

    plt.close('all')
    tilestr = ['att', 'vel', 'pos','eb ','db ','kod','mpe']
    
    if ussetlen == 0:
        ltc=tcs[-1,0]-t0
        llc=lcs[-1,0]-t0
        readlen = max([ltc,llc])
    xranges = [tstart, readlen*1.1]
    
    figurelen = 4
    for si in range(1, figurelen):  # 限制为1:3 对应Python中的range(1, 4)，避免索引越界
        plt.figure(si)
        plt.title(tilestr[si-1])  # tilestr(si,:) 对应Python中的tilestr[si-1]

        for i in range(1, 4):  # 1:3 对应Python中的range(1, 4)
            pi = 3 * (si - 1) + 1 + i  # pi=3*(si-1)+1+i
            pi_idx = pi - 1  # 转换为Python的0基索引

            plt.subplot(picrow, 3, i)
            # 检查数据维度是否足够
            if lcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(lcs[:, 0] - t0, lcs[:,pi_idx], "-o", linewidth=1, color='red', markersize=1, label='new')
            if tcs.shape[1] > pi_idx:  # 改为 > 以确保索引有效
                plt.plot(tcs[:, 0] - t0, tcs[:,pi_idx], "-o", linewidth=1, color='blue', markersize=1, label='old')
            plt.legend()  # 更新图例
            plt.xlim(xranges)
            plt.grid(True)
            # print(diff_datalc[:, pi_idx])
            if si < 4:
                plt.subplot(picrow, 3, i + 3)
                # 检查数据维度是否足够
                if diff_datalc.shape[1] > pi_idx:
                    plt.plot(common_timelc - t0, diff_datalc[:, pi_idx], "-o", linewidth=1, color='red', markersize=1, label='diff')
            
        plt.legend()  # 更新图例
        plt.grid(True)
        
    plt.grid(True)
    plt.xlim(xranges)
    plt.legend()
    
    plt.show()


# 如果直接运行此脚本，则执行compare_tc_lc_ref_100c函数
if __name__ == "__main__":
    if 1:
        two_version_cmp()
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
