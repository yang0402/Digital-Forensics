import requests
import json
import hashlib
import os
import time
import sqlite3
from typing import List, Dict, Any
from datetime import datetime

class ImprovedHashAnalyzer:
    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com/v1", 
                 database_path: str = "hash_database.db"):
        """
        初始化改进的哈希分析器
        
        Args:
            api_key: DeepSeek API密钥
            api_base: DeepSeek API基础URL
            database_path: 哈希数据库路径
        """
        self.api_key = api_key
        self.api_base = api_base
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.db_path = database_path
        self._init_database()
    
    def _init_database(self):
        """初始化哈希数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建哈希记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hash_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            file_name TEXT,
            file_size INTEGER,
            md5 TEXT,
            sha1 TEXT,
            sha256 TEXT,
            last_modified TEXT,
            record_time TEXT
        )
        ''')
        
        # 创建基准哈希表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS baseline_hashes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_size INTEGER,
            md5 TEXT,
            sha1 TEXT,
            sha256 TEXT,
            last_modified TEXT,
            baseline_time TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def compute_file_hash(self, file_path: str) -> Dict[str, str]:
        """
        计算文件的多种哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含多种哈希算法结果的字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        hash_md5 = hashlib.md5()
        hash_sha1 = hashlib.sha1()
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                hash_sha1.update(chunk)
                hash_sha256.update(chunk)
                
        return {
            "file_path": os.path.abspath(file_path),
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "md5": hash_md5.hexdigest(),
            "sha1": hash_sha1.hexdigest(),
            "sha256": hash_sha256.hexdigest(),
            "last_modified": time.ctime(os.path.getmtime(file_path))
        }
    
    def create_baseline(self, directory_path: str) -> Dict[str, Any]:
        """
        为目录中的所有文件创建哈希基准
        
        Args:
            directory_path: 目录路径
            
        Returns:
            基准创建结果
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"目录不存在: {directory_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        baseline_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hash_data = []
        created_count = 0
        updated_count = 0
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    hash_info = self.compute_file_hash(file_path)
                    hash_data.append(hash_info)
                    
                    # 检查是否已存在基准
                    cursor.execute("SELECT id FROM baseline_hashes WHERE file_path = ?", 
                                  (hash_info["file_path"],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 更新现有基准
                        cursor.execute('''
                        UPDATE baseline_hashes 
                        SET file_name = ?, file_size = ?, md5 = ?, sha1 = ?, sha256 = ?, 
                            last_modified = ?, baseline_time = ?
                        WHERE file_path = ?
                        ''', (
                            hash_info["file_name"], hash_info["file_size"], 
                            hash_info["md5"], hash_info["sha1"], hash_info["sha256"],
                            hash_info["last_modified"], baseline_time, hash_info["file_path"]
                        ))
                        updated_count += 1
                    else:
                        # 创建新基准
                        cursor.execute('''
                        INSERT INTO baseline_hashes 
                        (file_path, file_name, file_size, md5, sha1, sha256, last_modified, baseline_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            hash_info["file_path"], hash_info["file_name"], hash_info["file_size"],
                            hash_info["md5"], hash_info["sha1"], hash_info["sha256"],
                            hash_info["last_modified"], baseline_time
                        ))
                        created_count += 1
                    
                    # 同时记录到历史记录表
                    cursor.execute('''
                    INSERT INTO hash_records 
                    (file_path, file_name, file_size, md5, sha1, sha256, last_modified, record_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        hash_info["file_path"], hash_info["file_name"], hash_info["file_size"],
                        hash_info["md5"], hash_info["sha1"], hash_info["sha256"],
                        hash_info["last_modified"], baseline_time
                    ))
                    
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "baseline_time": baseline_time,
            "files_processed": len(hash_data),
            "baselines_created": created_count,
            "baselines_updated": updated_count,
            "hash_data": hash_data
        }
    
    def detect_tampering(self, directory_path: str) -> Dict[str, Any]:
        """
        分析目录中所有文件的哈希值，检测可能的篡改
        
        Args:
            directory_path: 目录路径
            
        Returns:
            分析结果
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"目录不存在: {directory_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_hash_data = []
        tampering_detected = []
        new_files = []
        missing_files = []
        
        # 获取基准哈希列表
        cursor.execute("SELECT file_path FROM baseline_hashes")
        baseline_files = {row[0] for row in cursor.fetchall()}
        checked_files = set()
        
        # 检查当前文件
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                checked_files.add(file_path)
                
                try:
                    current_hash = self.compute_file_hash(file_path)
                    current_hash_data.append(current_hash)
                    
                    # 检查是否存在基准哈希
                    if file_path in baseline_files:
                        cursor.execute('''
                        SELECT md5, sha1, sha256, file_size, last_modified 
                        FROM baseline_hashes WHERE file_path = ?
                        ''', (file_path,))
                        baseline = cursor.fetchone()
                        
                        if baseline:
                            baseline_md5, baseline_sha1, baseline_sha256, baseline_size, baseline_modified = baseline
                            
                            # 检测篡改
                            if (current_hash["md5"] != baseline_md5 or 
                                current_hash["sha1"] != baseline_sha1 or 
                                current_hash["sha256"] != baseline_sha256):
                                
                                tampering_detected.append({
                                    "file_path": file_path,
                                    "file_name": current_hash["file_name"],
                                    "current_hash": {
                                        "md5": current_hash["md5"],
                                        "sha1": current_hash["sha1"],
                                        "sha256": current_hash["sha256"]
                                    },
                                    "baseline_hash": {
                                        "md5": baseline_md5,
                                        "sha1": baseline_sha1,
                                        "sha256": baseline_sha256
                                    },
                                    "size_changed": current_hash["file_size"] != baseline_size,
                                    "modification_time": {
                                        "current": current_hash["last_modified"],
                                        "baseline": baseline_modified
                                    }
                                })
                    else:
                        # 新文件
                        new_files.append({
                            "file_path": file_path,
                            "file_name": current_hash["file_name"],
                            "hash": {
                                "md5": current_hash["md5"],
                                "sha1": current_hash["sha1"],
                                "sha256": current_hash["sha256"]
                            }
                        })
                        
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
        
        # 检查丢失的文件
        for baseline_file in baseline_files:
            if baseline_file not in checked_files:
                cursor.execute("SELECT file_name FROM baseline_hashes WHERE file_path = ?", 
                              (baseline_file,))
                file_name = cursor.fetchone()[0]
                missing_files.append({
                    "file_path": baseline_file,
                    "file_name": file_name
                })
        
        # 记录当前哈希到历史记录
        record_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for hash_info in current_hash_data:
            cursor.execute('''
            INSERT INTO hash_records 
            (file_path, file_name, file_size, md5, sha1, sha256, last_modified, record_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hash_info["file_path"], hash_info["file_name"], hash_info["file_size"],
                hash_info["md5"], hash_info["sha1"], hash_info["sha256"],
                hash_info["last_modified"], record_time
            ))
        
        conn.commit()
        
        # 构建分析结果
        analysis_result = {
            "scan_time": record_time,
            "files_scanned": len(current_hash_data),
            "tampering_detected": tampering_detected,
            "new_files": new_files,
            "missing_files": missing_files,
            "hash_data": current_hash_data
        }
        
        # 如果检测到篡改，使用API进行深度分析
        if tampering_detected:
            api_analysis = self._analyze_tampering(analysis_result)
            analysis_result["ai_analysis"] = api_analysis
        
        conn.close()
        return analysis_result
    
    def _analyze_tampering(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用DeepSeek API分析篡改模式
        
        Args:
            detection_result: 篡改检测结果
            
        Returns:
            API返回的分析结果
        """
        endpoint = f"{self.api_base}/chat/completions"
        
        prompt = f"""
        请分析以下文件篡改检测结果，提供专业的安全分析和建议。
        
        检测结果:
        {json.dumps(detection_result, indent=2, ensure_ascii=False)}
        
        请提供以下内容的分析:
        1. 篡改模式分析：识别出的篡改模式和可能的动机
        2. 风险评估：这些篡改可能带来的安全风险
        3. 建议的响应措施：应该如何处理这些被篡改的文件
        4. 防护建议：如何防止未来类似的篡改
        
        请使用纯文本格式输出，不要使用Markdown标记。
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的数字取证和安全分析专家，擅长分析文件篡改模式和安全风险。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                analysis_content = result["choices"][0]["message"]["content"]
                return {
                    "analysis": analysis_content,
                    "api_response": result
                }
            else:
                return {"error": "API未返回有效分析结果", "api_response": result}
                
        except requests.exceptions.RequestException as e:
            print(f"API请求错误: {e}")
            return {"error": str(e)}
    
    def get_file_history(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件的哈希历史记录
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件的哈希历史
        """
        file_path = os.path.abspath(file_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT file_size, md5, sha1, sha256, last_modified, record_time
        FROM hash_records
        WHERE file_path = ?
        ORDER BY record_time
        ''', (file_path,))
        
        records = cursor.fetchall()
        conn.close()
        
        history = []
        for record in records:
            file_size, md5, sha1, sha256, last_modified, record_time = record
            history.append({
                "record_time": record_time,
                "file_size": file_size,
                "md5": md5,
                "sha1": sha1,
                "sha256": sha256,
                "last_modified": last_modified
            })
        
        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "history": history,
            "history_count": len(history)
        }


