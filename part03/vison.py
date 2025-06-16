import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# 修复中文字体显示问题
def setup_chinese_fonts():
    """设置中文字体支持"""
    import matplotlib.font_manager as fm
    
    # 尝试多种中文字体
    chinese_fonts = [
        'SimHei',           # 黑体 (Windows)
        'Microsoft YaHei',  # 微软雅黑 (Windows)
        'PingFang SC',      # 苹方 (macOS)
        'Hiragino Sans GB', # 冬青黑体 (macOS)
        'WenQuanYi Micro Hei', # 文泉驿微米黑 (Linux)
        'Noto Sans CJK SC', # 思源黑体 (Linux)
        'DejaVu Sans'       # 备用字体
    ]
    
    # 获取系统可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 选择第一个可用的中文字体
    selected_font = 'DejaVu Sans'  # 默认字体
    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    print(f"📝 使用字体: {selected_font}")
    
    # 设置matplotlib字体
    plt.rcParams['font.sans-serif'] = [selected_font, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 10
    
    return selected_font

class AnalysisVisualizer:
    """语义分析结果可视化工具"""
    
    def __init__(self, json_file: str):
        """
        初始化可视化工具
        Args:
            json_file: JSON文件路径
        """
        # 设置中文字体
        self.font_name = setup_chinese_fonts()
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 成功加载JSON文件: {json_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ 找不到文件: {json_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ JSON文件格式错误: {str(e)}")
        except Exception as e:
            raise Exception(f"❌ 读取文件时出错: {str(e)}")
        
        # 设置颜色主题
        self.colors = {
            'High Risk': '#FF4444',      # 高风险
            'Medium Risk': '#FF8800',    # 中风险
            'Low Risk': '#FFCC00',       # 低风险
            'No Risk': '#44AA44',        # 无风险
            'Error': '#888888',          # 错误
            'Unknown': '#CCCCCC',        # 未知
            # 中文映射
            '高风险': '#FF4444',
            '中风险': '#FF8800', 
            '低风险': '#FFCC00',
            '无风险': '#44AA44',
            '错误': '#888888',
            '未知': '#CCCCCC'
        }
        
        # 创建输出目录
        self.output_dir = "visualization_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 创建输出目录: {self.output_dir}")

    def create_dashboard(self, save_path: str = None) -> str:
        """创建综合仪表板"""
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(self.output_dir, f"analysis_dashboard_{timestamp}.png")
        
        # 创建大图布局 (3行4列)
        fig = plt.figure(figsize=(20, 15))
        
        # 使用英文标题避免字体问题
        fig.suptitle('Semantic Analysis Dashboard / 语义分析结果仪表板', 
                    fontsize=20, fontweight='bold', y=0.95)
        
        # 1. 风险等级分布饼图
        ax1 = plt.subplot(3, 4, 1)
        self._plot_risk_distribution_pie(ax1)
        
        # 2. 风险等级分布柱状图
        ax2 = plt.subplot(3, 4, 2)
        self._plot_risk_distribution_bar(ax2)
        
        # 3. 置信度分布
        ax3 = plt.subplot(3, 4, 3)
        self._plot_confidence_distribution(ax3)
        
        # 4. 敏感词类别统计
        ax4 = plt.subplot(3, 4, 4)
        self._plot_sensitive_word_categories(ax4)
        
        # 5. 文本风险热力图
        ax5 = plt.subplot(3, 4, (5, 6))
        self._plot_text_risk_heatmap(ax5)
        
        # 6. 敏感词数量分布
        ax6 = plt.subplot(3, 4, 7)
        self._plot_sensitive_word_count(ax6)
        
        # 7. 语义模式统计
        ax7 = plt.subplot(3, 4, 8)
        self._plot_semantic_patterns(ax7)
        
        # 8. 详细文本分析 (占用底部大空间)
        ax8 = plt.subplot(3, 1, 3)
        self._plot_detailed_text_analysis(ax8)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, hspace=0.3, wspace=0.3)
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"📊 仪表板已保存到: {save_path}")
        return save_path

    def _plot_risk_distribution_pie(self, ax):
        """绘制风险等级分布饼图"""
        risk_dist = self.data['summary_statistics']['risk_level_distribution']
        
        # 转换为英文标签
        label_mapping = {
            '高风险': 'High Risk',
            '中风险': 'Medium Risk', 
            '低风险': 'Low Risk',
            '无风险': 'No Risk',
            '错误': 'Error'
        }
        
        labels = []
        sizes = []
        colors = []
        
        for chinese_label, count in risk_dist.items():
            english_label = label_mapping.get(chinese_label, chinese_label)
            labels.append(f"{english_label}\n({chinese_label})")
            sizes.append(count)
            colors.append(self.colors.get(chinese_label, '#CCCCCC'))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct='%1.1f%%', startangle=90,
                                         textprops={'fontsize': 9})
        ax.set_title('Risk Level Distribution', fontsize=12, fontweight='bold')
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

    def _plot_risk_distribution_bar(self, ax):
        """绘制风险等级分布柱状图"""
        risk_dist = self.data['summary_statistics']['risk_level_distribution']
        
        # 转换标签
        label_mapping = {
            '高风险': 'High\nRisk',
            '中风险': 'Medium\nRisk', 
            '低风险': 'Low\nRisk',
            '无风险': 'No\nRisk',
            '错误': 'Error'
        }
        
        labels = []
        values = []
        colors = []
        
        for chinese_label, count in risk_dist.items():
            english_label = label_mapping.get(chinese_label, chinese_label)
            labels.append(english_label)
            values.append(count)
            colors.append(self.colors.get(chinese_label, '#CCCCCC'))
        
        bars = ax.bar(labels, values, color=colors, alpha=0.8, 
                     edgecolor='black', linewidth=1)
        ax.set_title('Risk Level Statistics', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count')
        
        # 在柱子上显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                   f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        if values:
            ax.set_ylim(0, max(values) * 1.2)

    def _plot_confidence_distribution(self, ax):
        """绘制置信度分布"""
        results = self.data['detailed_results']
        confidences = [r.get('confidence_score', 0) for r in results 
                      if r.get('confidence_score', 0) > 0]
        
        if confidences:
            ax.hist(confidences, bins=10, alpha=0.7, color='skyblue', 
                   edgecolor='black', linewidth=1)
            ax.axvline(np.mean(confidences), color='red', linestyle='--', 
                      linewidth=2, label=f'Mean: {np.mean(confidences):.2f}')
            ax.set_title('Confidence Score Distribution', fontsize=12, fontweight='bold')
            ax.set_xlabel('Confidence Score')
            ax.set_ylabel('Frequency')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No Valid Confidence Data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('Confidence Score Distribution', fontsize=12, fontweight='bold')

    def _plot_sensitive_word_categories(self, ax):
        """绘制敏感词类别统计"""
        categories = self.data['summary_statistics']['sensitive_word_categories']
        
        if categories:
            # 限制显示的类别数量，避免标签重叠
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            top_categories = sorted_categories[:8]  # 只显示前8个类别
            
            labels = [item[0] for item in top_categories]
            values = [item[1] for item in top_categories]
            
            # 使用不同颜色
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            bars = ax.barh(labels, values, color=colors, alpha=0.8, 
                          edgecolor='black', linewidth=1)
            ax.set_title('Sensitive Word Categories', fontsize=12, fontweight='bold')
            ax.set_xlabel('Count')
            
            # 在柱子上显示数值
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                       f'{int(width)}', ha='left', va='center', fontweight='bold')
            
            # 调整标签字体大小
            ax.tick_params(axis='y', labelsize=8)
        else:
            ax.text(0.5, 0.5, 'No Sensitive Word Data', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('Sensitive Word Categories', fontsize=12, fontweight='bold')

    def _plot_text_risk_heatmap(self, ax):
        """绘制文本风险热力图"""
        results = self.data['detailed_results']
        
        # 创建数据矩阵
        risk_values = {'无风险': 0, '低风险': 1, '中风险': 2, '高风险': 3, '错误': -1}
        
        # 准备数据
        text_risks = []
        text_labels = []
        
        for i, result in enumerate(results):
            risk = result.get('risk_level', '未知')
            confidence = result.get('confidence_score', 0)
            text_risks.append([risk_values.get(risk, -1), confidence])
            text_labels.append(f'Text{i+1}')
        
        if text_risks:
            data_matrix = np.array(text_risks).T
            
            # 创建热力图
            im = ax.imshow(data_matrix, cmap='RdYlGn_r', aspect='auto')
            
            # 设置标签
            ax.set_xticks(range(len(text_labels)))
            ax.set_xticklabels(text_labels, rotation=45, fontsize=8)
            ax.set_yticks([0, 1])
            ax.set_yticklabels(['Risk Level', 'Confidence'], fontsize=10)
            ax.set_title('Text Risk Heatmap', fontsize=12, fontweight='bold')
            
            # 添加文本注释
            risk_labels = {0: 'Safe', 1: 'Low', 2: 'Med', 3: 'High', -1: 'Err'}
            for i in range(len(text_labels)):
                risk_level = data_matrix[0, i]
                risk_text = risk_labels.get(risk_level, 'Unk')
                ax.text(i, 0, risk_text, ha='center', va='center', 
                       fontsize=8, fontweight='bold')
                ax.text(i, 1, f'{data_matrix[1, i]:.2f}', ha='center', va='center', 
                       fontsize=8, fontweight='bold')

    def _plot_sensitive_word_count(self, ax):
        """绘制每个文本的敏感词数量"""
        results = self.data['detailed_results']
        
        text_indices = []
        word_counts = []
        colors_list = []
        
        for i, result in enumerate(results):
            text_indices.append(f"Text{i+1}")
            word_counts.append(len(result.get('sensitive_words', [])))
            risk_level = result.get('risk_level', '未知')
            colors_list.append(self.colors.get(risk_level, '#CCCCCC'))
        
        bars = ax.bar(text_indices, word_counts, color=colors_list, alpha=0.8, 
                     edgecolor='black', linewidth=1)
        ax.set_title('Sensitive Words per Text', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count')
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        
        # 在柱子上显示数值
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(height)}', ha='center', va='bottom', fontweight='bold')

    def _plot_semantic_patterns(self, ax):
        """绘制语义模式统计"""
        results = self.data['detailed_results']
        
        text_indices = []
        pattern_counts = []
        colors_list = []
        
        for i, result in enumerate(results):
            text_indices.append(f"Text{i+1}")
            pattern_counts.append(len(result.get('semantic_patterns', [])))
            risk_level = result.get('risk_level', '未知')
            colors_list.append(self.colors.get(risk_level, '#CCCCCC'))
        
        bars = ax.bar(text_indices, pattern_counts, color=colors_list, alpha=0.8, 
                     edgecolor='black', linewidth=1)
        ax.set_title('Semantic Patterns per Text', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count')
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        
        # 在柱子上显示数值
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                       f'{int(height)}', ha='center', va='bottom', fontweight='bold')

    def _plot_detailed_text_analysis(self, ax):
        """绘制详细文本分析"""
        results = self.data['detailed_results']
        
        # 清除坐标轴
        ax.set_xlim(0, 10)
        ax.set_ylim(0, len(results))
        ax.axis('off')
        ax.set_title('Detailed Text Analysis', fontsize=14, fontweight='bold', pad=20)
        
        # 风险等级映射
        risk_mapping = {
            '高风险': 'High Risk',
            '中风险': 'Medium Risk',
            '低风险': 'Low Risk',
            '无风险': 'No Risk',
            '错误': 'Error'
        }
        
        for i, result in enumerate(results):
            y_pos = len(results) - i - 1
            
            # 文本背景色
            risk_level = result.get('risk_level', '未知')
            bg_color = self.colors.get(risk_level, '#CCCCCC')
            
            # 绘制背景矩形
            rect = Rectangle((0, y_pos - 0.4), 10, 0.8, 
                            facecolor=bg_color, alpha=0.3, edgecolor='black')
            ax.add_patch(rect)
            
            # 文本信息
            text_content = result.get('original_text', 'N/A')
            if len(text_content) > 60:
                text_content = text_content[:60] + '...'
            
            confidence = result.get('confidence_score', 0)
            sensitive_count = len(result.get('sensitive_words', []))
            risk_english = risk_mapping.get(risk_level, risk_level)
            
            # 显示信息（使用英文避免字体问题）
            info_text = f"Text {i+1}: {text_content}\n"
            info_text += f"Risk: {risk_english} | Confidence: {confidence:.2f} | "
            info_text += f"Sensitive Words: {sensitive_count}"
            
            ax.text(0.1, y_pos, info_text, fontsize=9, va='center', 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    def create_risk_summary_chart(self, save_path: str = None) -> str:
        """创建风险摘要图表"""
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(self.output_dir, f"risk_summary_{timestamp}.png")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Risk Analysis Summary', fontsize=18, fontweight='bold')
        
        # 1. 风险等级饼图
        self._plot_risk_distribution_pie(ax1)
        
        # 2. 置信度箱线图
        results = self.data['detailed_results']
        risk_confidence = {}
        risk_mapping = {
            '高风险': 'High Risk',
            '中风险': 'Medium Risk',
            '低风险': 'Low Risk',
            '无风险': 'No Risk',
            '错误': 'Error'
        }
        
        for result in results:
            risk = result.get('risk_level', '未知')
            conf = result.get('confidence_score', 0)
            if conf > 0:
                risk_english = risk_mapping.get(risk, risk)
                if risk_english not in risk_confidence:
                    risk_confidence[risk_english] = []
                risk_confidence[risk_english].append(conf)
        
        if risk_confidence:
            risks = list(risk_confidence.keys())
            confs = [risk_confidence[risk] for risk in risks]
            colors = [self.colors.get(risk, '#CCCCCC') for risk in risks]
            
            bp = ax2.boxplot(confs, labels=risks, patch_artist=True)
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            ax2.set_title('Confidence Distribution by Risk Level', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Confidence Score')
            ax2.tick_params(axis='x', labelsize=8)
        
        # 3. 敏感词类别
        self._plot_sensitive_word_categories(ax3)
        
        # 4. 统计摘要
        risk_dist = self.data['summary_statistics']['risk_level_distribution']
        total_texts = sum(risk_dist.values())
        
        ax4.text(0.1, 0.9, f"Total Texts: {total_texts}", transform=ax4.transAxes, 
                 fontsize=12, fontweight='bold')
        ax4.text(0.1, 0.8, f"High Risk: {risk_dist.get('高风险', 0)}", 
                 transform=ax4.transAxes, fontsize=11, color='red')
        ax4.text(0.1, 0.7, f"Medium Risk: {risk_dist.get('中风险', 0)}", 
                 transform=ax4.transAxes, fontsize=11, color='orange')
        ax4.text(0.1, 0.6, f"Low Risk: {risk_dist.get('低风险', 0)}", 
                 transform=ax4.transAxes, fontsize=11, color='gold')
        ax4.text(0.1, 0.5, f"No Risk: {risk_dist.get('无风险', 0)}", 
                 transform=ax4.transAxes, fontsize=11, color='green')
        
        avg_conf = self.data['summary_statistics']['average_confidence']
        total_words = self.data['summary_statistics']['total_sensitive_words']
        
        ax4.text(0.1, 0.3, f"Avg Confidence: {avg_conf:.3f}", 
                 transform=ax4.transAxes, fontsize=11)
        ax4.text(0.1, 0.2, f"Total Sensitive Words: {total_words}", 
                 transform=ax4.transAxes, fontsize=11)
        ax4.text(0.1, 0.1, f"Semantic Patterns: {self.data['summary_statistics']['semantic_patterns_count']}", 
                 transform=ax4.transAxes, fontsize=11)
        
        ax4.set_title('Statistics Summary', fontsize=12, fontweight='bold')
        ax4.axis('off')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"📈 风险摘要图表已保存到: {save_path}")
        return save_path

    def create_all_visualizations(self) -> List[str]:
        """创建所有可视化图表"""
        saved_files = []
        
        print("🎨 开始生成可视化图表...")
        
        # 1. 综合仪表板
        dashboard_path = self.create_dashboard()
        saved_files.append(dashboard_path)
        
        # 2. 风险摘要
        summary_path = self.create_risk_summary_chart()
        saved_files.append(summary_path)
        
        print(f"✅ 所有可视化图表已生成完成!")
        print(f"📁 保存位置: {self.output_dir}/")
        
        return saved_files

    def print_file_info(self):
        """打印文件基本信息"""
        print("\n📄 File Information:")
        print(f"  Generated: {self.data['analysis_info']['generated_at']}")
        print(f"  Total Texts: {self.data['analysis_info']['total_texts']}")
        print(f"  Analyzer Version: {self.data['analysis_info']['analyzer_version']}")
        print(f"  API Model: {self.data['analysis_info']['api_model']}")
        
        print("\n📊 Statistics Summary:")
        stats = self.data['summary_statistics']
        print(f"  High Risk Texts: {stats['high_risk_count']}")
        print(f"  Average Confidence: {stats['average_confidence']:.3f}")
        print(f"  Total Sensitive Words: {stats['total_sensitive_words']}")
        print(f"  Semantic Patterns: {stats['semantic_patterns_count']}")
        
        print("\n🚨 Risk Distribution:")
        risk_mapping = {
            '高风险': 'High Risk',
            '中风险': 'Medium Risk',
            '低风险': 'Low Risk',
            '无风险': 'No Risk',
            '错误': 'Error'
        }
        for risk, count in stats['risk_level_distribution'].items():
            english_risk = risk_mapping.get(risk, risk)
            print(f"  {english_risk}: {count}")


# 使用示例
def main():
    # 指定JSON文件路径
    json_file_path = "/home/user1/tengyang/forensic_analyzer/part03/analysis_results/semantic_analysis_results_20250617_013417.json"
    
    try:
        print("🔍 开始处理语义分析结果...")
        
        # 创建可视化器
        visualizer = AnalysisVisualizer(json_file_path)
        
        # 打印文件基本信息
        visualizer.print_file_info()
        
        # 生成所有可视化图表
        saved_files = visualizer.create_all_visualizations()
        
        print("\n🎉 可视化完成!")
        print("Generated Files:")
        for file in saved_files:
            print(f"  📊 {file}")
        
        # 显示当前工作目录下的可视化文件
        current_dir = os.getcwd()
        vis_dir = os.path.join(current_dir, "visualization_output")
        if os.path.exists(vis_dir):
            print(f"\n📁 Visualization files saved in: {vis_dir}")
            files = os.listdir(vis_dir)
            if files:
                print("  Files:")
                for file in files:
                    print(f"    - {file}")
            
    except FileNotFoundError:
        print(f"❌ Error: Cannot find the specified JSON file")
        print(f"Please check if the file path is correct: {json_file_path}")
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        print("Please check file format and content")


if __name__ == "__main__":
    main()