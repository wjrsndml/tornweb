# 将CC OC系数CSV文件转换为JSON格式
# 读取CSV文件，按oc_name、rank、slot_code分组，并转换为JSON格式

import csv
import json
from collections import defaultdict
import re

def normalize_slot_code(slot_code):
    """
    标准化slot_code：
    - 如果以数字结尾但没有#，则在数字前加#（如"Picklock1" -> "Picklock#1"）
    - 其他情况保持原样
    """
    # 匹配以数字结尾的情况（如 Picklock1, Muscle2 等）
    match = re.match(r'^(.+?)(\d+)$', slot_code)
    if match:
        base_name = match.group(1)
        number = match.group(2)
        return f"{base_name}#{number}"
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
    将CC OC系数CSV文件转换为JSON格式
    
    CSV格式：rank,oc_name,slot_code,pass_rate_min,pass_rate_max,coefficient（无header）
    JSON格式：按oc_name -> rank -> slot_code -> [[min, max, coefficient], ...] 组织
    """
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 6:
                    continue
                
                rank = row[0].strip()
                oc_name = row[1].strip()
                slot_code = normalize_slot_code(row[2].strip())
                pass_rate_min = int(row[3].strip())
                pass_rate_max = int(row[4].strip())
                coefficient = float(row[5].strip())
                
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
    csv_file = 'ccocxishu.csv'
    json_file = 'xishucc.json'
    convert_csv_to_json(csv_file, json_file)