def main():
    # 替换为你的DeepSeek API密钥
    api_key = "sk-cca4a6b0541a4aef83489d5501813f30"
    
    # 初始化分析器
    analyzer = ImprovedHashAnalyzer(api_key)
    
    # 示例目录
    directory_to_analyze = "/home/user1/tengyang/forensic_analyzer/part02/data"
    
    # #创建基准（首次运行或需要更新基准时）
    # print("创建哈希基准...")
    # baseline_result = analyzer.create_baseline(directory_to_analyze)
    # print(f"基准创建完成: 处理了 {baseline_result['files_processed']} 个文件")
    
    # 检测篡改
    print("检测文件篡改...")
    result = analyzer.detect_tampering(directory_to_analyze)
    
    # 保存结果到JSON文件
    with open("tampering_analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("分析完成，结果已保存到 tampering_analysis_result.json")
    
    # 打印分析摘要
    print("\n分析摘要:")
    print(f"扫描时间: {result['scan_time']}")
    print(f"扫描的文件数: {result['files_scanned']}")
    print(f"检测到篡改的文件数: {len(result['tampering_detected'])}")
    print(f"新文件数: {len(result['new_files'])}")
    print(f"丢失的文件数: {len(result['missing_files'])}")
    
    if result['tampering_detected']:
        print("\n被篡改的文件:")
        for item in result['tampering_detected']:
            print(f"- {item['file_name']}")


if __name__ == "__main__":
    main()
