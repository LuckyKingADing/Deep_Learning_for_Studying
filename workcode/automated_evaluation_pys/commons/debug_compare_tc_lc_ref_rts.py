#!/usr/bin/env python3
"""
调试 compare_tc_lc_ref_rts.py 脚本
"""

import sys
import os
import traceback

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_script():
    """
    调试 compare_tc_lc_ref_rts.py 脚本
    """
    print("开始调试 compare_tc_lc_ref_rts.py 脚本...")
    
    # 检查依赖
    try:
        import numpy as np
        print("✓ numpy 已安装")
    except ImportError:
        print("✗ numpy 未安装")
        return False
        
    try:
        import matplotlib.pyplot as plt
        print("✓ matplotlib 已安装")
    except ImportError:
        print("✗ matplotlib 未安装")
        return False
    
    try:
        from readmsf_debug_state import readmsf_debug_state
        print("✓ readmsf_debug_state 模块可导入")
    except ImportError as e:
        print(f"✗ readmsf_debug_state 模块导入失败: {e}")
        return False
    
    try:
        from read_rts_file import read_rts_file
        print("✓ read_rts_file 模块可导入")
    except ImportError as e:
        print(f"✗ read_rts_file 模块导入失败: {e}")
        return False
    
    try:
        from alignDataByTimeTcSol import alignDataByTimeTcSol
        print("✓ alignDataByTimeTcSol 模块可导入")
    except ImportError as e:
        print(f"✗ alignDataByTimeTcSol 模块导入失败: {e}")
        return False
    
    try:
        import utils
        print("✓ utils 模块可导入")
    except ImportError as e:
        print(f"✗ utils 模块导入失败: {e}")
        return False
    
    # 测试函数导入
    try:
        from compare_tc_lc_ref_rts import compare_tc_lc_ref_rts_with_plots
        print("✓ compare_tc_lc_ref_rts_with_plots 函数可导入")
    except ImportError as e:
        print(f"✗ compare_tc_lc_ref_rts_with_plots 函数导入失败: {e}")
        return False
    
    # 检查数据文件是否存在
    print("\n检查数据文件...")
    basefold = '/mnt/d/dockers/test/rts'
    dataset = 'e2e_chenshixiagu_2025-08-30_08-48-26'
    tcver = 'tc_ebec524'
    lcver = 'rts_2bf9a53'
    
    lcpath = os.path.join(basefold, dataset, lcver, 'msf_debug_state.csv')
    tcpath = os.path.join(basefold, dataset, tcver, 'msf_debug_state.csv')
    rtspath = os.path.join(basefold, dataset, lcver, 'rts_result.csv')
    
    print(f"LC文件路径: {lcpath}")
    print(f"TC文件路径: {tcpath}")
    print(f"RTS文件路径: {rtspath}")
    
    if not os.path.exists(lcpath):
        print(f"✗ LC文件不存在: {lcpath}")
    else:
        print(f"✓ LC文件存在")
        
    if not os.path.exists(tcpath):
        print(f"✗ TC文件不存在: {tcpath}")
    else:
        print(f"✓ TC文件存在")
        
    if not os.path.exists(rtspath):
        print(f"✗ RTS文件不存在: {rtspath}")
    else:
        print(f"✓ RTS文件存在")
    
    # 如果文件存在，尝试运行函数
    if os.path.exists(lcpath) and os.path.exists(tcpath) and os.path.exists(rtspath):
        print("\n尝试运行 compare_tc_lc_ref_rts_with_plots 函数...")
        try:
            save_dir = os.path.join(basefold, dataset, tcver, 'detail_plots')
            compare_tc_lc_ref_rts_with_plots(lcpath, tcpath, rtspath, save_dir)
            print("✓ 函数执行成功")
        except Exception as e:
            print(f"✗ 函数执行失败: {e}")
            print("详细错误信息:")
            traceback.print_exc()
            return False
    else:
        print("\n由于缺少数据文件，无法运行函数。")
        print("请确保以下文件存在:")
        print(f"- {lcpath}")
        print(f"- {tcpath}")
        print(f"- {rtspath}")
    
    return True

