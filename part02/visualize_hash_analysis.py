import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.gridspec import GridSpec
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
import os

# 确保使用中文字体
try:
    # 尝试找到系统中的中文字体
    chinese_fonts = [f for f in fm.findSystemFonts() if 'chinese' in f.lower() or 
                     'cjk' in f.lower() or 'yahei' in f.lower() or 
                     'simhei' in f.lower() or 'simsun' in f.lower() or 
                     'msyh' in f.lower() or 'pingfang' in f.lower()]
    
    if chinese_fonts:
        plt.rcParams['font.family'] = fm.FontProperties(fname=chinese_fonts[0]).get_name()
    else:
        # 如果找不到中文字体，使用默认无衬线字体
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
except:
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']

# 设置matplotlib可以显示中文
plt.rcParams['axes.unicode_minus'] = False

# 读取JSON数据
def load_tampering_data(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 计算哈希值差异百分比 - 使用逐字符对比法
def calculate_hash_difference_percentage(hash1, hash2):
    if not hash1 or not hash2:
        return 100.0
    
    # 确保两个哈希值长度相同，如果不同则视为完全不同
    if len(hash1) != len(hash2):
        return 100.0
    
    # 计算不同字符的数量
    different_chars = sum(1 for a, b in zip(hash1, hash2) if a != b)
    
    # 计算差异百分比
    return (different_chars / len(hash1)) * 100

# 生成文件篡改检测结果图片
def generate_tampering_analysis_image(data, output_path="tampering_analysis.png"):
    # 创建图像
    plt.figure(figsize=(16, 22))  # 增加图片高度以容纳哈希差异图
    plt.suptitle("文件篡改检测结果分析报告", fontsize=24, y=0.98)
    
    # 创建网格布局
    gs = GridSpec(6, 2, figure=plt.gcf())  # 增加一行用于哈希差异图
    
    # 1. 扫描摘要
    ax_summary = plt.subplot(gs[0, :])
    ax_summary.axis('off')
    scan_time = data['scan_time']
    files_scanned = data['files_scanned']
    tampering_detected = len(data['tampering_detected'])
    new_files = len(data['new_files'])
    missing_files = len(data['missing_files'])
    
    summary_text = f"扫描时间: {scan_time}\n"
    summary_text += f"扫描文件数: {files_scanned}\n"
    summary_text += f"检测到篡改文件: {tampering_detected}\n"
    summary_text += f"新增文件: {new_files}\n"
    summary_text += f"缺失文件: {missing_files}"
    
    ax_summary.text(0.5, 0.5, summary_text, ha='center', va='center', fontsize=14,
                   bbox=dict(boxstyle="round,pad=1", fc="#f0f0f0", ec="gray", alpha=0.8))
    ax_summary.set_title("扫描摘要", fontsize=18)
    
    # 2. 篡改文件详情
    if data['tampering_detected']:
        ax_tamper = plt.subplot(gs[1, :])
        ax_tamper.axis('off')
        
        tampered_file = data['tampering_detected'][0]
        file_path = tampered_file['file_path']
        file_name = tampered_file['file_name']
        current_md5 = tampered_file['current_hash']['md5']
        baseline_md5 = tampered_file['baseline_hash']['md5']
        current_sha1 = tampered_file['current_hash']['sha1']
        baseline_sha1 = tampered_file['baseline_hash']['sha1']
        current_sha256 = tampered_file['current_hash']['sha256']
        baseline_sha256 = tampered_file['baseline_hash']['sha256']
        size_changed = tampered_file['size_changed']
        current_time = tampered_file['modification_time']['current']
        baseline_time = tampered_file['modification_time']['baseline']
        
        tamper_text = f"文件路径: {file_path}\n"
        tamper_text += f"文件名: {file_name}\n"
        tamper_text += f"当前MD5: {current_md5}\n"
        tamper_text += f"基准MD5: {baseline_md5}\n"
        tamper_text += f"当前SHA1: {current_sha1}\n"
        tamper_text += f"基准SHA1: {baseline_sha1}\n"
        tamper_text += f"当前SHA256: {current_sha256}\n"
        tamper_text += f"基准SHA256: {baseline_sha256}\n"
        tamper_text += f"文件大小是否变化: {'是' if size_changed else '否'}\n"
        tamper_text += f"当前修改时间: {current_time}\n"
        tamper_text += f"基准修改时间: {baseline_time}"
        
        ax_tamper.text(0.5, 0.5, tamper_text, ha='center', va='center', fontsize=12,
                      bbox=dict(boxstyle="round,pad=1", fc="#ffe6e6", ec="red", alpha=0.8))
        ax_tamper.set_title("篡改文件详情", fontsize=18)
        
        # 3. 哈希值变化百分比
        ax_hash_diff = plt.subplot(gs[2, :])
        
        # 计算各哈希值的差异百分比
        md5_diff = calculate_hash_difference_percentage(current_md5, baseline_md5)
        sha1_diff = calculate_hash_difference_percentage(current_sha1, baseline_sha1)
        sha256_diff = calculate_hash_difference_percentage(current_sha256, baseline_sha256)
        
        # 绘制哈希值变化百分比条形图
        hash_types = ['MD5', 'SHA1', 'SHA256']
        diff_percentages = [md5_diff, sha1_diff, sha256_diff]
        
        # 添加精确的字符差异数量
        md5_diff_chars = sum(1 for a, b in zip(current_md5, baseline_md5) if a != b)
        sha1_diff_chars = sum(1 for a, b in zip(current_sha1, baseline_sha1) if a != b)
        sha256_diff_chars = sum(1 for a, b in zip(current_sha256, baseline_sha256) if a != b)
        
        # 设置条形图颜色，根据差异百分比调整颜色深浅
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        bars = ax_hash_diff.bar(hash_types, diff_percentages, color=colors)
        
        # 添加数值标签，同时显示百分比和不同字符数
        for i, bar in enumerate(bars):
            height = bar.get_height()
            diff_chars = [md5_diff_chars, sha1_diff_chars, sha256_diff_chars][i]
            total_chars = [len(current_md5), len(current_sha1), len(current_sha256)][i]
            ax_hash_diff.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{height:.2f}%\n({diff_chars}/{total_chars}字符)', 
                            ha='center', va='bottom', fontsize=12)
        
        ax_hash_diff.set_ylim(0, 105)  # 设置y轴范围，留出空间显示标签
        ax_hash_diff.set_ylabel('差异百分比 (%)', fontsize=12)
        ax_hash_diff.set_title('哈希值变化百分比 (逐字符对比)', fontsize=18)
        
        # 添加解释文本
        explanation_text = "注: 差异百分比表示哈希值中不同字符的比例。100%表示完全不同，0%表示完全相同。"
        ax_hash_diff.text(0.5, -0.15, explanation_text, ha='center', va='center', 
                        transform=ax_hash_diff.transAxes, fontsize=10, style='italic')
    
    # 4. AI分析结果
    analysis_text = data['ai_analysis']['analysis']
    
    # 将AI分析分成几个部分
    analysis_parts = analysis_text.split('\n\n')
    
    # 篡改模式分析
    if len(analysis_parts) > 0:
        ax_mode = plt.subplot(gs[3, 0])
        ax_mode.axis('off')
        ax_mode.text(0.5, 0.5, analysis_parts[1], ha='center', va='center', fontsize=10, wrap=True,
                   bbox=dict(boxstyle="round,pad=1", fc="#e6f2ff", ec="blue", alpha=0.8))
        ax_mode.set_title("篡改模式分析", fontsize=16)
    
    # 风险评估
    if len(analysis_parts) > 1:
        ax_risk = plt.subplot(gs[3, 1])
        ax_risk.axis('off')
        ax_risk.text(0.5, 0.5, analysis_parts[2], ha='center', va='center', fontsize=10, wrap=True,
                   bbox=dict(boxstyle="round,pad=1", fc="#fff2e6", ec="orange", alpha=0.8))
        ax_risk.set_title("风险评估", fontsize=16)
    
    # 响应措施
    if len(analysis_parts) > 2:
        ax_response = plt.subplot(gs[4, 0])
        ax_response.axis('off')
        ax_response.text(0.5, 0.5, analysis_parts[3], ha='center', va='center', fontsize=10, wrap=True,
                       bbox=dict(boxstyle="round,pad=1", fc="#e6ffe6", ec="green", alpha=0.8))
        ax_response.set_title("建议的响应措施", fontsize=16)
    
    # 防护建议
    if len(analysis_parts) > 3:
        ax_prevention = plt.subplot(gs[4, 1])
        ax_prevention.axis('off')
        ax_prevention.text(0.5, 0.5, analysis_parts[4], ha='center', va='center', fontsize=10, wrap=True,
                         bbox=dict(boxstyle="round,pad=1", fc="#f2e6ff", ec="purple", alpha=0.8))
        ax_prevention.set_title("防护建议", fontsize=16)
    
    # 补充建议
    if len(analysis_parts) > 4:
        ax_additional = plt.subplot(gs[5, :])
        ax_additional.axis('off')
        ax_additional.text(0.5, 0.5, analysis_parts[5] if len(analysis_parts) > 5 else "无补充建议", 
                         ha='center', va='center', fontsize=10, wrap=True,
                         bbox=dict(boxstyle="round,pad=1", fc="#f5f5f5", ec="gray", alpha=0.8))
        ax_additional.set_title("补充建议", fontsize=16)
    
    # 添加页脚
    plt.figtext(0.5, 0.01, f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
               ha="center", fontsize=10, style='italic')
    
    # 调整布局
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"篡改分析报告已保存为图片: {output_path}")
    return output_path

# 主函数
def main():
    # 指定JSON文件路径
    json_path = "/home/user1/tengyang/forensic_analyzer/part02/tampering_analysis_result.json"
    
    # 如果文件不存在，尝试使用相对路径
    if not os.path.exists(json_path):
        json_path = "tampering_analysis_result.json"
    
    # 输出图片路径
    output_path = "tampering_analysis_report.png"
    
    try:
        # 加载数据
        data = load_tampering_data(json_path)
        
        # 生成图片
        generate_tampering_analysis_image(data, output_path)
        
        print("文件篡改检测结果图片生成成功！")
    except Exception as e:
        print(f"生成图片时出错: {e}")

if __name__ == "__main__":
    main()
