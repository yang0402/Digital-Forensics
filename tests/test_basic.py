# -*- coding: utf-8 -*-
import unittest
import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_processor import ForensicDataProcessor

class TestBasic(unittest.TestCase):
    """基本功能测试类"""
    
    def setUp(self):
        """测试前设置"""
        # 创建测试配置
        self.test_config = {
            "data": {
                "raw_data_path": "tests/test_data/raw/",
                "processed_data_path": "tests/test_data/processed/",
                "results_path": "tests/test_data/results/"
            }
        }
        
        # 确保测试目录存在
        for path in [
            self.test_config["data"]["raw_data_path"],
            self.test_config["data"]["processed_data_path"],
            self.test_config["data"]["results_path"]
        ]:
            os.makedirs(path, exist_ok=True)
        
        # 创建测试数据
        self.test_data = [
            {
                "id": "test001",
                "path": "C:/Test/Documents/",
                "filename": "test_file.txt",
                "timestamps": {
                    "created": "2023-01-01T10:00:00",
                    "modified": "2023-01-02T11:00:00",
                    "accessed": "2023-01-03T12:00:00"
                },
                "size": 1024,
                "file_type": "Text Document",
                "content_preview": "This is a test file content",
                "metadata": {
                    "author": "Test User",
                    "hidden": False
                }
            }
        ]
        
        # 写入测试数据文件
        with open(os.path.join(self.test_config["data"]["raw_data_path"], "test_data.json"), "w") as f:
            json.dump(self.test_data, f)
        
        # 初始化数据处理器
        self.data_processor = ForensicDataProcessor(self.test_config)
    
    def test_load_data(self):
        """测试数据加载功能"""
        # 加载测试数据
        loaded_data = self.data_processor.load_data("test_data.json")
        
        # 验证数据正确加载
        self.assertEqual(len(loaded_data), 1)
        self.assertEqual(loaded_data[0]["id"], "test001")
        self.assertEqual(loaded_data[0]["filename"], "test_file.txt")
    
    def test_extract_text_features(self):
        """测试文本特征提取功能"""
        # 提取特征
        features = self.data_processor.extract_text_features(self.test_data[0])
        
        # 验证特征包含关键信息
        self.assertIn("路径: C:/Test/Documents/", features)
        self.assertIn("文件名: test_file.txt", features)
        self.assertIn("创建时间: 2023-01-01T10:00:00", features)
        self.assertIn("文件类型: Text Document", features)
    
    def test_save_results(self):
        """测试结果保存功能"""
        # 创建测试结果
        test_results = [{"test": "result"}]
        
        # 保存结果
        file_path = self.data_processor.save_results(test_results, "test_result.json")
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(file_path))
        
        # 验证内容正确
        with open(file_path, "r") as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_results)
    
    def tearDown(self):
        """测试后清理"""
        # 这里可以添加清理测试文件的代码
        pass

if __name__ == "__main__":
    unittest.main()
