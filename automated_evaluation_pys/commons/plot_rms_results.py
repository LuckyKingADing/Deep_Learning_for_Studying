import numpy as np
import matplotlib.pyplot as plt
import os
import re

def read_rms_results(file_path):
    """
    读取rms_results.txt文件并解析数据
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 使用更精确的正则表达式来匹配各个部分
    # 匹配 diff_datarts RMS values 部分
    datarts_rms_pattern = r'diff_datarts RMS values:(.*?)(?=diff_datarts2 RMS values:|diff_datarts RMS \* 2:|$)'
    # 匹配 diff_datarts2 RMS values 部分
    datarts2_rms_pattern = r'diff_datarts2 RMS values:(.*?)(?=diff_datarts RMS \* 2:|diff_datarts2 RMS \* 2:|$)'
    
    # 匹配 diff_datarts RMS * 2 部分
    datarts_2x_pattern = r'diff_datarts RMS \* 2:(.*?)(?=diff_datarts RMS \* 3:|diff_datarts2 RMS \* 2:|$)'
    # 匹配 diff_datarts RMS * 3 部分
    datarts_3x_pattern = r'diff_datarts RMS \* 3:(.*?)(?=------------------|diff_datarts2 RMS \* 3:|$)'
    
    # 匹配 diff_datarts2 RMS * 2 部分
    datarts2_2x_pattern = r'diff_datarts2 RMS \* 2:(.*?)(?=diff_datarts2 RMS \* 3:|$)'
    # 匹配 diff_datarts2 RMS * 3 部分
    datarts2_3x_pattern = r'diff_datarts2 RMS \* 3:(.*?)$'
    
    rms_datarts_match = re.search(datarts_rms_pattern, content, re.DOTALL)
    rms_datarts2_match = re.search(datarts2_rms_pattern, content, re.DOTALL)
    rms_2x_datarts_match = re.search(datarts_2x_pattern, content, re.DOTALL)
    rms_3x_datarts_match = re.search(datarts_3x_pattern, content, re.DOTALL)
    rms_2x_datarts2_match = re.search(datarts2_2x_pattern, content, re.DOTALL)
    rms_3x_datarts2_match = re.search(datarts2_3x_pattern, content, re.DOTALL)
    
    def parse_values(match):
        if match:
            text = match.group(1).strip()
            values = []
            lines = text.split('\n')
            for line in lines:
                # 匹配 "Column group X: value" 格式
                if 'Column group' in line and ':' in line:
                    try:
                        val_str = line.split(':')[-1].strip()
                        val = float(val_str)
                        values.append(val)
                    except ValueError:
                        continue
            return values
        return []
    
    # 解析所有数据
    rms_datarts = parse_values(rms_datarts_match)
    rms_datarts2 = parse_values(rms_datarts2_match)
    rms_2x_datarts = parse_values(rms_2x_datarts_match)
    rms_3x_datarts = parse_values(rms_3x_datarts_match)
    rms_2x_datarts2 = parse_values(rms_2x_datarts2_match)
    rms_3x_datarts2 = parse_values(rms_3x_datarts2_match)
    
    # 调试信息 - 打印解析的数据
    print(f"Parsed rms_datarts: {rms_datarts}")
    print(f"Parsed rms_datarts2: {rms_datarts2}")
    print(f"Parsed rms_2x_datarts: {rms_2x_datarts}")
    print(f"Parsed rms_3x_datarts: {rms_3x_datarts}")
    print(f"Parsed rms_2x_datarts2: {rms_2x_datarts2}")
    print(f"Parsed rms_3x_datarts2: {rms_3x_datarts2}")
    
    # 返回字典格式的数据
    return {
        'rms_datarts': rms_datarts,
        'rms_datarts2': rms_datarts2,
        'rms_2x_datarts': rms_2x_datarts,
        'rms_3x_datarts': rms_3x_datarts,
        'rms_2x_datarts2': rms_2x_datarts2,
        'rms_3x_datarts2': rms_3x_datarts2
    }

def plot_rms_comparison(datasets, basefold, rts_folder='rts_6304322df', column_indices=[3, 4, 7], column_labels=['Column 4', 'Column 5-6', 'Column 8-9']):
    """
    绘制RMS比较图
    datasets: 数据集名称列表
    basefold: 基础路径
    rts_folder: RTS文件夹名称
    column_indices: 要绘制的列索引（从0开始计数，对应原来的4,5,8列）
    column_labels: 列标签
    """
    n_columns = len(column_indices)
    
    # 为每个数据集读取数据
    all_data = {}
    for dataset in datasets:
        rtspath2 = os.path.join(basefold, dataset, rts_folder, 'rms_results.txt')
        data = read_rms_results(rtspath2)
        all_data[dataset] = data
    
    # 为每一列绘制独立的图（RMS, 2*RMS, 3*RMS），每幅图按3*1的子图布局
    for col_idx, (col_index, col_label) in enumerate(zip(column_indices, column_labels)):
        # 获取要绘制的数据
        dataset_names = list(datasets)
        datarts_rms = [all_data[ds]['rms_datarts'][col_index] if all_data[ds] and len(all_data[ds]['rms_datarts']) > col_index else 0 for ds in datasets]
        datarts2_rms = [all_data[ds]['rms_datarts2'][col_index] if all_data[ds] and len(all_data[ds]['rms_datarts2']) > col_index else 0 for ds in datasets]
        
        datarts_2x = [all_data[ds]['rms_2x_datarts'][col_index] if all_data[ds] and len(all_data[ds]['rms_2x_datarts']) > col_index else 0 for ds in datasets]
        datarts2_2x = [all_data[ds]['rms_2x_datarts2'][col_index] if all_data[ds] and len(all_data[ds]['rms_2x_datarts2']) > col_index else 0 for ds in datasets]
        
        datarts_3x = [all_data[ds]['rms_3x_datarts'][col_index] if all_data[ds] and len(all_data[ds]['rms_3x_datarts']) > col_index else 0 for ds in datasets]
        datarts2_3x = [all_data[ds]['rms_3x_datarts2'][col_index] if all_data[ds] and len(all_data[ds]['rms_3x_datarts2']) > col_index else 0 for ds in datasets]
        
        # 提取地点名称作为横轴标签（去掉日期前缀，例如"20250428_gaojia1"只保留"gaojia1"）
        simplified_datasets = [ds.split('_')[1] if '_' in ds else ds for ds in datasets]
        
        # 创建图形，按3*1的子图布局
        fig, axes = plt.subplots(3, 1, figsize=(12, 12))
        
        # 子图1: RMS
        x = np.arange(len(datasets))
        width = 0.35
        
        bars1 = axes[0].bar(x - width/2, datarts_rms, width, label='diff_datarts', alpha=0.8)
        bars2 = axes[0].bar(x + width/2, datarts2_rms, width, label='diff_datarts2', alpha=0.8)
        
        # 在柱状图上标注数值
        for bar, value in zip(bars1, datarts_rms):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        for bar, value in zip(bars2, datarts2_rms):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        axes[0].set_xlabel('Dataset')
        axes[0].set_ylabel('RMS Value')
        axes[0].set_title(f'{col_label} - RMS Comparison')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(simplified_datasets, rotation=45, ha='right')
        axes[0].legend()
        axes[0].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 子图2: 2*RMS
        bars3 = axes[1].bar(x - width/2, datarts_2x, width, label='diff_datarts', alpha=0.8)
        bars4 = axes[1].bar(x + width/2, datarts2_2x, width, label='diff_datarts2', alpha=0.8)
        
        # 在柱状图上标注数值
        for bar, value in zip(bars3, datarts_2x):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        for bar, value in zip(bars4, datarts2_2x):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        axes[1].set_xlabel('Dataset')
        axes[1].set_ylabel('2*RMS Value')
        axes[1].set_title(f'{col_label} - 2*RMS Comparison')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(simplified_datasets, rotation=45, ha='right')
        axes[1].legend()
        axes[1].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 子图3: 3*RMS
        bars5 = axes[2].bar(x - width/2, datarts_3x, width, label='diff_datarts', alpha=0.8)
        bars6 = axes[2].bar(x + width/2, datarts2_3x, width, label='diff_datarts2', alpha=0.8)
        
        # 在柱状图上标注数值
        for bar, value in zip(bars5, datarts_3x):
            height = bar.get_height()
            axes[2].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        for bar, value in zip(bars6, datarts2_3x):
            height = bar.get_height()
            axes[2].text(bar.get_x() + bar.get_width()/2., height,
                         f'{value:.3f}',
                         ha='center', va='bottom', fontsize=8)
        
        axes[2].set_xlabel('Dataset')
        axes[2].set_ylabel('3*RMS Value')
        axes[2].set_title(f'{col_label} - 3*RMS Comparison')
        axes[2].set_xticks(x)
        axes[2].set_xticklabels(simplified_datasets, rotation=45, ha='right')
        axes[2].legend()
        axes[2].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 调整子图间距
        plt.tight_layout()
        
        # 创建保存路径
        save_dir = os.path.join(basefold, 'rts_compare', rts_folder)
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成图片文件名
        filename = os.path.join(save_dir, f'{col_label}_comparison_{rts_folder}.png')
        
        # 保存图片
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {filename}")
        
        # 关闭图形以释放内存
        plt.close()

def main():
    # 固定的basefold
    basefold = '/mnt/d/dockers/test/'
    
    # RTS文件夹名称
    rts_folder = 'rts_6304322df'
    
    # 数据集名称数组
    datasets = [
        '20250428_gaojia1',
        '20250428_gaojia2',
        '20250428_gaojia3',
        '20250429_yanhai',
        '20250429_huanlegu',
        '20250429_huizhan',
        '20250429_huishen',
        '20250430_dameisha',
    ]
    
    # 只绘制4列(索引3)、5-6列(索引4)、8-9列(索引7)
    # 根据之前的代码，我们处理的列是：
    # 2-3列(norm) -> 索引0
    # 4列 -> 索引1  
    # 5-6列 -> 索引2
    # 7列 -> 索引3
    # 8-9列(norm) -> 索引4
    # 10列 -> 索引5
    # 所以我们需要的是索引1(对应原4列), 2(对应原5-6列), 4(对应原8-9列)
    column_indices = [1, 2, 4]  # 对应原4列、5-6列、8-9列
    column_labels = ['yaw', 'vel_hor', 'pos_hor']
    
    plot_rms_comparison(datasets, basefold, rts_folder, column_indices, column_labels)

if __name__ == "__main__":
    main()
