#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将20250428_span_stdref.csv转换为ref.txt格式

输入文件格式：
Week, TOW, UTC, Leap, Q, Lat, Lon, Height, Pos_x, Pos_y, Pos_z, 
Vel_x, Vel_y, Vel_z, Vel_e, Vel_n, Vel_u, Heading, Roll, Pitch

输出文件格式：
GPSTime(sec) Week(weeks) Latitude(deg) Longitude(deg) H-EllHve(m) 
Heading(deg) Pitch(deg) Roll(deg) AccBiasX(m/s^2) GyroDriftX(deg/s) 
AccBiasY(m/s^2) GyroDriftY(deg/s) AccBiasZ(m/s^2) GyroDriftZ(deg/s) 
VNorth(m/s) VEast(m/s) AccUp(m/s^2) Q H-MSL(m) AngRateX(deg/s) 
AngRateY(deg/s) AngRateZ(deg/s) AccBdyX(m/s^2) AccBdyY(m/s^2) AccBdyZ(m/s^2) 
UTCTime(sec)

注意：
- TOW单位为毫秒，转换为秒（除以1000）
- 输入文件中不存在的字段置0
"""

import pandas as pd
import sys
import os


def convert_span_stdref_to_ref(input_csv_path, output_txt_path):
    """
    将span_stdref.csv转换为ref.txt格式
    
    Args:
        input_csv_path: 输入CSV文件路径
        output_txt_path: 输出TXT文件路径
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_csv_path):
        print(f"错误：输入文件不存在: {input_csv_path}")
        sys.exit(1)
    
    # 读取CSV文件
    print(f"正在读取输入文件: {input_csv_path}")
    df = pd.read_csv(input_csv_path)
    
    print(f"输入文件包含 {len(df)} 行数据")
    print(f"输入字段: {list(df.columns)}")
    
    # 创建输出数据框架
    output_data = pd.DataFrame()
    
    # 字段映射关系
    # 输入字段 -> 输出字段
    output_data['GPSTime'] = df['TOW'] / 1000.0  # 毫秒转换为秒
    output_data['Week'] = df['Week']
    output_data['Latitude'] = df['Lat']
    output_data['Longitude'] = df['Lon']
    output_data['H-EllHve'] = df['Height']
    output_data['Heading'] = df['Heading']
    output_data['Pitch'] = df['Pitch']
    output_data['Roll'] = df['Roll']
    output_data['VNorth'] = df['Vel_n']
    output_data['VEast'] = df['Vel_e']
    output_data['Q'] = df['Q']
    output_data['UTCTime'] = df['UTC']
    
    # 输入文件中不存在的字段，全部置0
    output_data['AccBiasX'] = 0.0
    output_data['GyroDriftX'] = 0.0
    output_data['AccBiasY'] = 0.0
    output_data['GyroDriftY'] = 0.0
    output_data['AccBiasZ'] = 0.0
    output_data['GyroDriftZ'] = 0.0
    output_data['AccUp'] = 0.0
    output_data['H-MSL'] = 0.0
    output_data['AngRateX'] = 0.0
    output_data['AngRateY'] = 0.0
    output_data['AngRateZ'] = 0.0
    output_data['AccBdyX'] = 0.0
    output_data['AccBdyY'] = 0.0
    output_data['AccBdyZ'] = 0.0
    
    # 按照ref.txt格式顺序重新排列列
    column_order = [
        'GPSTime', 'Week', 'Latitude', 'Longitude', 'H-EllHve',
        'Heading', 'Pitch', 'Roll', 'AccBiasX', 'GyroDriftX',
        'AccBiasY', 'GyroDriftY', 'AccBiasZ', 'GyroDriftZ',
        'VNorth', 'VEast', 'AccUp', 'Q', 'H-MSL',
        'AngRateX', 'AngRateY', 'AngRateZ', 'AccBdyX', 'AccBdyY', 'AccBdyZ',
        'UTCTime'
    ]
    output_data = output_data[column_order]
    
    # 写入输出文件（手动写入以保留完整文件头和数据精度）
    print(f"正在写入输出文件: {output_txt_path}")
    
    # 定义完整的文件头（包括单位行）
    header_line1 = "GPSTime       Week       Latitude      Longitude     H-EllHve        Heading          Pitch           Roll      AccBiasX    GyroDriftX      AccBiasY    GyroDriftY      AccBiasZ    GyroDriftZ    VNorth     VEast   AccUp Q        H-MSL  AngRateX  AngRateY  AngRateZ AccBdyX AccBdyY AccBdyZ       UTCTime"
    header_line2 = "    (sec)    (weeks)          (deg)          (deg)          (m)          (deg)          (deg)          (deg)       (m/s^2)       (deg/s)       (m/s^2)       (deg/s)       (m/s^2)       (deg/s)     (m/s)     (m/s) (m/s^2)            (m)   (deg/s)   (deg/s)   (deg/s) (m/s^2) (m/s^2) (m/s^2)         (sec)"
    
    with open(output_txt_path, 'w') as f:
        # 写入文件头
        f.write(header_line1 + '\n')
        f.write(header_line2 + '\n')
        
        # 写入数据（对特定字段进行格式化）
        for _, row in output_data.iterrows():
            # 对特定字段进行格式化
            formatted_values = []
            for col in output_data.columns:
                val = row[col]
                if col.startswith('AccBias'):
                    # AccBias保留4位小数
                    formatted_values.append(f"{val:.4f}")
                elif col.startswith('GyroDrift'):
                    # GyroDrift保留3位小数
                    formatted_values.append(f"{val:.3f}")
                elif col.startswith('AngRate'):
                    # AngRate保留5位小数
                    formatted_values.append(f"{val:.5f}")
                elif col.startswith('AccBdy'):
                    # AccBdy保留7位小数
                    formatted_values.append(f"{val:.7f}")
                else:
                    # 其他字段保持原始精度
                    formatted_values.append(str(val))
            
            line = '    '.join(formatted_values)
            f.write(line + '\n')
    
    print(f"转换完成！共处理 {len(output_data)} 行数据")
    print(f"输出文件: {output_txt_path}")


def main():
    """主函数，处理命令行参数"""
    if len(sys.argv) != 3:
        print("使用方法:")
        print("  python convert_span_stdref_to_ref.py <input_csv_path> <output_txt_path>")
        print()
        print("示例:")
        print("  python convert_span_stdref_to_ref.py /mnt/d/dockers/datas/202504/0428/postprocessresult/20250428_span_stdref.csv /mnt/d/dockers/datas/202504/0428/postprocessresult/ref.txt")
        sys.exit(1)
    
    input_csv_path = sys.argv[1]
    output_txt_path = sys.argv[2]
    
    convert_span_stdref_to_ref(input_csv_path, output_txt_path)


if __name__ == '__main__':
    main()