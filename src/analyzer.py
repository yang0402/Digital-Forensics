# -*- coding: utf-8 -*-
import json
import time
from typing import List, Dict, Any
from tqdm import tqdm

class ForensicAnalyzer:
    """电子取证数据分析类"""
    
    def __init__(self, config: Dict, data_processor, api_client):
        """
        初始化分析器
        
        Args:
            config: 配置字典
            data_processor: 数据处理器实例
            api_client: API客户端实例
        """
        # 保存配置和依赖项
        self.config = config
        self.data_processor = data_processor
        self.api_client = api_client
        
        # 从配置中获取处理设置
        self.batch_size = config['processing']['batch_size']
        self.api_delay = config['processing']['api_delay']
    
    def batch_process_data(self, data: List[Dict]) -> List[Dict]:
        """
        批量处理数据
        
        Args:
            data: 数据列表
            
        Returns:
            处理结果列表
        """
        results = []
        
        # 使用tqdm显示进度条
        for i in tqdm(range(0, len(data), self.batch_size), desc="处理数据批次"):
            # 获取当前批次的数据
            batch = data[i:i+self.batch_size]
            
            batch_results = []
            for item in batch:
                # 提取文本特征
                text_features = self.data_processor.extract_text_features(item)
                
                # 调用API进行分类
                result = self.api_client.classify_data(item, text_features)
                batch_results.append(result)
                
                # 添加延迟以避免API限制
                time.sleep(self.api_delay)
            
            # 将批次结果添加到总结果中
            results.extend(batch_results)
            
            # 保存中间结果
            self.data_processor.save_results(
                batch_results, 
                f"interim_results_batch_{i//self.batch_size}.json"
            )
        
        return results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """
        分析处理结果
        
        Args:
            results: 处理结果列表
            
        Returns:
            分析结果
        """
        # 提取有效的分类结果
        valid_results = [r for r in results if "classification" in r]
        
        # 统计各类别数量
        categories = {}
        for result in valid_results:
            category = result["classification"].get("category", "未知")
            categories[category] = categories.get(category, 0) + 1
        
        # 统计各证据价值等级
        evidence_values = {}
        for result in valid_results:
            value = result["classification"].get("evidence_value", "未知")
            evidence_values[value] = evidence_values.get(value, 0) + 1
        
        # 按相关性得分排序
        sorted_by_relevance = sorted(
            valid_results, 
            key=lambda x: x["classification"].get("relevance", 0), 
            reverse=True
        )
        
        # 提取高价值证据
        high_value_evidence = [
            r for r in valid_results 
            if r["classification"].get("evidence_value") == "高"
        ]
        
        # 返回分析结果
        return {
            "total_processed": len(results),
            "valid_results": len(valid_results),
            "category_distribution": categories,
            "evidence_value_distribution": evidence_values,
            "top_relevant_items": [r["data_id"] for r in sorted_by_relevance[:10]],
            "high_value_evidence_count": len(high_value_evidence)
        }
    
    def filter_high_value_evidence(self, results: List[Dict]) -> List[Dict]:
        """
        筛选高价值证据
        
        Args:
            results: 处理结果列表
            
        Returns:
            高价值证据列表
        """
        # 筛选条件：高证据价值或高相关性（8分以上）
        high_value = [
            r for r in results 
            if ("classification" in r and 
                (r["classification"].get("evidence_value") == "高" or 
                r["classification"].get("relevance", 0) >= 8))
        ]
        
        return high_value