def debug_step_by_step():
    """
    逐步调试 compare_tc_lc_ref_rts_with_plots 函数
    """
    print("\n开始逐步调试...")
    
    # 导入必要的模块
    from compare_tc_lc_ref_rts import compare_tc_lc_ref_rts_with_plots
    from readmsf_debug_state import readmsf_debug_state
    from read_rts_file import read_rts_file
    from alignDataByTimeTcSol import alignDataByTimeTcSol
    import utils
    import numpy as np
    import os
    
    # 设置路径
    basefold = '/mnt/d/dockers/test/rts'
    dataset = 'e2e_chenshixiagu_2025-08-30_08-48-26'
    tcver = 'tc_ebec524'
    lcver = 'rts_2bf9a53'
    
    lcpath = os.path.join(basefold, dataset, lcver, 'msf_debug_state.csv')
    tcpath = os.path.join(basefold, dataset, tcver, 'msf_debug_state.csv')
    rtspath = os.path.join(basefold, dataset, lcver, 'rts_result.csv')
    
    if not (os.path.exists(lcpath) and os.path.exists(tcpath) and os.path.exists(rtspath)):
        print("数据文件不存在，使用模拟数据进行调试...")
        # 创建模拟数据
        print("创建模拟数据...")
        sample_data = np.random.rand(100, 10)
        sample_rts = np.random.rand(100, 10)
        t0 = 1756518586.415
        
        # 模拟函数执行过程
        print("模拟函数执行过程...")
        try:
            # 坐标转换参数
            pi = 3.14159265358979
            d2r = pi / 180
            r2m = d2r * 6378137
            
            print("1. 数据读取完成")
            
            # 检查数据维度是否足够进行坐标转换
            if sample_data.shape[1] >= 10 and sample_rts.shape[1] >= 10:
                sample_data[:, 7:9] = (sample_data[:, 7:9] - sample_rts[0, 7:9]) * r2m
                sample_rts[:, 7:9] = (sample_rts[:, 7:9] - sample_rts[0, 7:9]) * r2m
            
            print("2. 坐标转换完成")
            
            # RTS 插值
            tref = sample_data[:, 0]
            rts = utils.InterpState(sample_rts, sample_rts[:, 0], tref)
            
            print("3. RTS插值完成")
            
            # 数据对齐
            aligned_lc, aligned_data2, common_timelc = alignDataByTimeTcSol(
                sample_data, sample_data[:, 0], rts, rts[:, 0], 1e-3, 1)
            diff_datalc = utils.calculateDifferenceTcSol(aligned_lc, aligned_data2)
            
            aligned_tc, aligned_data2, common_timetc = alignDataByTimeTcSol(
                sample_data, sample_data[:, 0], rts, rts[:, 0], 1e-3, 1)
            diff_datatc = utils.calculateDifferenceTcSol(aligned_tc, aligned_data2)
            
            print("4. 数据对齐和差异计算完成")
            
            # 检查数据形状
            print(f"   aligned_lc shape: {aligned_lc.shape}")
            print(f"   aligned_tc shape: {aligned_tc.shape}")
            print(f"   diff_datalc shape: {diff_datalc.shape}")
            print(f"   diff_datatc shape: {diff_datatc.shape}")
            print(f"   common_timelc shape: {common_timelc.shape}")
            print(f"   common_timetc shape: {common_timetc.shape}")
            
            print("5. 所有步骤执行成功，没有遇到错误")
            
        except Exception as e:
            print(f"模拟执行过程中出错: {e}")
            traceback.print_exc()
            return False
            
    else:
        print("使用真实数据进行调试...")
        try:
            save_dir = os.path.join(basefold, dataset, tcver, 'detail_plots')
            os.makedirs(save_dir, exist_ok=True)
            compare_tc_lc_ref_rts_with_plots(lcpath, tcpath, rtspath, save_dir)
            print("真实数据处理完成")
        except Exception as e:
            print(f"真实数据处理出错: {e}")
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("Compare_TC_LC_Ref_RTS 调试工具")
    print("="*60)
    
    success = debug_script()
    
    if success:
        debug_step_by_step()
    
    print("\n调试完成。")
