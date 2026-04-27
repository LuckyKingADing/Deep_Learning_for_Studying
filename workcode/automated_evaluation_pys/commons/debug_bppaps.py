#!/usr/bin/env python3
"""
调试 bppaps_msfdebg_rts.py 脚本的辅助脚本
"""

import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_bppaps():
    """
    调试 bppaps 函数
    """
    try:
        # 导入主模块
        from modules.util.evaluate_pys.bppaps_msfdebg_rts import bppaps
        
        print("开始调试 bppaps 函数...")
        print("默认参数:")
        print("  foldobjbase_lc: '/mnt/d/dockers/test/rts'")
        print("  foldobjbase_tc: '/mnt/d/dockers/test/rts'")
        print("  foldrefbase: '/mnt/d/dockers/test/rts'")
        print("  resultfile: 'msf_debug_state.csv'")
        
        # 设置断点，便于调试
        import pdb; pdb.set_trace()
        
        # 调用函数
        result = bppaps(
            foldobjbase_lc='/mnt/d/dockers/test/rts',
            foldobjbase_tc='/mnt/d/dockers/test/rts', 
            foldrefbase='/mnt/d/dockers/test/rts',
            resultfile='msf_debug_state.csv'
        )
        
        print(f"函数执行完成，返回结果类型: {type(result)}")
        return result
        
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return None

def debug_individual_functions():
    """
    调试单个函数
    """
    print("选择要调试的函数:")
    print("1. compare_tc_lc_ref_100c_with_plots")
    print("2. InterpState")
    print("3. result_statistics")
    print("4. 全部调试")
    
    choice = input("请输入选择 (1-4): ").strip()
    
    if choice == "1":
        debug_compare_function()
    elif choice == "2":
        debug_interp_function()
    elif choice == "3":
        debug_statistics_function()
    elif choice == "4":
        debug_compare_function()
        debug_interp_function()
        debug_statistics_function()
    else:
        print("无效选择")

def debug_compare_function():
    """
    调试 compare_tc_lc_ref_100c_with_plots 函数
    """
    try:
        from modules.util.evaluate_pys.bppaps_msfdebg_rts import compare_tc_lc_ref_100c_with_plots
        
        print("调试 compare_tc_lc_ref_100c_with_plots 函数...")
        print("注意: 此函数需要有效的文件路径参数")
        
        # 示例路径（需要根据实际情况调整）
        lcpath = input("请输入 LC 文件路径 (默认: /mnt/d/dockers/test/rts/data/msf_debug_state.csv): ").strip()
        if not lcpath:
            lcpath = "/mnt/d/dockers/test/rts/data/msf_debug_state.csv"
            
        tcpath = input("请输入 TC 文件路径 (默认: /mnt/d/dockers/test/rts/data/msf_debug_state.csv): ").strip()
        if not tcpath:
            tcpath = "/mnt/d/dockers/test/rts/data/msf_debug_state.csv"
            
        rtspath = input("请输入 RTS 文件路径 (默认: /mnt/d/dockers/test/rts/data/rts_result.csv): ").strip()
        if not rtspath:
            rtspath = "/mnt/d/dockers/test/rts/data/rts_result.csv"
            
        savedir = input("请输入保存目录 (默认: ./debug_output): ").strip()
        if not savedir:
            savedir = "./debug_output"
        
        # 创建保存目录
        os.makedirs(savedir, exist_ok=True)
        
        print(f"调用函数: compare_tc_lc_ref_100c_with_plots('{lcpath}', '{tcpath}', '{rtspath}', '{savedir}')")
        
        # 设置断点
        import pdb; pdb.set_trace()
        
        result = compare_tc_lc_ref_100c_with_plots(lcpath, tcpath, rtspath, savedir)
        print("函数执行完成")
        
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()

def debug_interp_function():
    """
    调试 InterpState 函数
    """
    try:
        import numpy as np
        from modules.util.evaluate_pys.bppaps_msfdebg_rts import InterpState
        
        print("调试 InterpState 函数...")
        
        # 创建示例数据
        t = np.linspace(0, 10, 100)
        state = np.column_stack([t, np.sin(t), np.cos(t)])
        t_ref = np.linspace(0, 10, 50)
        
        print(f"原始数据形状: {state.shape}")
        print(f"参考时间长度: {len(t_ref)}")
        
        # 设置断点
        import pdb; pdb.set_trace()
        
        result = InterpState(state, t, t_ref)
        print(f"插值后数据形状: {result.shape}")
        
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()

def debug_statistics_function():
    """
    调试 result_statistics 函数
    """
    try:
        import numpy as np
        from modules.util.evaluate_pys.bppaps_msfdebg_rts import result_statistics
        
        print("调试 result_statistics 函数...")
        
        # 创建示例数据
        diff_datalc = np.random.rand(100, 10)  # 模拟LC差异数据
        diff_datatc = np.random.rand(100, 10)  # 模拟TC差异数据
        tcstart = 10  # 起始索引
        
        print(f"LC差异数据形状: {diff_datalc.shape}")
        print(f"TC差异数据形状: {diff_datatc.shape}")
        print(f"TC起始索引: {tcstart}")
        
        # 设置断点
        import pdb; pdb.set_trace()
        
        result = result_statistics(diff_datalc, diff_datatc, tcstart)
        print(f"统计结果类型: {type(result)}")
        if 'LC' in result:
            print(f"LC统计项: {list(result['LC'].keys())}")
        if 'TC' in result:
            print(f"TC统计项: {list(result['TC'].keys())}")
        
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()

def check_dependencies():
    """
    检查依赖项
    """
    print("检查依赖项...")
    
    dependencies = [
        'numpy',
        'matplotlib',
        'scipy',
        'pandas'
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n缺少依赖项: {', '.join(missing_deps)}")
        print("请运行: pip install " + ' '.join(missing_deps))
    else:
        print("\n✓ 所有依赖项均已安装")
    
    # 检查辅助模块
    print("\n检查辅助模块...")
    aux_modules = [
        'readmsf_debug_state',
        'read_rts_file'
    ]
    
    for mod in aux_modules:
        try:
            __import__(f'modules.util.evaluate_pys.{mod}')
            print(f"✓ {mod} 模块可用")
        except ImportError:
            print(f"✗ {mod} 模块不可用")

def main():
    """
    主函数
    """
    print("="*60)
    print("BPPAPS 调试工具")
    print("="*60)
    
    while True:
        print("\n请选择操作:")
        print("1. 调试整个 bppaps 函数")
        print("2. 调试单个函数")
        print("3. 检查依赖项")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            debug_bppaps()
        elif choice == "2":
            debug_individual_functions()
        elif choice == "3":
            check_dependencies()
        elif choice == "4":
            print("退出调试工具")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
