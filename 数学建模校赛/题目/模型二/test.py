import pandas as pd
import os
import numpy as np
import random
import sys

# 导入main.py中的修复函数
sys.path.append(".")
try:
    from main import read_csv_with_encoding_fix, fix_encoding
except ImportError:
    # 如果导入失败，在这里重新定义函数
    def fix_encoding(df):
        """修复因编码问题导致的列名和数据内容乱码"""
        # 修复列名
        new_columns = []
        for col in df.columns:
            try:
                # 将latin1编码的字符串转换为字节，再用utf-8解码
                fixed_col = col.encode('latin1').decode('utf-8', errors='replace')
                new_columns.append(fixed_col)
            except Exception:
                new_columns.append(col)
        
        df.columns = new_columns
        
        # 修复数据内容（仅处理字符串类型的列）
        for col in df.columns:
            if df[col].dtype == object:  # 只处理可能包含字符串的列
                try:
                    df[col] = df[col].apply(
                        lambda x: x.encode('latin1').decode('utf-8', errors='replace') 
                        if isinstance(x, str) else x
                    )
                except Exception as e:
                    print(f"修复列 {col} 内容时出错: {e}")
        
        return df

    def read_csv_with_encoding_fix(file_path, encodings=None):
        """尝试多种编码读取CSV文件，并在必要时修复编码问题"""
        if encodings is None:
            encodings = ['utf-8', 'gbk', 'gb18030', 'gb2312']
        
        # 尝试标准编码
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except Exception:
                if encoding == encodings[-1]:
                    # 如果所有标准编码都失败，尝试latin1读取后修复
                    try:
                        df = pd.read_csv(file_path, encoding='latin1')
                        return fix_encoding(df)
                    except Exception as e:
                        print(f"使用latin1读取并修复失败: {e}")
                        raise
        
        # 不应该执行到这里，但为了代码完整性添加
        raise ValueError(f"无法使用任何编码读取文件: {file_path}")

def test_csv_reading():
    """测试CSV读取和编码修复的有效性"""
    
    data_dir = "data"
    city_files = os.listdir(data_dir)
    
    # 测试文件列表：包含已知有问题的文件和随机选择的几个正常文件
    test_files = ["阿拉尔.csv"]  # 已知有问题的文件
    
    # 随机选择5个其他文件进行测试
    other_files = [f for f in city_files if f != "阿拉尔.csv" and f.endswith('.csv')]
    if other_files:
        random_files = random.sample(other_files, min(5, len(other_files)))
        test_files.extend(random_files)
    
    print(f"将测试以下 {len(test_files)} 个文件:")
    for i, file in enumerate(test_files, 1):
        print(f"{i}. {file}")
    
    # 遍历测试文件
    for file_name in test_files:
        file_path = os.path.join(data_dir, file_name)
        print(f"\n{'='*80}")
        print(f"测试文件: {file_name}")
        print(f"{'='*80}")
        
        try:
            # 使用我们的修复函数读取
            df = read_csv_with_encoding_fix(file_path)
            
            # 输出基本信息
            print(f"成功读取！行数: {len(df)}, 列数: {len(df.columns)}")
            
            # 输出列名
            print("\n列名:")
            for i, col in enumerate(df.columns):
                print(f"{i}. {repr(col)}")
            
            # 查找评分列
            score_cols = [col for col in df.columns if '评分' in col or 'score' in str(col).lower()]
            if score_cols:
                score_col = score_cols[0]
                print(f"\n找到评分列: {score_col}")
                
                # 转换为数值
                df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
                
                # 输出评分统计
                print("\n评分统计:")
                print(f"最高评分: {df[score_col].max()}")
                print(f"最低评分: {df[score_col].min()}")
                print(f"平均评分: {df[score_col].mean():.2f}")
                print(f"评分分布: {df[score_col].value_counts().sort_index().to_dict()}")
            else:
                print("\n未找到评分列")
            
            # 输出前3行数据
            print("\n前3行数据:")
            print(df.head(3).to_string(max_colwidth=30))
            
            # 检查是否有缺失值
            missing_values = df.isnull().sum().sum()
            print(f"\n缺失值数量: {missing_values}")
            
            # 随机抽取3个中文列，验证中文是否正确
            text_cols = [col for col in df.columns if df[col].dtype == object]
            if text_cols:
                sample_cols = random.sample(text_cols, min(3, len(text_cols)))
                print("\n随机抽查3个文本列的内容:")
                for col in sample_cols:
                    non_empty_values = df[col].dropna().tolist()
                    if non_empty_values:
                        sample_value = random.choice(non_empty_values)
                        print(f"{col}: {sample_value}")
            
        except Exception as e:
            print(f"读取文件 {file_name} 失败: {str(e)}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_csv_reading()
