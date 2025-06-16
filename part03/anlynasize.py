import requests
import json
import re
from typing import List, Dict, Tuple
import logging
from datetime import datetime
import asyncio
import aiohttp
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SemanticAnalyzer:
    """基于DeepSeek API的语义分析器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 预定义的敏感词汇类别
        self.sensitive_categories = {
            "毒品交易": [
                "冰糖", "白面", "大麻", "摇头丸", "K粉", "海洛因",
                "货", "料", "粉", "片", "丸", "草", "叶子",
                "上货", "出货", "拿货", "走货", "清货"
            ],
            "暗语交易": [
                "茶叶", "咖啡", "糖果", "面粉", "调料",
                "见面", "交流", "切磋", "研究", "品尝"
            ],
            "地点代码": [
                "老地方", "那个地方", "熟悉的地方", "安全屋",
                "1号", "2号", "A点", "B点"
            ],
            "时间暗示": [
                "老时间", "平时", "那个时候", "约定时间"
            ]
        }

    def create_analysis_prompt(self, text: str, context: str = "") -> str:
        """创建语义分析提示词"""
        prompt = f"""
你是一个专业的语义分析专家，专门识别文本中的敏感词汇和隐含含义。

任务：分析以下文本，识别可能与违法活动相关的敏感词汇、暗语和上下文线索。

分析重点：
1. 毒品交易相关暗语和代词
2. 交易时间、地点的隐晦表达
3. 数量、价格的暗示性描述
4. 上下文中的异常表达模式
5. 多重含义的词汇在特定语境下的真实意图

待分析文本：
"{text}"

上下文信息：
"{context}"

