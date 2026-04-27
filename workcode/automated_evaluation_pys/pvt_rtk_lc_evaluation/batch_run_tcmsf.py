#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量执行tcmsf脚本

功能说明：
1. 读取指定路径下的所有子目录
2. 对每个子目录依次执行tcmsf（fusion_mode从配置文件读取）
3. 执行topic_parse解析和wgs to mars坐标转换

使用方法：
    python batch_run_tcmsf.py <输入路径> [配置文件路径]

示例：
    python batch_run_tcmsf.py /path/to/data
    python batch_run_tcmsf.py /path/to data /path/to/config.toml

依赖：
    - 需要sudo权限来复制文件
    - 需要确保tcmsf可执行文件已编译：bazel-bin/modules/localization/src/TCMSF/TCMSF
    - 需要确保record_parser可执行文件已编译
"""

import os
import sys
import subprocess
import shutil
import argparse
import toml
from pathlib import Path
from typing import List, Optional, Dict


class BatchRunTcmsf:
    """批量执行tcmsf的主类"""
    
    def __init__(self, config_file: str, input_path_override: Optional[str] = None):
        """
        初始化批量执行器
        
        参数:
            config_file: 配置文件路径
            input_path_override: 可选，覆盖配置文件中的input_path
        """
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = toml.load(f)
        
        # 从配置文件读取参数
        input_path_str = input_path_override if input_path_override else self.config.get('input_path', '/path/to/data')
        self.input_path = Path(input_path_str)
        self.tcmsf_bin = self.config.get('tcmsf_bin', 'bazel-bin/modules/localization/src/TCMSF/TCMSF')
        self.record_parser_bin = self.config.get('record_parser_bin', 'bazel-bin/modules/localization/src/TCMSF/analysis_tools/tcmsf/tcmsf_parser/PARSER')
        self.convert_bin = self.config.get('convert_bin', 'bazel-bin/modules/localization/src/TCMSF/analysis_tools/wgs84_to_02/convert_ie')
        self.tc_config_file = self.config.get('config_file', 'modules/localization/conf/tcmsf_init_platform_A.toml')
        self.tcmsf_ver = self.config.get('tcmsf_ver', 'v1.0')
        self.verbose = self.config.get('verbose', False)
        
        # 获取项目根目录（从脚本所在目录向上查找，直到找到.bazelignore或WORKSPACE文件）
        script_path = Path(__file__).resolve()
        current_dir = script_path.parent
        self.project_root = None
        
        # 向上查找项目根目录
        while current_dir != current_dir.parent:  # 还没到根目录
            if (current_dir / '.bazelignore').exists() or (current_dir / 'WORKSPACE').exists():
                self.project_root = current_dir
                break
            current_dir = current_dir.parent
        
        # 如果没找到，使用脚本所在目录的父目录的父目录
        if self.project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        
        if self.verbose:
            print(f"[信息] 项目根目录: {self.project_root}")
        self.config_backup = self.config.get('config_backup', True)
        self.gnss_oem_type = self.config.get('gnss_oem_type', 'LG695P')
        self.vehicle_info_file = self.config.get('vehicle_info_file', 'modules/localization/conf/vehicle_hc25.toml')
        self.fusion_modes = self.config.get('fusion_modes', [0, 2, 3])
        self.skip_dirs = self.config.get('skip_dirs', [])
        self.reffold = self.config.get('reffold', '')
        
        # 读取 datasets 配置（新增）
        self.datasets_config = self.config.get('datasets', [])
        
        # 检查是否需要source环境变量
        self.source_env_path = None
        self.tcmsf_working_dir = None  # TCMSF工作目录
        bins = [self.tcmsf_bin, self.record_parser_bin, self.convert_bin]
        for bin_path in bins:
            if not self.is_apollo_bin(bin_path):
                # 非apollo路径，需要source环境变量
                bin_dir = Path(bin_path).parent
                # source_env.sh在bin所在目录的父目录
                source_env_path_candidate = bin_dir.parent / "source_env.sh"
                if source_env_path_candidate.exists():
                    self.source_env_path = source_env_path_candidate
                    self.tcmsf_working_dir = bin_dir.parent  # TCMSF工作目录为tcmsf_offline目录
                    self._source_environment_variables()
                    break
        
        # 输出基础目录
        output_dir_str = self.config.get('output_base_dir', '')
        if output_dir_str:
            self.output_base_dir = Path(output_dir_str)
        else:
            self.output_base_dir = self.input_path
        
        # TCMSF配置文件路径（如果不是绝对路径，则基于项目根目录解析）
        if self.tc_config_file:
            tc_config_path = Path(self.tc_config_file)
            if tc_config_path.is_absolute():
                self.tc_config_file_path = tc_config_path
            else:
                # 相对路径，基于项目根目录解析
                self.tc_config_file_path = (self.project_root / tc_config_path).resolve()
                if self.verbose:
                    print(f"[信息] TCMSF配置文件路径（相对于项目根目录）: {self.tc_config_file_path}")
        else:
            self.tc_config_file_path = None
        
        # 统一的 bin 工作目录（设置为tcmsf_bin的父级目录）
        self.bin_working_dir = Path(self.tcmsf_bin).parent.parent.resolve()
        
        if self.verbose:
            print(f"[信息] Bin工作目录: {self.bin_working_dir}")
        
        # 验证路径
        if not self.input_path.exists():
            raise FileNotFoundError(f"输入路径不存在: {self.input_path}")
        if not self.input_path.is_dir():
            raise NotADirectoryError(f"输入路径不是目录: {self.input_path}")
        
        # 创建输出基础目录
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_subdirectories(self) -> List[Path]:
        """
        获取输入路径下的所有子目录
        
        返回:
            子目录路径列表
        """
        subdirs = []
        for item in self.input_path.iterdir():
            # 跳过隐藏目录和在skip_dirs列表中的目录
            if item.is_dir() and not item.name.startswith('.') and item.name not in self.skip_dirs:
                subdirs.append(item)
        
        # 按名称排序
        subdirs.sort(key=lambda x: x.name)
        return subdirs
    
    def get_dataset_config(self, dataset_name: str) -> Dict[str, str]:
        """
        根据数据集名称获取对应的配置
        
        参数:
            dataset_name: 数据集名称（父目录名）
        
        返回:
            包含 gnss_oem_type 和 vehicle_info_file 的字典
        """
        # 从 datasets_config 中查找匹配的配置
        for dataset in self.datasets_config:
            if dataset['name'] == dataset_name:
                return {
                    'gnss_oem_type': dataset['gnss_oem_type'],
                    'vehicle_info_file': dataset['vehicle_info_file'],
                    'ref_type': dataset.get('ref_type', 'gcj02')
                }
        
        # 如果找不到，使用默认配置
        return {
            'gnss_oem_type': self.gnss_oem_type,
            'vehicle_info_file': self.vehicle_info_file,
            'ref_type': 'gcj02'
        }
    
    def get_subdirectories_for_dataset(self, dataset_path: Path) -> List[Path]:
        """
        获取指定 dataset 下的所有子目录
        
        参数:
            dataset_path: dataset 路径
        
        返回:
            子目录路径列表
        """
        subdirs = []
        for item in dataset_path.iterdir():
            # 跳过隐藏目录和在skip_dirs列表中的目录
            if item.is_dir() and not item.name.startswith('.') and item.name not in self.skip_dirs:
                subdirs.append(item)
        
        # 按名称排序
        subdirs.sort(key=lambda x: x.name)
        return subdirs
    
    def is_apollo_bin(self, bin_path: str) -> bool:
        """
        判断bin路径是否为apollo路径（包含bazel-bin）
        
        参数:
            bin_path: bin文件路径
        
        返回:
            是否为apollo路径
        """
        return "bazel-bin" in bin_path
    
    def _source_environment_variables(self):
        """
        在初始化时source环境变量，将其应用到当前Python进程
        
        注意：这个方法在__init__中调用，如果source失败会抛出异常
        """
        try:
            if self.verbose:
                print(f"[信息] Source环境变量: {self.source_env_path}")
            
            # 执行source命令并捕获输出，使用bash shell
            command = f"source {self.source_env_path} && env"
            result = subprocess.run(
                command,
                shell=True,
                executable='/bin/bash',
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 解析环境变量并更新到当前进程
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
            
            print(f"[成功] 环境变量已从 {self.source_env_path} 加载")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Source环境变量失败: {self.source_env_path}\n错误: {e.stderr}")
    
    def run_command(self, command: List[str], description: str = "", cwd: Optional[Path] = None) -> bool:
        """
        执行shell命令
        
        参数:
            command: 命令及其参数列表
            description: 命令描述（用于日志）
            cwd: 工作目录（可选）
        
        返回:
            命令是否执行成功
        """
        if self.verbose:
            print(f"[执行命令] {description}: {' '.join(command)}")
            if cwd:
                print(f"[工作目录] {cwd}")
        
        # 如果有source_env.sh，需要通过shell执行以继承环境变量
        if self.source_env_path:
            # 通过shell执行，source环境变量
            cmd_str = f"source {self.source_env_path} && {' '.join(command)}"
            if self.verbose:
                print(f"[执行Shell命令] {cmd_str}")
            
            try:
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    executable='/bin/bash',
                    cwd=cwd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if self.verbose:
                    if result.stdout:
                        print(f"[标准输出] {result.stdout}")
                    if result.stderr:
                        print(f"[标准错误] {result.stderr}")
                
                return True
            except subprocess.CalledProcessError as e:
                print(f"[错误] 命令执行失败: {' '.join(command)}")
                print(f"[错误] 返回码: {e.returncode}")
                if e.stderr:
                    print(f"[错误] 错误信息: {e.stderr}")
                else:
                    print(f"[错误] 未捕获到错误信息")
                return False
        else:
            # 没有source_env.sh，直接执行
            try:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if self.verbose:
                    if result.stdout:
                        print(f"[标准输出] {result.stdout}")
                    if result.stderr:
                        print(f"[标准错误] {result.stderr}")
                
                return True
            except subprocess.CalledProcessError as e:
                print(f"[错误] 命令执行失败: {' '.join(command)}")
                print(f"[错误] 返回码: {e.returncode}")
                if e.stderr:
                    print(f"[错误] 错误信息: {e.stderr}")
                else:
                    print(f"[错误] 未捕获到错误信息")
                return False
    
    def get_fusion_mode_type(self, mode: int) -> str:
        """
        根据fusion_mode数值返回对应的类型名称
        
        参数:
            mode: fusion_mode数值
        
        返回:
            类型名称 (pvtlc, pvttc, rtklc, rtktc)
        """
        # 0-pvtlc, 1-pvttc, 2-rtklc, 3-rtktc
        type_map = {
            0: "pvtlc",
            1: "pvttc",
            2: "rtklc",
            3: "rtktc"
        }
        return type_map.get(mode, "unknown")
    
    def modify_config_file(self, modifications: Dict[str, str], result_dir: Optional[Path] = None) -> bool:
        """
        修改配置文件，并保存到data/tmp目录
        
        参数:
            modifications: 配置修改字典，格式为 {配置项: 新值}
            result_dir: 结果目录路径（用于保存配置文件备份）
        
        返回:
            是否修改成功
        """
        if self.tc_config_file_path is None:
            print("[信息] 未指定配置文件，跳过配置修改步骤")
            return True
        
        if not self.tc_config_file_path.exists():
            print(f"[错误] 配置文件不存在: {self.tc_config_file_path}")
            return False
        
        # 备份配置文件到结果目录
        if self.config_backup and result_dir:
            try:
                backup_file = result_dir / f"{self.tc_config_file_path.name}.bak"
                result_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.tc_config_file_path, backup_file)
                if self.verbose:
                    print(f"[信息] 备份配置文件到结果目录: {backup_file}")
            except Exception as e:
                print(f"[错误] 备份配置文件失败: {e}")
                return False
        
        # 读取并修改配置文件
        try:
            with open(self.tc_config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 应用修改
            for key, value in modifications.items():
                old_pattern = f"{key}\\s*=\\s*[^\\n]+"
                new_line = f"{key} = {value}"
                import re
                content = re.sub(old_pattern, new_line, content)
                print(f"[修改] {key} = {value}")
            
            # 写回配置文件到原位置
            with open(self.tc_config_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 同时保存到data/tmp目录
            tmp_dir = Path("data/tmp")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_config_file = tmp_dir / self.tc_config_file_path.name
            
            try:
                with open(tmp_config_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                if self.verbose:
                    print(f"[信息] 配置文件已保存到data/tmp: {tmp_config_file}")
            except Exception as e:
                print(f"[错误] 保存配置文件到data/tmp失败: {e}")
                return False
            
            return True
        except Exception as e:
            print(f"[错误] 修改配置文件失败: {e}")
            return False
    
    def restore_config_file(self) -> bool:
        """
        恢复配置文件
        
        返回:
            是否恢复成功
        """
        if self.tc_config_file_path is None:
            return True
        
        backup_file = self.tc_config_file_path.with_suffix('.toml.bak')
        
        if not backup_file.exists():
            print("[信息] 配置文件备份不存在，跳过恢复")
            return True
        
        try:
            shutil.copy2(backup_file, self.tc_config_file_path)
            if self.verbose:
                print(f"[信息] 恢复配置文件: {self.tc_config_file_path}")
            return True
        except Exception as e:
            print(f"[错误] 恢复配置文件失败: {e}")
            return False
    
    def run_tcmsf(self, dataset_path: Path) -> bool:
        """
        执行tcmsf命令（命令A）
        
        参数:
            dataset_path: 数据集路径
        
        返回:
            是否执行成功
        """
        dataset_name = dataset_path.name
        
        # 使用绝对路径调用 bin
        # 工作目录设置为tcmsf_offline目录（这样TCMSF才能正确创建data/tmp目录）
        command = [str(Path(self.tcmsf_bin).resolve()), str(dataset_path), "tcmsf"]
        
        # 使用tcmsf_working_dir（tcmsf_offline目录）作为工作目录
        working_dir = self.tcmsf_working_dir if self.tcmsf_working_dir else self.bin_working_dir
        success = self.run_command(command, f"执行tcmsf - {dataset_name}", cwd=working_dir)
        
        return success
    
    def copy_results(self, dataset_path: Path, fusion_mode: int, subdatasets_name) -> bool:
        """
        复制tcmsf结果（命令B）
        将整个data/tmp目录复制到输出目录下的dataset名字下，并以type+'_'+tcmsf_ver命名
        
        参数:
            dataset_path: 数据集路径
            fusion_mode: fusion_mode数值
        
        返回:
            是否执行成功
        """
        dataset_name = dataset_path.name
        
        # data/tmp目录在tcmsf_offline目录下
        if self.tcmsf_working_dir:
            source_dir = self.tcmsf_working_dir / "data" / "tmp"
        else:
            source_dir = Path("data/tmp")
        
        if not source_dir.exists():
            print(f"[警告] 源目录不存在: {source_dir}")
            return False
        
        # 获取fusion mode类型
        fusion_type = self.get_fusion_mode_type(fusion_mode)
        
        # 创建输出目录: output_base_dir/dataset_name/type_tcmsf_ver
        result_dir = self.output_base_dir / subdatasets_name / dataset_name / f"{fusion_type}_{self.tcmsf_ver}"
        
        if self.verbose:
            print(f"[信息] Fusion类型: {fusion_type}, 模式: {fusion_mode}, 版本: {self.tcmsf_ver}")
            print(f"[信息] 源目录: {source_dir}")
            print(f"[信息] 目标目录: {result_dir}")
        
        # 复制整个data/tmp目录到结果目录
        try:
            # 如果目标目录已存在，先删除
            if result_dir.exists():
                if self.verbose:
                    print(f"[信息] 删除已存在的结果目录: {result_dir}")
                shutil.rmtree(result_dir)
            
            # 创建父目录
            result_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制整个data/tmp目录
            shutil.copytree(source_dir, result_dir, dirs_exist_ok=False)
            
            if self.verbose:
                print(f"[信息] 已复制整个data/tmp目录到: {result_dir}")
            
            print(f"[成功] 结果已复制到: {result_dir}")
            return True
        except Exception as e:
            print(f"[错误] 复制目录失败: {e}")
            return False
    
    def run_topic_parse(self, dataset_path: Path,subdatasets_name) -> bool:
        """
        执行topic_parse（命令C）
        输出到指定目录下的dataset名字的topic_parse目录中
        
        参数:
            dataset_path: 数据集路径
        
        返回:
            是否执行成功
        """
        dataset_name = dataset_path.name
        output_dir = self.output_base_dir / subdatasets_name / dataset_name / "topic_parse"
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            print(f"[信息] topic_parse输出目录: {output_dir}")
        
        # 使用绝对路径调用 bin，工作目录设置为统一的 bin 目录
        command = [str(Path(self.record_parser_bin).resolve()), str(dataset_path), str(output_dir)]
        
        success = self.run_command(command, f"执行topic_parse - {dataset_name}", cwd=self.bin_working_dir)
        
        if success:
            print(f"[成功] topic_parse完成: {dataset_name}")
        
        return success
    
    @staticmethod
    def convert_ie_to_csv_wgs84(ref_file: Path, output_file: Path) -> bool:
        """
        * 将IE格式的ref.txt中的数据提取为CSV格式的ref_84.txt（保留WGS84坐标，不做坐标偏移）
        * IE格式：头部若干行，数据从包含 "(sec)    (weeks)" 的标记行之后开始，每行数据为空格分隔的18个字段。
        * ref_file: 输入的IE格式ref.txt路径
        * output_file: 输出的CSV格式ref_84.txt路径
        """
        try:
            with open(ref_file, 'r', encoding='utf-8', errors='replace') as f_in:
                lines = f_in.readlines()
            
            # 查找数据起始行：包含 "(sec)    (weeks)" 的标记行
            body_start = -1
            for i, line in enumerate(lines):
                if '(sec)' in line and '(weeks)' in line:
                    body_start = i + 1  # 数据从标记行的下一行开始
                    break
                if lines[0] >= '0' and lines[0] <= '9':
                    body_start = i + 1  # 数据从标记行的下一行开始
                    break
            
            if body_start < 0:
                print(f"[错误] ref.txt中未找到IE格式标记行 '(sec)    (weeks)'")
                return False
            
            data_lines = 0
            with open(output_file, 'w', encoding='utf-8') as f_out:
                for line in lines[body_start:]:
                    line = line.strip()
                    if not line or len(line) < 200:
                        # 与convert_ie.cpp一致：空行或过短行表示数据结束
                        break
                    
                    # 按空格分隔，跳过空字符串
                    fields = line.split()
                    if len(fields) < 18:
                        print(f"[警告] 数据行字段数不足18: {len(fields)}，跳过")
                        continue
                    
                    try:
                        out_line = "{},{},{:>15.10f},{:>15.10f},{:>9s},{:>9s},{:>9s},{:>9s},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{:>15.10f},{},{},{},{}\n".format(
                            fields[0], fields[1],
                            float(fields[2]), float(fields[3]),  # lat, lon 保留WGS84原值
                            fields[4],  
                            fields[5], fields[6], fields[7],  
                            float(fields[8]), float(fields[9]),
                            float(fields[10]), float(fields[11]),
                            float(fields[12]), float(fields[13]),
                            fields[14], fields[15], fields[16], fields[17]
                        )
                        f_out.write(out_line)
                        data_lines += 1
                    except (ValueError, IndexError) as e:
                        print(f"[警告] 解析数据行失败: {e}，跳过该行")
                        continue
            
            if data_lines == 0:
                print(f"[错误] 未从ref.txt中提取到任何有效数据行")
                return False
            
            print(f"[成功] IE→CSV(WGS84)转换完成: {output_file} ({data_lines}行)")
            return True
            
        except Exception as e:
            print(f"[错误] IE→CSV转换异常: {e}")
            return False
    
    def run_wgs_to_mars(self, dataset_path: Path, ref_type: str = "gcj02") -> bool:
        """
        执行坐标转换/格式转换（命令D）
        
        - ref_type="gcj02": 调用convert_ie将ref.txt(IE/WGS84)转为ref_02.txt(CSV/GCJ-02)
        - ref_type="wgs84": 用Python将ref.txt(IE/WGS84)转为ref_84.txt(CSV/WGS84，仅格式转换)
                            同时仍生成ref_02.txt(CSV/GCJ-02)供需要时使用
        
        如果reffold配置有值，ref文件在reffold目录下
        否则，ref文件在dataset目录或input_path下
        
        参数:
            dataset_path: 数据集路径
            ref_type: 参考坐标类型 ('wgs84' 或 'gcj02')
        
        返回:
            是否执行成功
        """
        dataset_name = dataset_path.name
        
        print(f"[信息] 执行WGS to Mars坐标转换 (ref_type={ref_type}) - {dataset_name}")
        
        # 根据reffold配置确定ref文件和输出文件的位置
        if self.reffold:
            # 使用reffold目录
            ref_dir = Path(self.reffold)
            if not ref_dir.exists():
                print(f"[警告] reffold目录不存在: {ref_dir}")
                return True
            
            ref_file = ref_dir / "ref.txt"
            output_file = ref_dir / "ref_02.txt"
            
            if self.verbose:
                print(f"[信息] 使用reffold目录: {ref_dir}")
        else:
            # 查找ref.txt
            # 搜索顺序: 子数据集目录 → 父dataset目录(如.../20260324/) → input_path根目录
            ref_file = dataset_path / "ref.txt"
            
            if not ref_file.exists():
                # 在父目录（dataset级别，如 .../20260324/）下查找
                parent_ref = dataset_path.parent / "ref.txt"
                if parent_ref.exists() and dataset_path.parent != self.input_path:
                    ref_file = parent_ref
                else:
                    # 在input_path根目录下查找
                    ref_file = self.input_path / "ref.txt"
            
            # 输出文件：与ref.txt同目录的ref_02.txt
            output_file = ref_file.parent / "ref_02.txt"
        
        if not ref_file.exists():
            print(f"[警告] 未找到ref.txt文件 - {dataset_name}")
            if self.reffold:
                print(f"[信息] 已搜索reffold: {ref_file}")
            else:
                print(f"[信息] 已搜索路径: {dataset_path}, {dataset_path.parent}, {self.input_path}")
            return True
        
        all_success = True

        # 对于wgs84数据，先生成ref_84.txt（CSV/WGS84，仅格式转换、数据提取）
        if ref_type == 'wgs84':
            ref_84_file = ref_file.parent / "ref_84.txt"
            if ref_84_file.exists():
                print(f"[跳过] ref_84.txt已存在: {ref_84_file}")
            else:
                print(f"[信息] 生成WGS84 CSV参考文件: {ref_84_file}")
                if not self.convert_ie_to_csv_wgs84(ref_file, ref_84_file):
                    print(f"[失败] ref_84.txt生成失败 - {dataset_name}")
                    all_success = False

        # 生成ref_02.txt（CSV/GCJ-02，坐标+格式转换）
        if output_file.exists():
            print(f"[跳过] ref_02.txt已存在: {output_file}")
        else:
            if self.verbose:
                print(f"[信息] 输入文件: {ref_file}")
                print(f"[信息] 输出文件: {output_file}")
            
            command = [str(Path(self.convert_bin).resolve()), str(ref_file), str(output_file)]
            success = self.run_command(command, f"坐标转换 {dataset_name}", cwd=self.bin_working_dir)
            
            if success:
                print(f"[成功] 坐标转换完成: {output_file}")
            else:
                print(f"[失败] 坐标转换失败: {dataset_name}")
                all_success = False

        return all_success
    
    def process_single_dataset(self, dataset_path: Path, subdatasets_name) -> bool:
        """
        处理单个数据集
        执行tcmsf（fusion_mode从配置文件读取），然后执行topic_parse和wgs to mars
        
        参数:
            dataset_path: 数据集路径（子数据集路径）
        
        返回:
            是否全部执行成功
        """
        dataset_name = dataset_path.name
        
        # 从子数据集路径提取父目录名（dataset名称）
        parent_dataset_name = dataset_path.parent.name
        
        # 获取该 dataset 的配置
        dataset_config = self.get_dataset_config(parent_dataset_name)
        gnss_oem_type = dataset_config['gnss_oem_type']
        vehicle_info_file = dataset_config['vehicle_info_file']
        ref_type = dataset_config.get('ref_type', 'gcj02')
        
        print(f"\n{'='*60}")
        print(f"[开始处理] 数据集: {dataset_name}")
        print(f"[所属dataset] {parent_dataset_name}")
        print(f"[GNSS OEM类型] {gnss_oem_type}")
        print(f"[车辆信息文件] {vehicle_info_file}")
        print(f"[参考坐标类型] {ref_type}")
        print(f"{'='*60}")
        
        all_success = True
        
        # 执行tcmsf，fusion_mode从配置文件读取
        for idx, fusion_mode in enumerate(self.fusion_modes, 1):
            print(f"\n[第{idx}次] 执行tcmsf（fusion_mode={fusion_mode}）")
            
            # 计算结果目录
            fusion_type = self.get_fusion_mode_type(fusion_mode)
            result_dir = self.output_base_dir / subdatasets_name / dataset_name / f"{fusion_type}_{self.tcmsf_ver}"
            
            # 第一次执行时，修改gnss_oem_type和vehicle_info_override_file_path
            if idx == 1 and self.tc_config_file_path is not None:
                initial_modifications = {
                    "gnss_oem_type": f'"{gnss_oem_type}"',
                    "vehicle_info_override_file_path": f'"{vehicle_info_file}"'
                }
                
                if not self.modify_config_file(initial_modifications, result_dir):
                    print(f"[失败] 初始配置修改失败 - {dataset_name}")
                    all_success = False
                    return all_success
            
            if self.tc_config_file_path is not None:
                modifications = {
                    "gnss_fusion_mode": str(fusion_mode),
                }
                
                if not self.modify_config_file(modifications, result_dir):
                    print(f"[失败] fusion_mode修改失败 - {dataset_name}")
                    all_success = False
                    break
            
            # 执行tcmsf
            if not self.run_tcmsf(dataset_path):
                print(f"[失败] tcmsf执行失败（第{idx}次）- {dataset_name}")
                all_success = False
                break
            
            # 复制结果
            if not self.copy_results(dataset_path, fusion_mode, subdatasets_name):
                print(f"[失败] 结果复制失败（第{idx}次）- {dataset_name}")
                all_success = False
                break
            
            print(f"[成功] 第{idx}次完成 - {dataset_name} ({fusion_type}_{self.tcmsf_ver})")
        
        # 恢复配置文件
        if self.tc_config_file_path is not None:
            self.restore_config_file()
        
        if not all_success:
            return all_success
        
        # 执行topic_parse和wgs to mars
        print(f"\n[后处理] 执行topic_parse和wgs to mars")
        
        if not self.run_topic_parse(dataset_path,subdatasets_name):
            print(f"[失败] topic_parse执行失败 - {dataset_name}")
            all_success = False
        
        if not self.run_wgs_to_mars(dataset_path, ref_type=ref_type):
            print(f"[失败] wgs to mars执行失败 - {dataset_name}")
            all_success = False
        
        if all_success:
            print(f"[成功] 后处理完成 - {dataset_name}")
            # 写入 ref_type 标记文件到输出目录，供精度评估脚本读取
            ref_type_marker = self.output_base_dir / subdatasets_name / dataset_name / ".ref_type"
            try:
                ref_type_marker.parent.mkdir(parents=True, exist_ok=True)
                ref_type_marker.write_text(ref_type)
                if self.verbose:
                    print(f"[信息] 已写入ref_type标记: {ref_type_marker} -> {ref_type}")
            except Exception as e:
                print(f"[警告] 写入ref_type标记失败: {e}")
        
        print(f"\n{'='*60}")
        if all_success:
            print(f"[完成] 数据集 {dataset_name} 处理完成")
        else:
            print(f"[失败] 数据集 {dataset_name} 处理失败")
        print(f"{'='*60}\n")
        
        return all_success
    
    def run_all(self) -> None:
        """批量处理所有数据集"""
        
        # 判断使用哪种模式
        if self.datasets_config:
            # 新逻辑：两层循环（dataset → subdataset）
            print(f"[信息] 使用 datasets 配置模式")
            print(f"[信息] 找到 {len(self.datasets_config)} 个 dataset 配置")
            print(f"[信息] 输出目录: {self.output_base_dir}")
            print(f"[信息] TCMSF版本: {self.tcmsf_ver}")
            print(f"[信息] Fusion模式: {', '.join(map(str, self.fusion_modes))}")
            
            total_subdatasets = 0
            success_count = 0
            fail_count = 0
            
            # 遍历每个 dataset 配置
            for dataset_config in self.datasets_config:
                dataset_name = dataset_config['name']
                dataset_path = self.input_path / dataset_name
                
                print(f"\n{'='*60}")
                print(f"[Dataset] {dataset_name}")
                print(f"[GNSS OEM类型] {dataset_config['gnss_oem_type']}")
                print(f"[车辆信息文件] {dataset_config['vehicle_info_file']}")
                print(f"[路径] {dataset_path}")
                print(f"{'='*60}")
                
                if not dataset_path.exists():
                    print(f"[警告] Dataset 目录不存在: {dataset_path}")
                    continue
                
                # 获取该 dataset 下的所有子数据集
                subdatasets = self.get_subdirectories_for_dataset(dataset_path)
                
                if not subdatasets:
                    print(f"[警告] Dataset {dataset_name} 下没有子数据集")
                    continue
                
                print(f"\n[信息] 找到 {len(subdatasets)} 个子数据集\n")
                
                # 处理每个子数据集
                for subdataset_path in subdatasets:
                    try:
                        success = self.process_single_dataset(subdataset_path,dataset_name)
                        
                        if success:
                            success_count += 1
                        else:
                            fail_count += 1
                        
                        total_subdatasets += 1
                    except Exception as e:
                        print(f"[异常] 处理子数据集时发生异常 {subdataset_path.name}: {e}")
                        fail_count += 1
                        total_subdatasets += 1
            
            # 输出统计信息
            print(f"\n{'='*60}")
            print(f"[汇总] 批量处理完成")
            print(f"  总子数据集数: {total_subdatasets}")
            print(f"  成功: {success_count}")
            print(f"  失败: {fail_count}")
            if total_subdatasets > 0:
                print(f"  成功率: {success_count/total_subdatasets*100:.2f}%")
            print(f"{'='*60}\n")
            
        else:
            # 原逻辑：向后兼容（没有 datasets 配置时）
            print(f"[信息] 使用原有模式（兼容旧配置）")
            
            # 获取所有子目录
            subdirs = self.get_subdirectories()
            
            if not subdirs:
                print(f"[警告] 输入路径下没有子目录: {self.input_path}")
                return
            
            print(f"[信息] 找到 {len(subdirs)} 个数据集")
            print(f"[信息] 输出目录: {self.output_base_dir}")
            print(f"[信息] TCMSF版本: {self.tcmsf_ver}")
            print(f"[信息] GNSS OEM类型: {self.gnss_oem_type}")
            print(f"[信息] 车辆信息文件: {self.vehicle_info_file}")
            print(f"[信息] Fusion模式: {', '.join(map(str, self.fusion_modes))}")
            
            success_count = 0
            fail_count = 0
            
            # 处理每个数据集
            for dataset_path in subdirs:
                try:
                    success = self.process_single_dataset(dataset_path)
                    
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    print(f"[异常] 处理数据集时发生异常 {dataset_path.name}: {e}")
                    fail_count += 1
            
            # 输出统计信息
            print(f"\n{'='*60}")
            print(f"[汇总] 批量处理完成")
            print(f"  总数: {len(subdirs)}")
            print(f"  成功: {success_count}")
            print(f"  失败: {fail_count}")
            print(f"{'='*60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量执行tcmsf脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置文件（从配置文件读取input_path）
  python batch_run_tcmsf.py
  
  # 指定配置文件
  python batch_run_tcmsf.py /path/to/config.toml
  
  # 覆盖配置文件中的input_path
  python batch_run_tcmsf.py /path/to/config.toml /path/to/data
  
配置文件说明:
  默认配置文件路径: modules/localization/src/batchprocess/batch_run_tcmsf_config.toml
  配置文件为TOML格式，包含以下配置项:
  - input_path: 输入路径，包含多个数据集子目录
  - tcmsf_bin: TCMSF可执行文件路径
  - record_parser_bin: record_parser可执行文件路径
  - config_file: tcmsf配置文件路径
  - tcmsf_ver: tcmsf版本号
  - output_base_dir: 输出基础目录
  - gnss_oem_type: GNSS OEM类型
  - vehicle_info_file: 车辆信息配置文件路径
  - verbose: 是否显示详细输出
  - config_backup: 是否备份配置文件
  - fusion_modes: Fusion模式列表
  - skip_dirs: 要跳过的目录名称列表（如输出目录、临时目录等）
        """
    )
    
    parser.add_argument(
        "config_file",
        type=str,
        nargs='?',
        default="modules/localization/src/batchprocess/batch_run_tcmsf_config.toml",
        help="配置文件路径（默认: modules/localization/src/batchprocess/batch_run_tcmsf_config.toml）"
    )
    
    parser.add_argument(
        "input_path_override",
        type=str,
        nargs='?',
        default=None,
        help="覆盖配置文件中的input_path（可选）"
    )
    
    args = parser.parse_args()
    
    try:
        # 创建批量执行器
        runner = BatchRunTcmsf(
            config_file=args.config_file,
            input_path_override=args.input_path_override
        )
        
        # 执行批量处理
        runner.run_all()
        
        return 0
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())