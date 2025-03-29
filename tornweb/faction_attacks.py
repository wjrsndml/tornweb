#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
import json
import argparse
from datetime import datetime

class TornAPI:
    """Torn API客户端类"""
    
    BASE_URL = "https://api.torn.com/v2"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
    
    def _make_request(self, endpoint, params=None):
        """发送API请求并处理响应"""
        if params is None:
            params = {}
        
        params['key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 检查API错误
            if "error" in data:
                raise Exception(f"API错误: {data['error']['code']} - {data['error']['error']}")
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            return None
    
    def get_user(self):
        """获取当前用户信息"""
        endpoint = "user"
        return self._make_request(endpoint)

    def get_faction_members(self, faction_id):
        """获取派系成员信息"""
        endpoint = f"faction/{faction_id}/members"
        return self._make_request(endpoint)
    
    def get_faction_ranked_wars(self, faction_id):
        """获取派系的ranked wars历史"""
        endpoint = f"faction/{faction_id}/rankedwars"
        return self._make_request(endpoint)
    
    def get_faction_attacks(self, from_timestamp=None, limit=1000, sort="ASC"):
        """获取派系的attacksfull数据"""
        endpoint = "faction/attacksfull"
        params = {
            "limit": limit,
            "sort": sort
        }
        
        if from_timestamp:
            params["from"] = from_timestamp
        
        return self._make_request(endpoint, params)

def timestamp_to_datetime(timestamp):
    """将时间戳转换为可读日期时间格式"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def calculate_attack_potential(status, until_timestamp, current_timestamp):
    """
    计算给定时间点下成员可被攻击的次数
    
    参数:
        status: 成员状态
        until_timestamp: 医院出院时间戳
        current_timestamp: 当前时间戳
    
    返回:
        被攻击可能次数
    """
    if status not in ["Okay", "Hospital"]:
        return 0
    
    # 如果是医院状态，且出院时间大于当前时间，则无法被攻击
    if status == "Hospital" and until_timestamp and until_timestamp > current_timestamp:
        return 0
    # 每20分钟可被攻击一次
    # 假设从ranked war开始到当前时间的每20分钟都可以被攻击一次
    attack_interval = 20 * 60  # 20分钟转换为秒
    if status == "Hospital":
        return (current_timestamp - until_timestamp) // attack_interval
    else:
        return (current_timestamp - int(time.time())) // attack_interval

def calculate_average_respect(attacks, member_id, opponent_id):
    """
    计算成员的平均respect损失
    
    参数:
        attacks: 攻击记录列表
        member_id: 成员ID
        is_attacker: 是否为攻击方
    
    返回:
        平均respect值
    """
    respects = []
    
    for attack in attacks:
        respect_gain = float(attack.get("respect_gain", 0))
        
        # 排除异常值
        if respect_gain == 0 or respect_gain > 20:
            continue
        a=attack.get("attacker")
        b=attack.get("defender")
        if str(b.get("id")) == str(member_id):
            if a is not None and str(a.get("faction_id")) == str(opponent_id):
                respects.append(respect_gain)
    
    # 如果没有数据，返回默认值10
    if not respects:
        return 10.0
    
    return sum(respects) / len(respects)

def main():
    # 获取用户API密钥
    api_key = "3p5n5mHL7MggDaH7"
    output_file = "faction_attacks.json"
    
    api = TornAPI(api_key)
    
    # 获取用户信息和派系信息
    print("获取用户信息...")
    user_data = api.get_user()
    
    if not user_data:
        print("无法获取用户信息，请检查API密钥是否正确")
        return
    
    # 获取用户当前派系ID
    user_faction_id = user_data.get("faction", {}).get("faction_id")
    if not user_faction_id:
        print("您当前没有加入派系")
        return
    
    print(f"您的派系ID: {user_faction_id}")
    
    # 获取最新的ranked war开始时间戳和对方派系ID
    print(f"获取派系 {user_faction_id} 的ranked wars历史...")
    ranked_wars_data = api.get_faction_ranked_wars(user_faction_id)
    
    if not ranked_wars_data or "rankedwars" not in ranked_wars_data:
        print("未找到ranked wars数据")
        return
    
    # 按开始时间排序，获取最新的ranked war
    ranked_wars = sorted(ranked_wars_data["rankedwars"], key=lambda x: x["start"], reverse=True)
    
    if not ranked_wars:
        print("未找到任何ranked war记录")
        return
    
    latest_ranked_war = ranked_wars[0]
    
    # 检查最新的ranked war是否正在进行中
    if latest_ranked_war.get("winner") is not None:
        print("当前没有正在进行的ranked war")
        return
    
    start_timestamp = latest_ranked_war["start"]
    idlist = [latest_ranked_war["factions"][0]["id"],latest_ranked_war["factions"][1]["id"]]
    opponent_faction_id = idlist[0] if idlist[0] != user_faction_id else idlist[1]
    
    print(f"最新的ranked war开始于: {timestamp_to_datetime(start_timestamp)}")
    print(f"对方派系ID: {opponent_faction_id}")
    
    # 获取双方派系成员
    print("获取我方派系成员...")
    our_faction_members_data = api.get_faction_members(user_faction_id)
    
    print("获取对方派系成员...")
    opponent_faction_members_data = api.get_faction_members(opponent_faction_id)
    
    if not our_faction_members_data or not opponent_faction_members_data:
        print("获取派系成员失败")
        return
    
    our_faction_members = our_faction_members_data.get("members", {})
    opponent_faction_members = opponent_faction_members_data.get("members", {})
    
    print(f"我方派系成员数: {len(our_faction_members)}")
    print(f"对方派系成员数: {len(opponent_faction_members)}")
    
    # 从API获取攻击记录
    print("开始从API获取攻击记录...")
    
    all_attacks = []
    current_timestamp = start_timestamp
    has_more = True
    
    while has_more:
        print(f"获取从 {timestamp_to_datetime(current_timestamp)} 开始的攻击记录...")
        
        # 限制API请求，每秒一条
        time.sleep(1)
        
        response = api.get_faction_attacks(from_timestamp=current_timestamp)
        
        if not response or "attacks" not in response:
            print("获取攻击记录失败")
            break
        
        attacks = list(response["attacks"].values())
        if not attacks:
            print("没有更多攻击记录")
            has_more = False
            break
        
        print(f"获取到 {len(attacks)} 条攻击记录")
        all_attacks.extend(attacks)
        
        # 获取最后一条记录的时间戳作为下一次查询的起始时间
        # 我们需要按攻击开始时间排序，所以使用start时间
        last_attack_timestamp = max([int(attack["started"]) for attack in attacks])
        
        # 如果最后一条记录的时间戳没有变化，说明没有更多数据了
        if last_attack_timestamp <= current_timestamp:
            print("没有更多新的攻击记录")
            has_more = False
        else:
            current_timestamp = last_attack_timestamp
            print(f"下一次查询的起始时间为: {timestamp_to_datetime(current_timestamp)}")
    
    print(f"总共获取到 {len(all_attacks)} 条攻击记录")
    
    # 将结果保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_attacks, f, indent=2)
    
    print(f"攻击记录已保存到 {output_file}")
    
    # 输入小时数，计算未来某个时间点
    while True:
        try:
            hours_later = float(input("请输入多少小时后(可以是小数)："))
            if hours_later < 0:
                print("请输入大于或等于0的数字")
                continue
            # 当前时间戳加上用户输入的小时数（转换为秒）
            current_time = int(time.time())
            check_timestamp = current_time + int(hours_later * 3600)
            print(f"将计算 {timestamp_to_datetime(check_timestamp)} 的攻击情况")
            break
        except ValueError:
            print("请输入有效的数字")
    
    # 计算每个成员的被攻击次数和平均丢分
    our_faction_attack_counts = {}
    opponent_faction_attack_counts = {}
    our_faction_avg_respect = {}
    opponent_faction_avg_respect = {}
    
    # 计算我方成员的被攻击次数和平均丢分
    print("\n计算我方成员的被攻击次数和平均丢分:")
    our_faction_total_loss = 0
    
    for iter1 in our_faction_members:
        member_id = iter1['id']
        member_data = iter1
        status = member_data.get("status", {}).get("state", "")
        until_timestamp = member_data.get("status", {}).get("until")
        
        attack_count = calculate_attack_potential(status, until_timestamp, check_timestamp)
        our_faction_attack_counts[member_id] = attack_count
        
        avg_respect = calculate_average_respect(all_attacks, member_id,opponent_id=opponent_faction_id)
        our_faction_avg_respect[member_id] = avg_respect
        
        loss = attack_count * avg_respect
        our_faction_total_loss += loss
        
        print(f"成员: {member_data.get('name')}, 状态: {status}, 可被攻击次数: {attack_count}, 平均丢分: {avg_respect:.2f}, 总丢分: {loss:.2f}")
    
    # 计算对方成员的被攻击次数和平均丢分
    print("\n计算对方成员的被攻击次数和平均丢分:")
    opponent_faction_total_loss = 0
    
    for iter2 in opponent_faction_members:
        member_id = iter2['id']
        member_data = iter2
        status = member_data.get("status", {}).get("state", "")
        until_timestamp = member_data.get("status", {}).get("until")
        
        attack_count = calculate_attack_potential(status, until_timestamp, check_timestamp)
        opponent_faction_attack_counts[member_id] = attack_count
        
        avg_respect = calculate_average_respect(all_attacks, member_id, opponent_id=user_faction_id)
        opponent_faction_avg_respect[member_id] = avg_respect
        
        loss = attack_count * avg_respect
        opponent_faction_total_loss += loss
        
        print(f"成员: {member_data.get('name')}, 状态: {status}, 可被攻击次数: {attack_count}, 平均丢分: {avg_respect:.2f}, 总丢分: {loss:.2f}")
    
    # 打印总结
    print("\n总结:")
    print(f"我方派系总丢分: {our_faction_total_loss:.2f}")
    print(f"对方派系总丢分: {opponent_faction_total_loss:.2f}")
    

if __name__ == "__main__":
    main() 