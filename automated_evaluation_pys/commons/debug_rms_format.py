import os
import re

def debug_rms_format():
    # 创建一个模拟的rms_results.txt文件用于测试
    sample_content = """RMS Analysis Results for diff_datarts and diff_datarts2
==================================================
Columns processed: 2-3(norm), 4, 5-6, 7, 8-9(norm), 10
------------------------------
diff_datarts RMS values:
  Column group 1: 0.001234
  Column group 2: 0.002345
  Column group 3: 0.003456
  Column group 4: 0.004567
  Column group 5: 0.005678
  Column group 6: 0.006789

diff_datarts RMS * 2:
  Column group 1: 0.002468
  Column group 2: 0.004690
  Column group 3: 0.006912
  Column group 4: 0.009134
  Column group 5: 0.011356
  Column group 6: 0.013578

diff_datarts RMS * 3:
  Column group 1: 0.003702
  Column group 2: 0.007035
  Column group 3: 0.010368
  Column group 4: 0.013701
  Column group 5: 0.017034
  Column group 6: 0.020367

------------------------------
diff_datarts2 RMS values:
  Column group 1: 0.001122
  Column group 2: 0.002233
  Column group 3: 0.003344
  Column group 4: 0.004455
  Column group 5: 0.005566
  Column group 6: 0.006677

diff_datarts2 RMS * 2:
  Column group 1: 0.002244
  Column group 2: 0.004466
  Column group 3: 0.006688
  Column group 4: 0.008910
  Column group 5: 0.011132
  Column group 6: 0.013354

diff_datarts2 RMS * 3:
  Column group 1: 0.003366
  Column group 2: 0.006699
  Column group 3: 0.010032
  Column group 4: 0.013365
  Column group 5: 0.016698
  Column group 6: 0.020031
"""
    
    # 写入临时文件
    with open('temp_rms_sample.txt', 'w') as f:
        f.write(sample_content)
    
    # 读取文件内容
    with open('temp_rms_sample.txt', 'r') as f:
        content = f.read()
    
    print("文件内容:")
    print(content)
    print("\n" + "="*50 + "\n")
    
    # 当前使用的正则表达式
    print("当前使用的正则表达式:")
    
    # 匹配 diff_datarts RMS values 部分
    rms_datarts_match = re.search(r'diff_datarts RMS values:(.*?)(?:\n\n|\n-{5,}|\n[a-zA-Z_]+:)', content, re.DOTALL)
    # 匹配 diff_datarts2 RMS values 部分
    rms_datarts2_match = re.search(r'diff_datarts2 RMS values:(.*?)(?:\n\n|\n-{5,}|\n[a-zA-Z_]+:)', content, re.DOTALL)
    
    print(f"rms_datarts_match: {rms_datarts_match is not None}")
    print(f"rms_datarts2_match: {rms_datarts2_match is not None}")
    
    def parse_values_old(match):
        if match:
            lines = match.group(1).strip().split('\n')
            values = []
            for line in lines:
                # 提取冒号后的数字
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        val = float(parts[-1].strip())
                        values.append(val)
                    except ValueError:
                        continue
            return values
        return []
    
    # 解析数据
    rms_datarts = parse_values_old(rms_datarts_match)
    rms_datarts2 = parse_values_old(rms_datarts2_match)
    
    print(f"解析出的 rms_datarts: {rms_datarts}")
    print(f"解析出的 rms_datarts2: {rms_datarts2}")
    
    # 尝试更精确的正则表达式
    print("\n尝试更精确的正则表达式:")
    
    # 使用更简单的正则表达式
    datarts_rms_pattern = r'diff_datarts RMS values:(.*?)(?=diff_datarts2 RMS values:|diff_datarts RMS \* 2:|$)'
    datarts2_rms_pattern = r'diff_datarts2 RMS values:(.*?)(?=diff_datarts RMS \* 2:|diff_datarts2 RMS \* 2:|$)'
    
    rms_datarts_match_new = re.search(datarts_rms_pattern, content, re.DOTALL)
    rms_datarts2_match_new = re.search(datarts2_rms_pattern, content, re.DOTALL)
    
    def parse_values_new(match):
        if match:
            text = match.group(1).strip()
            # 使用更精确的模式匹配数值
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
    
    rms_datarts_new = parse_values_new(rms_datarts_match_new)
    rms_datarts2_new = parse_values_new(rms_datarts2_match_new)
    
    print(f"新方法解析出的 rms_datarts: {rms_datarts_new}")
    print(f"新方法解析出的 rms_datarts2: {rms_datarts2_new}")
    
    # 清理临时文件
    os.remove('temp_rms_sample.txt')

if __name__ == "__main__":
    debug_rms_format()
