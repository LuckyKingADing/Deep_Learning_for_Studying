#!/usr/bin/env python3
"""
简单调试 bppaps_msfdebg_rts.py 脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(parent_dir))

# 添加当前目录到 Python 路径
sys.path.insert(0, current_dir)

def simple_debug():
    """
    简单调试函数
    """
    print("开始调试 bppaps_msfdebg_rts.py")
    
    # 导入模块
    try:
        from modules.util.evaluate_pys.bppaps_msfdebg_rts import bppaps
        print("✓ 成功导入 bppaps 函数")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    
    # 检查依赖
    dependencies = ['numpy', 'matplotlib', 'scipy']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            return False
    
    # 检查辅助模块
    aux_modules = ['readmsf_debug_state', 'read_rts_file']
    for mod in aux_modules:
        try:
            __import__(f'modules.util.evaluate_pys.{mod}')
            print(f"✓ {mod} 模块可用")
        except ImportError:
            print(f"✗ {mod} 模块不可用")
            return False
    
    print("\n所有依赖项检查通过!")
    print("现在可以开始调试了。")
    
    # 询问是否要运行函数
    run = input("\n是否要运行 bppaps 函数? (y/n): ").lower().strip()
    if run == 'y':
        print("注意：函数需要有效的数据文件路径才能正常运行。")
        print("默认使用以下路径:")
        print("  foldobjbase_lc: '/mnt/d/dockers/test/rts'")
        print("  foldobjbase_tc: '/mnt/d/dockers/test/rts'") 
        print("  foldrefbase: '/mnt/d/dockers/test/rts'")
        print("  resultfile: 'msf_debug_state.csv'")
        
        confirm = input("确认运行? (y/n): ").lower().strip()
        if confirm == 'y':
            try:
                result = bppaps(
                    foldobjbase_lc='/mnt/d/dockers/test/rts',
                    foldobjbase_tc='/mnt/d/dockers/test/rts',
                    foldrefbase='/mnt/d/dockers/test/rts',
                    resultfile='msf_debug_state.csv'
                )
                print(f"函数执行完成，返回结果: {type(result)}")
            except Exception as e:
                print(f"执行出错: {e}")
                import traceback
                traceback.print_exc()
    
    return True

if __name__ == "__main__":
    simple_debug()
