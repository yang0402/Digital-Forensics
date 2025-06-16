# -*- coding: utf-8 -*-
import json
import time
import requests
import re
from typing import Dict, Any, List

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, config: Dict):
        """
        初始化DeepSeek API客户端
        
        Args:
            config: 配置字典
        """
        # 从配置中获取API设置
        self.api_key = config['api']['api_key']
        self.api_url = config['api']['api_url']
        self.model = config['api']['model']
        self.temperature = config['api']['temperature']
        self.max_tokens = config['api']['max_tokens']
        
        # 设置API请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def classify_data(self, data_item: Dict, text_features: str) -> Dict:
        """
        使用DeepSeek API对数据进行分类
        
        Args:
            data_item: 数据项
            text_features: 提取的文本特征
            
        Returns:
            分类结果
        """
        # 构建系统提示
        system_prompt = """
        你是一个专业的电子数据取证分析专家。你的任务是分析提供的数据，识别并分类与案件相关的高价值证据。
        请以JSON格式返回以下信息：
        1. category: 数据类别 (通信记录/文档文件/媒体文件/系统日志/应用数据/其他)
        2. evidence_value: 证据价值 (高/中/低)
        3. relevance: 与调查相关性 (1-10分)
        4. key_findings: 关键发现列表
        5. action_recommendation: 建议的后续操作
        """
        
        # 构建用户提示
        user_prompt = f"""
        请分析以下电子取证数据，并进行分类和价值评估：
        
        {text_features}
        
        请以JSON格式返回分析结果。不要包含任何额外的解释或前缀。
        """
        
        # 构建API请求负载
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 调用API
        try:
            # 发送POST请求
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取API返回的内容
            content = result["choices"][0]["message"]["content"]
            
            # 尝试解析JSON
            try:
                # 直接解析返回的内容
                classification = json.loads(content)
                return {
                    "data_id": data_item.get("id", ""),
                    "classification": classification,
                    "api_response": {
                        "model": result.get("model", ""),
                        "usage": result.get("usage", {})
                    }
                }
            except json.JSONDecodeError:
                # 如果返回的不是有效JSON，尝试提取JSON部分
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    try:
                        # 提取代码块中的JSON
                        classification = json.loads(json_match.group(1))
                        return {
                            "data_id": data_item.get("id", ""),
                            "classification": classification,
                            "api_response": {
                                "model": result.get("model", ""),
                                "usage": result.get("usage", {})
                            }
                        }
                    except:
                        pass
                
                # 如果仍然无法解析，返回错误
                return {
                    "data_id": data_item.get("id", ""),
                    "error": "无法解析JSON响应",
                    "raw_response": content
                }
                
        except requests.exceptions.RequestException as e:
            # 处理API请求异常
            return {
                "data_id": data_item.get("id", ""),
                "error": f"API请求失败: {str(e)}"
            }
        except Exception as e:
            # 处理其他异常
            return {
                "data_id": data_item.get("id", ""),
                "error": f"意外错误: {str(e)}"
            }
