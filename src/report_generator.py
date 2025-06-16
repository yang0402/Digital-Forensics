# -*- coding: utf-8 -*-
import time
import json
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import os

class ReportGenerator:
    """报告生成类"""
    
    def __init__(self, config: Dict):
        """
        初始化报告生成器
        
        Args:
            config: 配置字典
        """
        # 从配置中获取结果路径
        self.results_path = config['data']['results_path']
    
    def create_html_report(self, evidence_items: List[Dict], output_file: str) -> str:
        """
        创建HTML格式的证据报告
        
        Args:
            evidence_items: 证据项列表
            output_file: 输出文件名
            
        Returns:
            输出文件路径
        """
        # 创建HTML报告头部
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>电子数据取证分析报告</title>
            <style>
                body { 
                    font-family: "Microsoft YaHei", Arial, sans-serif; 
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                h1 { 
                    color: #2c3e50; 
                    text-align: center;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                .summary {
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .evidence-item { 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin-bottom: 15px; 
                    border-radius: 5px; 
                    background-color: #fff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .high-value { border-left: 5px solid #e74c3c; }
                .medium-value { border-left: 5px solid #f39c12; }
                .low-value { border-left: 5px solid #2ecc71; }
                .findings { 
                    margin-top: 10px;
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 3px;
                }
                .recommendation { 
                    font-style: italic; 
                    margin-top: 10px;
                    color: #0d6efd;
                    background-color: #e8f4ff;
                    padding: 8px;
                    border-radius: 3px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    font-size: 0.8em;
                    color: #7f8c8d;
                }
            </style>
        </head>
        <body>
            <h1>电子数据取证分析报告</h1>
            <div class="summary">
                <p><strong>生成时间:</strong> """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</p>
                <p><strong>高价值证据项数量:</strong> """ + str(len(evidence_items)) + """</p>
            </div>
            <h2>证据项列表</h2>
        """
        
        # 添加每个证据项
        for item in evidence_items:
            # 跳过无效的证据项
            if "classification" not in item:
                continue
                
            # 获取分类结果
            classification = item["classification"]
            
            # 根据证据价值设置不同的CSS类
            value = classification.get("evidence_value", "未知")
            if value == "高":
                value_class = "high-value"
            elif value == "中":
                value_class = "medium-value"
            else:
                value_class = "low-value"
            
            # 添加证据项HTML
            html += f"""
            <div class="evidence-item {value_class}">
                <h3>ID: {item["data_id"]}</h3>
                <p><strong>类别:</strong> {classification.get("category", "未知")}</p>
                <p><strong>证据价值:</strong> {classification.get("evidence_value", "未知")}</p>
                <p><strong>相关性评分:</strong> {classification.get("relevance", "未知")}/10</p>
                <div class="findings">
                    <p><strong>关键发现:</strong></p>
                    <ul>
            """
            
            # 添加关键发现
            key_findings = classification.get("key_findings", [])
            if isinstance(key_findings, list):
                for finding in key_findings:
                    html += f"<li>{finding}</li>"
            else:
                html += f"<li>{key_findings}</li>"
                
            html += """
                    </ul>
                </div>
                <p class="recommendation"><strong>建议操作:</strong> """ + classification.get("action_recommendation", "无") + """</p>
            </div>
            """
        
        # 添加报告尾部
        html += """
            <div class="footer">
                <p>本报告由AI辅助电子数据取证系统自动生成</p>
            </div>
        </body>
        </html>
        """
        
        # 构建完整的输出路径
        output_path = os.path.join(self.results_path, output_file)
        
        # 保存HTML报告
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"证据报告已创建: {output_path}")
        return output_path
    
    def create_summary_charts(self, analysis_result: Dict, output_file: str) -> str:
        """
        创建结果分析图表
        
        Args:
            analysis_result: 分析结果
            output_file: 输出文件名
            
        Returns:
            输出文件路径
        """
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 绘制类别分布饼图
        categories = analysis_result.get('category_distribution', {})
        if categories:
            ax1.pie(
                categories.values(), 
                labels=categories.keys(), 
                autopct='%1.1f%%',
                startangle=90
            )
            ax1.set_title('数据类别分布')
        
        # 绘制证据价值分布条形图
        evidence_values = analysis_result.get('evidence_value_distribution', {})
        if evidence_values:
            values = list(evidence_values.keys())
            counts = list(evidence_values.values())
            ax2.bar(values, counts, color=['red', 'orange', 'green'])
            ax2.set_title('证据价值分布')
            ax2.set_ylabel('数量')
        
        # 调整布局
        plt.tight_layout()
        
        # 构建完整的输出路径
        output_path = os.path.join(self.results_path, output_file)
        
        # 保存图表
        plt.savefig(output_path)
        print(f"分析图表已保存: {output_path}")
        
        return output_path
