#!/usr/bin/env python3
"""
Localization Initialization Test Results Analyzer
================================================
分析测试结果，生成统计报告和可视化图表。

Usage:
    python analyze_results.py --input ./results/summary.json
    python analyze_results.py --input ./results/summary.json --output ./analysis/
    python analyze_results.py --input ./results/summary.json --output ./analysis/ --format html
"""

import argparse
import json
import os
import sys
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import math

import pandas as pd
import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


ALIGN_TYPE_NAMES = {
    -1: "UNKNOWN",
    0: "UNALIGNED",
    1: "COARSE_ALIGN",
    2: "FINE_ALIGN",
    3: "ALIGNED",
}

FUSION_STATUS_NAMES = {
    -1: "UNKNOWN",
    0: "UNINIT",
    1: "INIT",
    2: "GPSONLY",
    3: "FULLSTATE",
    4: "VFMODE",
    5: "DRMODE",
}


class TestResultsAnalyzer:
    def __init__(self, results: List[Dict[str, Any]], output_dir: str):
        self.results = results
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.df = self._build_dataframe()

    def _build_dataframe(self) -> pd.DataFrame:
        """将结果转换为 DataFrame"""
        records = []
        for r in self.results:
            row = {k: v for k, v in r.items() if k != "log_output"}
            records.append(row)
        return pd.DataFrame(records)

    def get_module_results(self, module: str) -> pd.DataFrame:
        return self.df[self.df["module"] == module].copy()

    def compute_statistics(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """计算统计量"""
        if df is None:
            df = self.df

        numeric_cols = [
            "init_start_to_end_ms",
            "msf_ready_ms",
            "msf_aligned_ms",
            "dr_first_output_ms",
            "first_imu_to_first_output_ms",
            "first_gps_to_first_output_ms",
            "first_valid_gps_to_first_output_ms",
            "config_parse_ms",
            "callbacks_register_ms",
            "readers_create_ms",
            "writers_create_ms",
        ]

        stats_results = {}
        for col in numeric_cols:
            if col not in df.columns:
                continue
            values = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(values) == 0:
                continue

            q25, q50, q75 = values.quantile([0.25, 0.5, 0.75]).values
            stats_results[col] = {
                "count": int(len(values)),
                "mean": float(values.mean()),
                "std": float(values.std()) if len(values) > 1 else 0.0,
                "min": float(values.min()),
                "q25": float(q25),
                "median": float(q50),
                "q75": float(q75),
                "max": float(values.max()),
                "cv": float(values.std() / values.mean()) if len(values) > 1 and values.mean() != 0 else 0.0,
            }

        return stats_results

    def generate_report(self, format: str = "markdown") -> str:
        """生成分析报告"""
        if format == "markdown":
            return self._generate_markdown_report()
        elif format == "html":
            return self._generate_html_report()
        return ""

    def _generate_markdown_report(self) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        lines.append("# Localization 初始化测试分析报告")
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        modules = self.df["module"].unique()

        for mod in modules:
            mod_df = self.get_module_results(mod)
            lines.append(f"\n## 模块: {mod.upper()}")
            lines.append(f"\n测试用例数: {len(mod_df)}")

            success = mod_df["success"].sum()
            lines.append(f"进程成功: {success}/{len(mod_df)} ({100*success/len(mod_df):.1f}%)")

            if mod == "tcmsf":
                msf_ready = mod_df["msf_ready_reached"].sum()
                msf_aligned = mod_df["msf_aligned_reached"].sum()
                lines.append(f"MSF Ready: {msf_ready}/{len(mod_df)} ({100*msf_ready/len(mod_df):.1f}%)")
                lines.append(f"MSF Aligned: {msf_aligned}/{len(mod_df)} ({100*msf_aligned/len(mod_df):.1f}%)")

                init_times = pd.to_numeric(mod_df["init_start_to_end_ms"], errors="coerce").dropna()
                if len(init_times) > 0:
                    lines.append(f"\n**初始化耗时 (ms)**")
                    lines.append(f"- 平均: {init_times.mean():.2f} ms")
                    lines.append(f"- 中位数: {init_times.median():.2f} ms")
                    lines.append(f"- 标准差: {init_times.std():.2f} ms")
                    lines.append(f"- 范围: [{init_times.min():.2f}, {init_times.max():.2f}]")

                ready_times = pd.to_numeric(mod_df["msf_ready_ms"], errors="coerce").dropna()
                if len(ready_times) > 0:
                    lines.append(f"\n**MSF Ready 耗时 (ms)**")
                    lines.append(f"- 平均: {ready_times.mean():.2f} ms")
                    lines.append(f"- 中位数: {ready_times.median():.2f} ms")
                    lines.append(f"- 标准差: {ready_times.std():.2f} ms")
                    lines.append(f"- 范围: [{ready_times.min():.2f}, {ready_times.max():.2f}]")

                aligned_times = pd.to_numeric(mod_df["msf_aligned_ms"], errors="coerce").dropna()
                if len(aligned_times) > 0:
                    lines.append(f"\n**MSF Aligned 耗时 (ms)**")
                    lines.append(f"- 平均: {aligned_times.mean():.2f} ms")
                    lines.append(f"- 中位数: {aligned_times.median():.2f} ms")
                    lines.append(f"- 标准差: {aligned_times.std():.2f} ms")
                    lines.append(f"- 范围: [{aligned_times.min():.2f}, {aligned_times.max():.2f}]")

                lines.append(f"\n**首次输出时的融合状态分布**")
                status_counts = mod_df["fusion_status_at_first_output"].value_counts()
                for status, count in status_counts.items():
                    name = FUSION_STATUS_NAMES.get(int(status), f"STATUS_{status}")
                    lines.append(f"- {name}: {count} ({100*count/len(mod_df):.1f}%)")

                lines.append(f"\n**首次输出时的对准状态分布**")
                align_counts = mod_df["align_status_at_first_output"].value_counts()
                for status, count in align_counts.items():
                    name = ALIGN_TYPE_NAMES.get(int(status), f"TYPE_{status}")
                    lines.append(f"- {name}: {count} ({100*count/len(mod_df):.1f}%)")

            elif mod == "dr":
                init_times = pd.to_numeric(mod_df["init_start_to_end_ms"], errors="coerce").dropna()
                if len(init_times) > 0:
                    lines.append(f"\n**DR 初始化耗时 (ms)**")
                    lines.append(f"- 平均: {init_times.mean():.2f} ms")
                    lines.append(f"- 中位数: {init_times.median():.2f} ms")
                    lines.append(f"- 标准差: {init_times.std():.2f} ms")

                output_times = pd.to_numeric(mod_df["dr_first_output_ms"], errors="coerce").dropna()
                if len(output_times) > 0:
                    lines.append(f"\n**DR 首次输出耗时 (ms)**")
                    lines.append(f"- 平均: {output_times.mean():.2f} ms")
                    lines.append(f"- 中位数: {output_times.median():.2f} ms")
                    lines.append(f"- 标准差: {output_times.std():.2f} ms")

        lines.append("\n## 失败用例详情")
        failed = self.df[~self.df["success"]]
        if len(failed) > 0:
            for _, row in failed.iterrows():
                lines.append(f"\n### {row['case_name']}")
                lines.append(f"- 记录: {row['record_path']}")
                lines.append(f"- 错误: {row['error_message'][:200]}")
        else:
            lines.append("\n无失败用例。")

        return "\n".join(lines)

    def _generate_html_report(self) -> str:
        """生成 HTML 格式报告"""
        md = self._generate_markdown_report()

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Localization 初始化测试分析报告</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        max-width: 1200px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
h2 {{ color: #555; margin-top: 30px; border-left: 4px solid #007bff; padding-left: 10px; }}
h3 {{ color: #666; }}
.metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }}
.stat-box {{ background: #e9ecef; padding: 12px; border-radius: 5px; }}
.stat-label {{ font-size: 12px; color: #666; }}
.stat-value {{ font-size: 20px; font-weight: bold; color: #007bff; }}
.pass {{ color: #28a745; }}
.fail {{ color: #dc3545; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #007bff; color: white; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
code {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; }}
</style>
</head>
<body>
<h1>Localization 初始化测试分析报告</h1>
<p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""

        modules = self.df["module"].unique()
        for mod in modules:
            mod_df = self.get_module_results(mod)
            success = mod_df["success"].sum()
            total = len(mod_df)

            html += f"""
<h2>模块: {mod.upper()}</h2>
<div class="metric">
<div class="stat-grid">
<div class="stat-box">
<div class="stat-label">测试用例</div>
<div class="stat-value">{total}</div>
</div>
<div class="stat-box">
<div class="stat-label">成功率</div>
<div class="stat-value pass">{100*success/total:.1f}%</div>
</div>
"""
            if mod == "tcmsf":
                msf_ready = mod_df["msf_ready_reached"].sum()
                msf_aligned = mod_df["msf_aligned_reached"].sum()
                html += f"""
<div class="stat-box">
<div class="stat-label">MSF Ready</div>
<div class="stat-value">{100*msf_ready/total:.1f}%</div>
</div>
<div class="stat-box">
<div class="stat-label">MSF Aligned</div>
<div class="stat-value">{100*msf_aligned/total:.1f}%</div>
</div>
"""
            html += "</div></div>"

        html += "<hr><p>详细报告请查看 Markdown 输出。</p></body></html>"
        return html

    def save_report(self, format: str = "markdown"):
        """保存报告到文件"""
        if format == "markdown":
            path = os.path.join(self.output_dir, "analysis_report.md")
            with open(path, "w") as f:
                f.write(self._generate_markdown_report())
            return path
        elif format == "html":
            path = os.path.join(self.output_dir, "analysis_report.html")
            with open(path, "w") as f:
                f.write(self._generate_html_report())
            return path

    def save_statistics(self) -> str:
        """保存详细统计数据"""
        stats = self.compute_statistics()
        path = os.path.join(self.output_dir, "statistics.json")
        with open(path, "w") as f:
            json.dump(stats, f, indent=2, default=str)
        return path

    def plot_results(self):
        """生成可视化图表"""
        if not HAS_MATPLOTLIB:
            print("matplotlib not available, skipping plots")
            return

        modules = self.df["module"].unique()
        for mod in modules:
            mod_df = self.get_module_results(mod)
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(f"{mod.upper()} - Initialization Test Results", fontsize=14, fontweight="bold")

            if mod == "tcmsf":
                init_times = pd.to_numeric(mod_df["init_start_to_end_ms"], errors="coerce").dropna()
                axes[0, 0].hist(init_times, bins=20, edgecolor="black", alpha=0.7, color="steelblue")
                axes[0, 0].set_xlabel("Time (ms)")
                axes[0, 0].set_ylabel("Count")
                axes[0, 0].set_title("Component Init Duration")
                axes[0, 0].axvline(init_times.mean(), color="red", linestyle="--", label=f"Mean: {init_times.mean():.1f}ms")
                axes[0, 0].axvline(init_times.median(), color="orange", linestyle="--", label=f"Median: {init_times.median():.1f}ms")
                axes[0, 0].legend()

                ready_times = pd.to_numeric(mod_df["msf_ready_ms"], errors="coerce").dropna()
                axes[0, 1].hist(ready_times, bins=20, edgecolor="black", alpha=0.7, color="forestgreen")
                axes[0, 1].set_xlabel("Time (ms)")
                axes[0, 1].set_ylabel("Count")
                axes[0, 1].set_title("MSF Ready Duration")
                axes[0, 1].axvline(ready_times.mean(), color="red", linestyle="--", label=f"Mean: {ready_times.mean():.1f}ms")
                axes[0, 1].legend()

                aligned_times = pd.to_numeric(mod_df["msf_aligned_ms"], errors="coerce").dropna()
                axes[1, 0].hist(aligned_times, bins=20, edgecolor="black", alpha=0.7, color="darkorange")
                axes[1, 0].set_xlabel("Time (ms)")
                axes[1, 0].set_ylabel("Count")
                axes[1, 0].set_title("MSF Aligned Duration")
                axes[1, 0].axvline(aligned_times.mean(), color="red", linestyle="--", label=f"Mean: {aligned_times.mean():.1f}ms")
                axes[1, 0].legend()

                status_data = mod_df["fusion_status_at_first_output"].value_counts()
                labels = [FUSION_STATUS_NAMES.get(int(s), f"S{s}") for s in status_data.index]
                axes[1, 1].bar(labels, status_data.values, color="steelblue", edgecolor="black")
                axes[1, 1].set_xlabel("Fusion Status")
                axes[1, 1].set_ylabel("Count")
                axes[1, 1].set_title("Fusion Status at First Output")
                axes[1, 1].tick_params(axis="x", rotation=45)

            elif mod == "dr":
                init_times = pd.to_numeric(mod_df["init_start_to_end_ms"], errors="coerce").dropna()
                axes[0, 0].hist(init_times, bins=20, edgecolor="black", alpha=0.7, color="steelblue")
                axes[0, 0].set_xlabel("Time (ms)")
                axes[0, 0].set_ylabel("Count")
                axes[0, 0].set_title("DR Init Duration")
                axes[0, 0].axvline(init_times.mean(), color="red", linestyle="--", label=f"Mean: {init_times.mean():.1f}ms")
                axes[0, 0].legend()

                output_times = pd.to_numeric(mod_df["dr_first_output_ms"], errors="coerce").dropna()
                axes[0, 1].hist(output_times, bins=20, edgecolor="black", alpha=0.7, color="forestgreen")
                axes[0, 1].set_xlabel("Time (ms)")
                axes[0, 1].set_ylabel("Count")
                axes[0, 1].set_title("First DR Output (from IMU)")
                axes[0, 1].axvline(output_times.mean(), color="red", linestyle="--", label=f"Mean: {output_times.mean():.1f}ms")
                axes[0, 1].legend()

                stage_cols = ["config_parse_ms", "callbacks_register_ms", "readers_create_ms", "writers_create_ms"]
                stage_labels = ["Config Parse", "Callbacks Reg", "Readers", "Writers"]
                stage_data = []
                for col in stage_cols:
                    vals = pd.to_numeric(mod_df[col], errors="coerce").dropna()
                    stage_data.append(vals.mean() if len(vals) > 0 else 0)
                axes[1, 0].bar(stage_labels, stage_data, color="coral", edgecolor="black")
                axes[1, 0].set_ylabel("Time (ms)")
                axes[1, 0].set_title("Init Stage Breakdown")
                for i, v in enumerate(stage_data):
                    axes[1, 0].text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=9)

            plt.tight_layout()
            plot_path = os.path.join(self.output_dir, f"{mod}_init_analysis.png")
            plt.savefig(plot_path, dpi=150)
            plt.close()
            print(f"  Plot saved: {plot_path}")

        if HAS_SCIPY and len(self.df) > 1:
            try:
                fig2, axes2 = plt.subplots(1, 1, figsize=(10, 6))
                tcmsf_df = self.get_module_results("tcmsf")
                if len(tcmsf_df) > 2:
                    init_times = pd.to_numeric(tcmsf_df["msf_ready_ms"], errors="coerce").dropna().values
                    if len(init_times) >= 3:
                        fig2.suptitle("MSF Ready Time Distribution with Normal Fit")
                        axes2.hist(init_times, bins=min(20, len(init_times)), density=True, alpha=0.7, color="steelblue")
                        mu, std = np.mean(init_times), np.std(init_times)
                        x = np.linspace(min(init_times), max(init_times), 100)
                        axes2.plot(x, stats.norm.pdf(x, mu, std), "r-", lw=2, label=f"Normal(μ={mu:.1f}, σ={std:.1f})")
                        axes2.legend()
                        plot_path2 = os.path.join(self.output_dir, "msf_ready_distribution.png")
                        fig2.savefig(plot_path2, dpi=150)
                        plt.close()
                        print(f"  Distribution plot saved: {plot_path2}")
            except Exception as e:
                print(f"  Warning: Could not generate distribution plot: {e}")


def main():
    parser = argparse.ArgumentParser(description="Analyze localization init test results")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file with test results")
    parser.add_argument("--output", "-o", default="./analysis", help="Output directory")
    parser.add_argument("--format", "-f", choices=["markdown", "html", "both"], default="both")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating plots")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input) as f:
        results = json.load(f)

    print(f"\nLoaded {len(results)} test results from {args.input}")

    analyzer = TestResultsAnalyzer(results, args.output)

    if args.format in ["markdown", "both"]:
        md_path = analyzer.save_report("markdown")
        print(f"\nMarkdown report: {md_path}")
        print("\n" + analyzer._generate_markdown_report())

    if args.format in ["html", "both"]:
        html_path = analyzer.save_report("html")
        print(f"\nHTML report: {html_path}")

    stats_path = analyzer.save_statistics()
    print(f"Statistics: {stats_path}")

    if not args.no_plot:
        print("\nGenerating plots...")
        analyzer.plot_results()

    print(f"\nAnalysis complete. Output directory: {args.output}")


if __name__ == "__main__":
    main()
