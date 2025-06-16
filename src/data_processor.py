# -*- coding: utf-8 -*-
import os
import json
from typing import List, Dict, Any

class ForensicDataProcessor:
    """电子取证数据处理类"""
    
    def __init__(self, config: Dict):
        """
        初始化数据处理器
        
        Args:
            config: 配置字典
        """
        # 从配置中获取数据路径
        self.raw_data_path = config['data']['raw_data_path']
        self.processed_data_path = config['data']['processed_data_path']
        self.results_path = config['data']['results_path']
        
        # 确保目录存在
        for path in [self.raw_data_path, self.processed_data_path, self.results_path]:
            os.makedirs(path, exist_ok=True)
    
    def load_data(self, file_name: str) -> List[Dict]:
        """
        加载电子取证数据
        
        Args:
            file_name: 数据文件名
            
        Returns:
            数据列表
        """
        # 构建完整的文件路径
        file_path = os.path.join(self.raw_data_path, file_name)
        
        # 打开并读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"已加载 {len(data)} 条记录，来自 {file_path}")
        return data
    
    def extract_text_features(self, item: Dict) -> str:
        """
        从数据项中提取文本特征
        
        Args:
            item: 数据项
            
        Returns:
            提取的文本特征
        """
        # 创建一个列表存储所有特征
        features = []
        
        # 提取文件路径
        if 'path' in item:
            features.append(f"路径: {item['path']}")
        
        # 提取文件名
        if 'filename' in item:
            features.append(f"文件名: {item['filename']}")
        
        # 提取时间戳
        if 'timestamps' in item:
            ts = item['timestamps']
            if 'created' in ts:
                features.append(f"创建时间: {ts['created']}")
            if 'modified' in ts:
                features.append(f"修改时间: {ts['modified']}")
            if 'accessed' in ts:
                features.append(f"访问时间: {ts['accessed']}")
        
        # 提取文件大小
        if 'size' in item:
            # 转换为更易读的格式
            size = item['size']
            if size < 1024:
                size_str = f"{size} 字节"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.2f} KB"
            else:
                size_str = f"{size/(1024*1024):.2f} MB"
            features.append(f"文件大小: {size_str}")
        
        # 提取文件类型
        if 'file_type' in item:
            features.append(f"文件类型: {item['file_type']}")
        
        # 提取内容摘要
        if 'content_preview' in item:
            preview = item['content_preview']
            # 如果内容太长，截取一部分
            if len(preview) > 500:
                preview = preview[:500] + "..."
            features.append(f"内容预览: {preview}")
        
        # 提取元数据
        if 'metadata' in item:
            # 将元数据格式化为JSON字符串
            features.append(f"元数据: {json.dumps(item['metadata'], ensure_ascii=False)}")
        
        # 将所有特征合并为一个字符串，每个特征占一行
        return "\n".join(features)
    
    def save_results(self, results: List[Dict], file_name: str) -> str:
        """
        保存处理结果
        
        Args:
            results: 结果列表
            file_name: 文件名
            
        Returns:
            保存的文件路径
        """
        # 构建完整的文件路径
        file_path = os.path.join(self.results_path, file_name)
        
        # 将结果保存为JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"结果已保存至 {file_path}")
        return file_path
    
    def sample_data(self, data: List[Dict], sample_size: int) -> List[Dict]:
        """
        从数据集中抽样
        
        Args:
            data: 完整数据集
            sample_size: 样本大小
            
        Returns:
            抽样后的数据
        """
        # 如果数据量小于样本大小，直接返回全部数据
        if len(data) <= sample_size:
            return data
        
        # 否则随机抽样
        import random
        return random.sample(data, sample_size)
