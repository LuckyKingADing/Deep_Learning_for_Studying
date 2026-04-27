"""
Head Topic 精度评估 - 统一入口脚本
根据配置文件中的horizontal_only参数自动选择评估模式

使用方法:
    python precision_head_topic_ref_100c_wdh_main.py <config.toml>

配置文件说明:
    horizontal_only = 1  -> 使用水平精度专用模式（precision_head_topic_ref_100c_wdh_horizontal_only）
    horizontal_only = 0  -> 使用完整评估模式（precision_head_topic_ref_100c_wdh）
    配置文件的basefold + dataset需要能定位到输入的的文件夹
"""

import sys
import os

# 添加父目录到Python路径，以便导入commons模块
current_dir = os.path.dirname(os.path.abspath(__file__))
commons_dir = os.path.join(os.path.dirname(current_dir), 'commons')
if commons_dir not in sys.path:
    sys.path.insert(0, commons_dir)

from evaluation_utils import load_config_from_toml
from precision_head_topic_ref_100c_wdh import precision_head_topic_ref_100c_wdh
from precision_head_topic_ref_100c_wdh_horizontal_only import precision_head_topic_ref_100c_wdh_horizontal_only


def main():
    """统一入口函数"""
    print("="*80)
    print("Head Topic 精度评估系统 - 统一入口")
    print("="*80)
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("\n使用方法:")
        print("  python precision_head_topic_ref_100c_wdh_main.py <config.toml>")
        print("\n示例:")
        print("  python precision_head_topic_ref_100c_wdh_main.py precision_head_topic_ref_100c_wdh_config.toml")
        print("\n配置文件说明:")
        print("  在[evaluation]部分设置:")
        print("    horizontal_only = 1  -> 水平精度专用模式")
        print("    horizontal_only = 0  -> 完整评估模式（含高程）")
        return
    
    # 读取配置文件
    config_path = sys.argv[1]
    config = load_config_from_toml(config_path)
    
    # 检查horizontal_only配置
    horizontal_only = config.get('evaluation', {}).get('horizontal_only', 0)
    
    print(f"\n配置文件: {config_path}")
    print(f"评估模式: {'水平精度专用' if horizontal_only == 1 else '完整评估（含高程）'}")
    print(f"horizontal_only = {horizontal_only}")
    
    # 从配置文件读取参数
    basefold = config.get('data', {}).get('basefold', '')
    reffile = config.get('data', {}).get('reffile', '')
    lcver = config.get('data', {}).get('lcver', '')
    tcver = config.get('data', {}).get('tcver', '')
    dataset = config.get('data', {}).get('dataset', '')
    dt = config.get('data', {}).get('dt', 0.0)
    
    plotlc = config.get('plot', {}).get('plotlc', True)
    plottc = config.get('plot', {}).get('plottc', False)
    plotgnssstat = config.get('plot', {}).get('plotgnssstat', True)
    
    tthreshod = config.get('evaluation', {}).get('tthreshod', 5e-3)
    
    output_dir = config.get('output', {}).get('output_dir', '')
    if output_dir == '':
        output_dir = None
    
    reftype = config.get('advanced', {}).get('reftype', 0)
    statetype = config.get('advanced', {}).get('statetype', 0)
    
    print("\n评估参数:")
    print(f"  basefold = {basefold}")
    print(f"  reffile = {reffile}")
    print(f"  lcver = {lcver}")
    print(f"  tcver = {tcver}")
    print(f"  dataset = {dataset}")
    print(f"  dt = {dt}")
    print(f"  plotlc = {plotlc}")
    print(f"  plottc = {plottc}")
    print(f"  plotgnssstat = {plotgnssstat}")
    print(f"  tthreshod = {tthreshod}")
    print(f"  output_dir = {output_dir}")
    print(f"  reftype = {reftype}")
    print(f"  statetype = {statetype}")
    
    print("\n" + "="*80)
    print("开始执行评估...")
    print("="*80 + "\n")
    
    # 根据horizontal_only配置选择评估函数
    if horizontal_only == 1:
        # 使用水平精度专用模式
        print(">>> 调用水平精度专用评估函数\n")
        precision_head_topic_ref_100c_wdh_horizontal_only(
            basefold=basefold,
            reffile=reffile,
            lcver=lcver,
            tcver=tcver,
            dataset=dataset,
            dt=dt,
            plotlc=plotlc,
            plottc=plottc,
            plotgnssstat=plotgnssstat,
            tthreshod=tthreshod,
            output_dir=output_dir,
            reftype=reftype,
            statetype=statetype,
            config=config
        )
    else:
        # 使用完整评估模式
        print(">>> 调用完整评估函数（含高程误差）\n")
        precision_head_topic_ref_100c_wdh(
            basefold=basefold,
            reffile=reffile,
            lcver=lcver,
            tcver=tcver,
            dataset=dataset,
            dt=dt,
            plotlc=plotlc,
            plottc=plottc,
            plotgnssstat=plotgnssstat,
            tthreshod=tthreshod,
            output_dir=output_dir,
            reftype=reftype,
            statetype=statetype,
            config=config
        )
    
    print("\n" + "="*80)
    print("评估完成！")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()