请按以下JSON格式返回分析结果：
{{
    "risk_level": "高风险/中风险/低风险/无风险",
    "confidence_score": 0.0-1.0,
    "sensitive_words": [
        {{
            "word": "识别的敏感词",
            "category": "词汇类别",
            "context": "上下文片段",
            "interpretation": "可能的真实含义",
            "confidence": 0.0-1.0
        }}
    ],
    "semantic_patterns": [
        {{
            "pattern": "识别的语义模式",
            "description": "模式描述",
            "risk_indicator": "风险指标"
        }}
    ],
    "overall_assessment": "整体评估和建议"
}}
"""
        return prompt

    async def analyze_text_async(self, text: str, context: str = "") -> Dict:
        """异步分析文本语义"""
        try:
            prompt = self.create_analysis_prompt(text, context)
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的语义分析和敏感词识别专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # 尝试解析JSON响应
                        try:
                            # 提取JSON部分
                            json_match = re.search(r'\{.*\}', content, re.DOTALL)
                            if json_match:
                                analysis_result = json.loads(json_match.group())
                                return analysis_result
                            else:
                                return self._create_fallback_result(content)
                        except json.JSONDecodeError:
                            return self._create_fallback_result(content)
                    else:
                        logger.error(f"API请求失败: {response.status}")
                        return self._create_error_result(f"API请求失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"分析过程中出现错误: {str(e)}")
            return self._create_error_result(str(e))

    def analyze_text(self, text: str, context: str = "") -> Dict:
        """同步分析文本语义"""
        try:
            prompt = self.create_analysis_prompt(text, context)
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的语义分析和敏感词识别专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 尝试解析JSON响应
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis_result = json.loads(json_match.group())
                        return analysis_result
                    else:
                        return self._create_fallback_result(content)
                except json.JSONDecodeError:
                    return self._create_fallback_result(content)
            else:
                logger.error(f"API请求失败: {response.status_code}")
                return self._create_error_result(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"分析过程中出现错误: {str(e)}")
            return self._create_error_result(str(e))

    def _create_fallback_result(self, content: str) -> Dict:
        """创建备用结果"""
        return {
            "risk_level": "未知",
            "confidence_score": 0.0,
            "sensitive_words": [],
            "semantic_patterns": [],
            "overall_assessment": content,
            "error": "JSON解析失败，返回原始内容"
        }

    def _create_error_result(self, error_msg: str) -> Dict:
        """创建错误结果"""
        return {
            "risk_level": "错误",
            "confidence_score": 0.0,
            "sensitive_words": [],
            "semantic_patterns": [],
            "overall_assessment": f"分析失败: {error_msg}",
            "error": error_msg
        }

    def batch_analyze(self, texts: List[str], contexts: List[str] = None) -> List[Dict]:
        """批量分析文本"""
        if contexts is None:
            contexts = [""] * len(texts)
        
        results = []
        for i, text in enumerate(texts):
            context = contexts[i] if i < len(contexts) else ""
            result = self.analyze_text(text, context)
            result['text_index'] = i
            result['original_text'] = text
            results.append(result)
            
        return results

    async def batch_analyze_async(self, texts: List[str], contexts: List[str] = None) -> List[Dict]:
        """异步批量分析文本"""
        if contexts is None:
            contexts = [""] * len(texts)
        
        tasks = []
        for i, text in enumerate(texts):
            context = contexts[i] if i < len(contexts) else ""
            task = self.analyze_text_async(text, context)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 添加索引和原始文本
        for i, result in enumerate(results):
            result['text_index'] = i
            result['original_text'] = texts[i]
            
        return results

    def generate_report(self, analysis_results: List[Dict]) -> str:
        """生成分析报告"""
        report = []
        report.append("="*60)
        report.append("语义分析报告")
        report.append("="*60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"分析文本数量: {len(analysis_results)}")
        report.append("")
        
        # 统计风险等级
        risk_stats = {}
        high_risk_texts = []
        
        for result in analysis_results:
            risk_level = result.get('risk_level', '未知')
            risk_stats[risk_level] = risk_stats.get(risk_level, 0) + 1
            
            if risk_level == '高风险':
                high_risk_texts.append(result)
        
        report.append("风险等级统计:")
        for risk, count in risk_stats.items():
            report.append(f"  {risk}: {count}条")
        report.append("")
        
        # 详细分析高风险文本
        if high_risk_texts:
            report.append("高风险文本详细分析:")
            report.append("-" * 40)
            
            for i, result in enumerate(high_risk_texts, 1):
                report.append(f"\n{i}. 文本内容: {result.get('original_text', 'N/A')}")
                report.append(f"   风险等级: {result.get('risk_level', 'N/A')}")
                report.append(f"   置信度: {result.get('confidence_score', 0):.2f}")
                
                sensitive_words = result.get('sensitive_words', [])
                if sensitive_words:
                    report.append("   识别的敏感词汇:")
                    for word_info in sensitive_words:
                        report.append(f"     - {word_info.get('word', 'N/A')} "
                                    f"({word_info.get('category', 'N/A')}) "
                                    f"置信度: {word_info.get('confidence', 0):.2f}")
                        report.append(f"       解释: {word_info.get('interpretation', 'N/A')}")
                
                patterns = result.get('semantic_patterns', [])
                if patterns:
                    report.append("   语义模式:")
                    for pattern in patterns:
                        report.append(f"     - {pattern.get('pattern', 'N/A')}: "
                                    f"{pattern.get('description', 'N/A')}")
                
                report.append(f"   整体评估: {result.get('overall_assessment', 'N/A')}")
        
        return "\n".join(report)

    def save_results_to_json(self, analysis_results: List[Dict], filename: str = None) -> str:
        """保存分析结果到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"semantic_analysis_results_{timestamp}.json"
        
        # 创建输出目录
        output_dir = "analysis_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # 准备保存的数据结构
        output_data = {
            "analysis_info": {
                "generated_at": datetime.now().isoformat(),
                "total_texts": len(analysis_results),
                "analyzer_version": "1.0",
                "api_model": "deepseek-chat"
            },
            "summary_statistics": self._generate_summary_stats(analysis_results),
            "detailed_results": analysis_results
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            return None

    def _generate_summary_stats(self, analysis_results: List[Dict]) -> Dict:
        """生成汇总统计信息"""
        stats = {
            "risk_level_distribution": {},
            "high_risk_count": 0,
            "average_confidence": 0.0,
            "total_sensitive_words": 0,
            "sensitive_word_categories": {},
            "semantic_patterns_count": 0
        }
        
        total_confidence = 0.0
        valid_confidence_count = 0
        
        for result in analysis_results:
            # 风险等级统计
            risk_level = result.get('risk_level', '未知')
            stats["risk_level_distribution"][risk_level] = \
                stats["risk_level_distribution"].get(risk_level, 0) + 1
            
            if risk_level == '高风险':
                stats["high_risk_count"] += 1
            
            # 置信度统计
            confidence = result.get('confidence_score', 0)
            if isinstance(confidence, (int, float)) and confidence > 0:
                total_confidence += confidence
                valid_confidence_count += 1
            
            # 敏感词统计
            sensitive_words = result.get('sensitive_words', [])
            stats["total_sensitive_words"] += len(sensitive_words)
            
            for word_info in sensitive_words:
                category = word_info.get('category', '未分类')
                stats["sensitive_word_categories"][category] = \
                    stats["sensitive_word_categories"].get(category, 0) + 1
            
            # 语义模式统计
            patterns = result.get('semantic_patterns', [])
            stats["semantic_patterns_count"] += len(patterns)
        
        # 计算平均置信度
        if valid_confidence_count > 0:
            stats["average_confidence"] = total_confidence / valid_confidence_count
        
        return stats


class CaseAnalysisSystem:
    """案件分析系统"""
    
    def __init__(self, api_key: str):
        self.analyzer = SemanticAnalyzer(api_key)
        self.case_database = []
    
    def add_evidence_text(self, text: str, source: str, metadata: Dict = None):
        """添加证据文本"""
        evidence = {
            "id": len(self.case_database),
            "text": text,
            "source": source,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "analysis_result": None
        }
        self.case_database.append(evidence)
        return evidence["id"]
    
    def analyze_evidence(self, evidence_id: int) -> Dict:
        """分析特定证据"""
        if evidence_id >= len(self.case_database):
            return {"error": "证据ID不存在"}
        
        evidence = self.case_database[evidence_id]
        context = f"来源: {evidence['source']}"
        
        analysis_result = self.analyzer.analyze_text(evidence["text"], context)
        evidence["analysis_result"] = analysis_result
        
        return analysis_result
    
    def analyze_all_evidence(self) -> List[Dict]:
        """分析所有证据"""
        texts = [evidence["text"] for evidence in self.case_database]
        contexts = [f"来源: {evidence['source']}" for evidence in self.case_database]
        
        results = self.analyzer.batch_analyze(texts, contexts)
        
        # 更新数据库中的分析结果
        for i, result in enumerate(results):
            self.case_database[i]["analysis_result"] = result
        
        return results
    
    def get_high_risk_evidence(self) -> List[Dict]:
        """获取高风险证据"""
        high_risk_evidence = []
        for evidence in self.case_database:
            if evidence.get("analysis_result"):
                risk_level = evidence["analysis_result"].get("risk_level")
                if risk_level == "高风险":
                    high_risk_evidence.append(evidence)
        return high_risk_evidence
    
    def generate_case_report(self) -> str:
        """生成案件报告"""
        if not self.case_database:
            return "没有证据数据"
        
        # 确保所有证据都已分析
        unanalyzed = [e for e in self.case_database if not e.get("analysis_result")]
        if unanalyzed:
            logger.info(f"发现{len(unanalyzed)}条未分析证据，正在分析...")
            self.analyze_all_evidence()
        
        analysis_results = [e["analysis_result"] for e in self.case_database]
        return self.analyzer.generate_report(analysis_results)
    
    def save_case_to_json(self, filename: str = None) -> str:
        """保存案件分析结果到JSON文件"""
        if not self.case_database:
            logger.warning("没有证据数据可保存")
            return None
        
        # 确保所有证据都已分析
        unanalyzed = [e for e in self.case_database if not e.get("analysis_result")]
        if unanalyzed:
            logger.info(f"发现{len(unanalyzed)}条未分析证据，正在分析...")
            self.analyze_all_evidence()
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"case_analysis_{timestamp}.json"
        
        # 创建输出目录
        output_dir = "case_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        # 准备完整的案件数据
        case_data = {
            "case_info": {
                "created_at": datetime.now().isoformat(),
                "total_evidence": len(self.case_database),
                "high_risk_evidence_count": len(self.get_high_risk_evidence()),
                "analysis_version": "1.0"
            },
            "evidence_database": self.case_database,
            "summary_report": self.generate_case_report(),
            "analysis_summary": self.analyzer._generate_summary_stats(
                [e["analysis_result"] for e in self.case_database if e.get("analysis_result")]
            )
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"案件分析结果已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存案件JSON文件失败: {str(e)}")
            return None


# 使用示例
def main():
    # 初始化系统（需要替换为实际的API密钥）
    API_KEY = "sk-cca4a6b0541a4aef83489d5501813f30"
    
    try:
        # 创建案件分析系统
        case_system = CaseAnalysisSystem(API_KEY)
        
        # 添加示例证据文本
        sample_texts = [
            "今天那个冰糖的质量不错，老地方见面交流一下",
            "货已经到了，按老价格，需要的话联系",
            "咖啡豆新到了一批，品质很好，有需要可以品尝",
            "明天老时间老地方，带上那个东西",
            "面粉价格涨了，现在一包要500",
            "这是正常的商务对话，讨论产品销售策略"
        ]
        
        sources = [
            "手机短信", "微信聊天", "QQ聊天", 
            "电话录音", "邮件", "工作文档"
        ]
        
        # 添加证据到系统
        for i, text in enumerate(sample_texts):
            case_system.add_evidence_text(text, sources[i])
        
        print("正在分析证据...")
        
        # 分析所有证据
        results = case_system.analyze_all_evidence()
        
        # 生成并显示报告
        report = case_system.generate_case_report()
        print(report)
        
        # 保存详细分析结果到JSON文件
        json_file = case_system.save_case_to_json()
        if json_file:
            print(f"\n✅ 详细分析结果已保存到JSON文件: {json_file}")
        
        # 也可以单独保存分析结果
        analysis_results = [e["analysis_result"] for e in case_system.case_database]
        simple_json_file = case_system.analyzer.save_results_to_json(analysis_results)
        if simple_json_file:
            print(f"✅ 简化分析结果已保存到: {simple_json_file}")
        
        # 获取高风险证据
        high_risk = case_system.get_high_risk_evidence()
        print(f"\n🚨 发现 {len(high_risk)} 条高风险证据")
        
        # 显示文件保存位置
        print("\n📁 文件保存位置:")
        print("  - case_results/     (完整案件分析)")
        print("  - analysis_results/ (简化分析结果)")
        
    except Exception as e:
        print(f"系统运行错误: {str(e)}")
        print("请检查API密钥是否正确配置")


if __name__ == "__main__":
    main()