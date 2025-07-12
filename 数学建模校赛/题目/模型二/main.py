import os
import pandas as pd
import numpy as np
import codecs

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

def analyze_problematic_file(file_path):
    """分析无法正常读取的文件，尝试识别其编码"""
    print(f"\n正在分析问题文件: {os.path.basename(file_path)}")
    
    # 尝试更多编码
    extended_encodings = ['gbk', 'gb18030', 'utf-8', 'utf-8-sig', 'gb2312', 'big5', 'cp936', 'latin1', 'iso-8859-1']
    
    # 尝试读取文件的二进制数据
    with open(file_path, 'rb') as f:
        raw_data = f.read(200)  # 读取前200字节
    
    print("文件头字节 (十六进制):")
    hex_data = ' '.join(f'{byte:02x}' for byte in raw_data[:30])  # 显示前30个字节
    print(hex_data)
    
    # 尝试安装并使用chardet库来检测编码
    try:
        import chardet
        detection = chardet.detect(raw_data)
        print(f"检测到可能的编码: {detection}")
    except ImportError:
        print("未安装chardet库，无法自动检测编码")
    
    # 尝试更多编码读取文件
    print("\n尝试使用不同编码读取文件的前几行:")
    for encoding in extended_encodings:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                lines = [f.readline() for _ in range(3)]
                print(f"\n使用 {encoding} 编码读取结果:")
                for line in lines:
                    print(f"  {line.strip()}")
            
            # 尝试读取为CSV
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=3)
                print(f"\n成功使用 {encoding} 编码作为CSV读取。列名: {list(df.columns)}")
                return encoding  # 返回可能有效的编码
            except Exception as e:
                print(f"使用 {encoding} 作为CSV读取失败: {str(e)}")
                
        except UnicodeDecodeError as e:
            print(f"使用 {encoding} 读取失败: {str(e)}")
        except Exception as e:
            print(f"使用 {encoding} 出现其他错误: {str(e)}")
    
    return None  # 如果所有尝试都失败

def analyze_city_scores():
    # 定义数据目录路径
    data_dir = "data"
    city_files = os.listdir(data_dir)
    
    # 初始化变量
    max_score = 0  # 最高评分
    cities_bs_count = {}  # 存储每个城市拥有最高评分景点的数量
    total_bs_count = 0  # 全国最高评分景点总数
    problematic_files = []  # 存储无法处理的文件
    
    # 尝试多种编码格式
    encodings = ['gbk', 'gb18030', 'utf-8', 'gb2312']
    
    # 读取一个样本文件来检查列名
    sample_file = None
    for city_file in city_files:
        if city_file.endswith('.csv'):
            sample_file = os.path.join(data_dir, city_file)
            break
    
    if sample_file:
        try:
            sample_df = read_csv_with_encoding_fix(sample_file)
            print(f"成功读取样本文件")
            print(f"列名: {list(sample_df.columns)}")
        except Exception as e:
            print(f"读取样本文件失败: {e}")
    
    # 确认评分列名
    score_column = None
    if 'sample_df' in locals() and not sample_df.empty:
        for col in sample_df.columns:
            if '评分' in col or 'score' in str(col).lower():
                score_column = col
                print(f"找到评分列: {score_column}")
                break
    
    if not score_column:
        print("警告: 未找到评分列，将使用默认列名'评分'")
        score_column = "评分"
    
    # 第一次遍历：找出最高评分
    print("正在查找全国最高评分...")
    for city_file in city_files:
        if not city_file.endswith('.csv'):
            continue
            
        file_path = os.path.join(data_dir, city_file)
        try:
            # 使用我们的编码修复函数读取
            df = read_csv_with_encoding_fix(file_path)
            
            if score_column in df.columns:
                # 确保评分列是数值型
                df[score_column] = pd.to_numeric(df[score_column], errors='coerce')
                city_max_score = df[score_column].max()
                if pd.notna(city_max_score):  # 确保不是NaN
                    max_score = max(max_score, city_max_score)
                    print(f"城市 {city_file} 最高评分: {city_max_score}")
            else:
                print(f"警告: {city_file} 中未找到评分列 {score_column}")
                # 尝试查找任何可能的评分列
                for col in df.columns:
                    if '评' in col or '分' in col or 'score' in str(col).lower():
                        print(f"  可能的评分列: {col}")
        except Exception as e:
            print(f"处理文件 {city_file} 时出错: {e}")
            problematic_files.append(city_file)
    
    print(f"全国最高评分(BS)为: {max_score}")
    
    # 第二次遍历：统计每个城市拥有最高评分景点的数量
    print("正在统计各城市最高评分景点数量...")
    for city_file in city_files:
        if not city_file.endswith('.csv'):
            continue
            
        # 跳过已知有问题的文件
        if city_file in problematic_files:
            print(f"跳过已知有问题的文件: {city_file}")
            continue
            
        city_name = city_file.replace('.csv', '')
        file_path = os.path.join(data_dir, city_file)
        
        try:
            df = read_csv_with_encoding_fix(file_path)
            
            if score_column in df.columns:
                df[score_column] = pd.to_numeric(df[score_column], errors='coerce')
                bs_count = sum(df[score_column] == max_score)
                if bs_count > 0:
                    cities_bs_count[city_name] = bs_count
                    total_bs_count += bs_count
                    print(f"城市 {city_name} 有 {bs_count} 个最高评分景点")
        except Exception as e:
            print(f"处理文件 {city_file} 时出错: {e}")
    
    # 输出结果
    print(f"全国共有 {total_bs_count} 个景点获得最高评分(BS): {max_score}")
    
    # 按BS景点数量排序，找出前10个城市
    top_cities = sorted(cities_bs_count.items(), key=lambda x: x[1], reverse=True)
    
    print("\n获得最高评分景点数量最多的前10个城市:")
    for i, (city, count) in enumerate(top_cities[:10], 1):
        print(f"{i}. {city}: {count}个最高评分景点")
    
    # 分析有问题的文件
    if problematic_files:
        print(f"\n发现 {len(problematic_files)} 个有问题的文件，将尝试进行更深入分析:")
        for problem_file in problematic_files:
            file_path = os.path.join(data_dir, problem_file)
            successful_encoding = analyze_problematic_file(file_path)
            if successful_encoding:
                print(f"找到可能的编码方式: {successful_encoding}")
    
    return max_score, total_bs_count, top_cities

if __name__ == "__main__":
    analyze_city_scores()