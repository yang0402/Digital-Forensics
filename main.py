# -*- coding: utf-8 -*-
"""
电子数据取证自动分类与筛选系统
使用DeepSeek API实现高价值证据的自动识别与提取
"""

import os
import json
import argparse
from src.data_processor import ForensicDataProcessor
from src.api_client import DeepSeekClient
from src.analyzer import ForensicAnalyzer
from src.report_generator import ReportGenerator

# 首先导入必要的库
import matplotlib.pyplot as plt
import numpy as np
# 然后立即设置matplotlib的字体配置
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def load_config(config_path: str = "config/config.json") -> dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='电子数据取证自动分类与筛选系统')
    parser.add_argument('--config', default='config/config.json', help='配置文件路径')
    parser.add_argument('--input', required=True, help='输入数据文件名')
    parser.add_argument('--sample', type=int, default=0, help='样本大小，0表示处理所有数据')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 初始化各个模块
    data_processor = ForensicDataProcessor(config)
    api_client = DeepSeekClient(config)
    analyzer = ForensicAnalyzer(config, data_processor, api_client)
    report_generator = ReportGenerator(config)
    
    # 加载数据
    print("正在加载数据...")
    forensic_data = data_processor.load_data(args.input)
    
    # 如果指定了样本大小，进行抽样
    if args.sample > 0 and args.sample < len(forensic_data):
        print(f"正在从 {len(forensic_data)} 条记录中抽取 {args.sample} 条进行处理...")
        forensic_data = data_processor.sample_data(forensic_data, args.sample)
    
    # 批量处理数据
    print("开始处理数据...")
    results = analyzer.batch_process_data(forensic_data)
    
    # 保存完整结果
    results_file = "classification_results.json"
    data_processor.save_results(results, results_file)
    
    # 分析结果
    print("分析处理结果...")
    analysis = analyzer.analyze_results(results)
    print("\n结果分析:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # 保存分析结果
    data_processor.save_results(analysis, "analysis_summary.json")
    
    # 筛选高价值证据
    print("筛选高价值证据...")
    high_value_evidence = analyzer.filter_high_value_evidence(results)
    data_processor.save_results(high_value_evidence, "high_value_evidence.json")
    print(f"\n已识别 {len(high_value_evidence)} 条高价值证据项")
    
    # 创建报告
    print("生成证据报告...")
    report_path = report_generator.create_html_report(high_value_evidence, "evidence_report.html")
    
    # 创建图表
    chart_path = report_generator.create_summary_charts(analysis, "evidence_charts.png")
    
    print("\n处理完成!")
    print(f"- 完整结果: {os.path.join(config['data']['results_path'], results_file)}")
    print(f"- 证据报告: {report_path}")
    print(f"- 分析图表: {chart_path}")

if __name__ == "__main__":
    main()
