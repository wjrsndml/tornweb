# 将OC系数CSV文件转换为JSON格式
# 读取CSV文件，按oc_name、rank、slot_code分组，并转换为JSON格式

import csv
import json
from collections import defaultdict

def get_base_slot_name(slot_code):
    """获取slot_code的基础名称（去掉#1、#2等后缀）"""
    if '#' in slot_code:
        return slot_code.split('#')[0]
    return slot_code

def normalize_slot_code(slot_code, has_higher_version=False):
    """
    标准化slot_code：
    - 如果以#1结尾：
      - 如果有#2及以上版本，保留#1（如"Picklock#1" -> "Picklock#1"）
      - 如果没有#2及以上版本，去掉#1并去掉空格（如"Bomber#1" -> "Bomber"）
    - 如果以#2或更高结尾，保留完整的slot_code（如"Picklock#2"）
    - 否则保留原样
    """
    if slot_code.endswith('#1'):
        if has_higher_version:
            # 有#2及以上版本，保留#1
            return slot_code
        else:
            # 没有#2及以上版本，去掉#1并去掉空格
            base_name = slot_code[:-2].replace(' ', '')
            return base_name
    return slot_code

def format_json_compact(obj, indent=4, level=0):
    """
    格式化JSON，使数组元素保持紧凑（单行），缩进使用4个空格以匹配原格式
    """
    if isinstance(obj, dict):
        if not obj:
            return '{}'
        items = []
        for key, value in obj.items():
            key_str = json.dumps(key, ensure_ascii=False)
            value_str = format_json_compact(value, indent, level + 1)
            items.append(' ' * (level * indent + indent) + f'{key_str}: {value_str}')
        return '{\n' + ',\n'.join(items) + '\n' + ' ' * (level * indent) + '}'
    elif isinstance(obj, list):
        if not obj:
            return '[]'
        # 检查是否是嵌套数组（三元组数组）
        if obj and isinstance(obj[0], list) and len(obj[0]) == 3:
            # 紧凑格式：每个三元组一行
            items = []
            for item in obj:
                item_str = json.dumps(item, ensure_ascii=False)
                items.append(' ' * (level * indent + indent) + item_str)
            return '[\n' + ',\n'.join(items) + '\n' + ' ' * (level * indent) + ']'
        else:
            # 普通数组，使用标准格式
            items = []
            for item in obj:
                item_str = format_json_compact(item, indent, level + 1)
                items.append(' ' * (level * indent + indent) + item_str)
            return '[\n' + ',\n'.join(items) + '\n' + ' ' * (level * indent) + ']'
    else:
        return json.dumps(obj, ensure_ascii=False)

def convert_csv_to_json(csv_file_path, json_file_path):
    """
    将CSV文件转换为JSON格式
    
    CSV格式：,oc_name,rank,slot_code,pass_rate_min,pass_rate_max,coefficient
    JSON格式：按oc_name -> rank -> slot_code -> [[min, max, coefficient], ...] 组织
    """
    # 第一步：扫描所有数据，找出哪些slot_code有#2及以上的版本
    slot_versions = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))  # (oc_name, rank, base_name) -> {versions}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oc_name = row['oc_name'].strip()
                rank = row['rank'].strip()
                slot_code = row['slot_code'].strip()
                
                # 提取版本号
                base_name = get_base_slot_name(slot_code)
                if '#' in slot_code:
                    try:
                        version = int(slot_code.split('#')[1])
                        slot_versions[oc_name][rank][base_name].add(version)
                    except (ValueError, IndexError):
                        pass
        
        # 确定哪些基础名称有#2及以上的版本
        has_higher_version = defaultdict(lambda: defaultdict(dict))  # (oc_name, rank, base_name) -> bool
        
        for oc_name in slot_versions:
            for rank in slot_versions[oc_name]:
                for base_name, versions in slot_versions[oc_name][rank].items():
                    # 检查是否有#2及以上的版本
                    has_higher = any(v >= 2 for v in versions)
                    has_higher_version[oc_name][rank][base_name] = has_higher
        
        # 第二步：读取数据并标准化slot_code
        result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oc_name = row['oc_name'].strip()
                rank = row['rank'].strip()
                original_slot_code = row['slot_code'].strip()
                pass_rate_min = int(row['pass_rate_min'].strip())
                pass_rate_max = int(row['pass_rate_max'].strip())
                coefficient = float(row['coefficient'].strip())
                
                # 判断是否有#2及以上版本
                base_name = get_base_slot_name(original_slot_code)
                has_higher = has_higher_version.get(oc_name, {}).get(rank, {}).get(base_name, False)
                
                # 标准化slot_code
                slot_code = normalize_slot_code(original_slot_code, has_higher)
                
                # 添加数据到对应位置，区间上下限各加1
                result[oc_name][rank][slot_code].append([
                    pass_rate_min + 1,
                    pass_rate_max + 1,
                    coefficient
                ])
        
        # 对每个slot_code下的数据按pass_rate_min排序（从低到高）
        for oc_name in result:
            for rank in result[oc_name]:
                for slot_code in result[oc_name][rank]:
                    result[oc_name][rank][slot_code].sort(key=lambda x: x[0])
        
        # 转换为普通dict以便JSON序列化
        result_dict = {}
        for oc_name in sorted(result.keys()):
            result_dict[oc_name] = {}
            for rank in sorted(result[oc_name].keys(), key=int):
                result_dict[oc_name][rank] = {}
                for slot_code in sorted(result[oc_name][rank].keys()):
                    result_dict[oc_name][rank][slot_code] = result[oc_name][rank][slot_code]
        
        # 写入JSON文件，使用紧凑格式（缩进4个空格以匹配原格式）
        with open(json_file_path, 'w', encoding='utf-8') as f:
            formatted_json = format_json_compact(result_dict, indent=4)
            f.write(formatted_json)
        
        print(f"转换完成！已生成文件：{json_file_path}")
        print(f"共处理 {len(result_dict)} 个OC任务")
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {csv_file_path}")
    except Exception as e:
        print(f"转换过程中发生错误：{e}")

if __name__ == '__main__':
    csv_file = 'oc系数_daibb摸鱼版v0.3.csv'
    json_file = 'xishu.json'
    convert_csv_to_json(csv_file, json_file)

