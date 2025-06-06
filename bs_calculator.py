#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torn City BS (Battle Stats) 预测计算器
基于用户个人数据和算法预测用户的BS值

使用方法：
python bs_calculator.py --user_id <用户ID> --api_key <API密钥>
"""

import requests
import json
import math
import time
import argparse
from datetime import datetime

# BS预测算法常量
BS_CONSTANTS = {
    'L': [2, 2.8, 3.2, 3.2, 3.6, 3.8, 3.7, 4, 4.8, 4.8, 5.2, 5.2, 5.4, 5.8, 5.8, 6, 6.4, 6.6, 6.8, 7, 7, 7, 7, 7.3, 8],
    'W': [200, 500, 1000, 2000, 2750, 3000, 3500, 4000, 6000, 7000, 8000, 11000, 12420, 18000, 18100, 24140, 31260, 36610, 46640, 56520, 67775, 84535, 106305, 100000, float('inf')],
    'E': [5, 5, 5, 5, 5, 5, 10, 10, 10, 10, 10, 10, 25, 25, 25, 25, 25, 25, 25, 50, 50, 50, 50, 50, 50],  # 每个健身房的能量消耗
    'J': [2, 6, 11, 26, 31, 50, 71, 100],
    'K': [100, 5000, 10000, 20000, 30000, 50000],
    'V': [5000000, 50000000, 500000000, 5000000000, 50000000000],
    'B': [2000, 20000, 200000, 2000000, 20000000, 200000000],
    'R': [2500, 25000, 250000, 2500000, 35000000, 250000000],
    'Y': {
        "Absolute beginner": 1, "Beginner": 2, "Inexperienced": 3, "Rookie": 4,
        "Novice": 5, "Below average": 6, "Average": 7, "Reasonable": 8,
        "Above average": 9, "Competent": 10, "Highly competent": 11,
        "Veteran": 12, "Distinguished": 13, "Highly distinguished": 14,
        "Professional": 15, "Star": 16, "Master": 17, "Outstanding": 18,
        "Celebrity": 19, "Supreme": 20, "Idolised": 21, "Champion": 22,
        "Heroic": 23, "Legendary": 24, "Elite": 25, "Invincible": 26
    },
    # 新训练公式的属性特定常数
    'STAT_CONSTANTS': {
        'strength': {'A': 1600, 'B': 1700, 'C': 700},
        'speed': {'A': 1600, 'B': 2000, 'C': 1350}, 
        'dexterity': {'A': 1800, 'B': 1500, 'C': 1000},
        'defense': {'A': 2100, 'B': -600, 'C': 1500}
    }
}

class BSCalculator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.torn.com/v2"
        
    def fetch_api(self, endpoint):
        """发起API请求"""
        url = f"{self.base_url}{endpoint}"
        if '?' in url:
            url += f"&key={self.api_key}"
        else:
            url += f"?key={self.api_key}"
            
        print(f"🌐 API请求: {url.replace(self.api_key, '***')}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                raise Exception(f"Torn API 错误: {data['error']['error']} (代码: {data['error']['code']})")
                
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
    
    def get_user_data(self, user_id):
        """获取用户完整数据"""
        print(f"\n📊 获取用户 {user_id} 的数据...")
        
        # 获取用户基本信息
        profile_data = self.fetch_api(f"/user/{user_id}")
        profile = profile_data.get('profile') or profile_data
        
        # 获取个人统计数据
        stats_data = self.fetch_api(f"/user/{user_id}/personalstats?cat=all")
        personal_stats = stats_data.get('personalstats') or stats_data
        
        print(f"✅ 用户数据获取完成")
        print(f"   - 用户名: {profile.get('name', 'Unknown')}")
        print(f"   - 等级: {profile.get('level', 'Unknown')}")
        print(f"   - 年龄: {profile.get('age', 'Unknown')} 天")
        print(f"   - Rank: {profile.get('rank', 'Unknown')}")
        print(f"   - 净资产: ${profile.get('networth', {}).get('total', 0):,}")
        
        return {
            'profile': profile,
            'personalstats': personal_stats,
            'criminalrecord': personal_stats.get('criminalrecord', {})
        }
    
    def calculate_total_energy(self, profile, stats):
        """计算总能量消耗"""
        print(f"\n⚡ 开始计算总能量消耗...")
        
        now = int(time.time())
        start_timestamp = int(datetime(2011, 11, 22).timestamp())
        
        # 计算捐献者比例
        age = profile.get('age', 100)
        m = min(age, (now - start_timestamp) / 86400)
        donator_days = stats.get('other', {}).get('donator_days', 0)
        donator_percent = min(donator_days / m if m > 0 else 0, 1)
        
        print(f"   - 账户年龄: {age} 天")
        print(f"   - 捐献天数: {donator_days} 天")
        print(f"   - 捐献者比例: {donator_percent:.3f}")
        
        # 估算活跃天数
        y = 480 + 240 * donator_percent
        F = 611255 / y
        last_action = profile.get('last_action', {}).get('timestamp', now)
        a = (now - last_action) / 86400
        age_m = max(1, 21 * (age - a) / 24)
        
        activity_time = stats.get('other', {}).get('activity', {}).get('time', 0)
        travel_time = stats.get('travel', {}).get('time_spent', 0)
        N = 3 * (activity_time / 86400) + (travel_time / 86400)
        
        print(f"   - 每日能量(y): {y:.1f}")
        print(f"   - 活跃度因子(F): {F:.1f}")
        print(f"   - 离线天数: {a:.1f}")
        print(f"   - 活跃时间估算(N): {N:.1f}")
        
        # 药物活跃度计算 (S_drugs)
        drugs = stats.get('drugs', {})
        
        # 使用新的药物能量公式
        exttaken = drugs.get('ecstasy', 0)
        victaken = drugs.get('vicodin', 0) 
        kettaken = drugs.get('ketamine', 0)
        lsdtaken = drugs.get('lsd', 0)
        opitaken = drugs.get('opium', 0)
        pcptaken = drugs.get('pcp', 0)
        shrtaken = drugs.get('shrooms', 0)
        spetaken = drugs.get('speed', 0)
        cantaken = drugs.get('cannabis', 0)
        xantaken = drugs.get('xanax', 0)
        
        drug_energy = (
            75 * exttaken +
            210 * victaken +
            52.5 * kettaken +
            425 * lsdtaken +
            215 * opitaken +
            430 * pcptaken +
            209.5 * shrtaken +
            301 * spetaken +
            300 * cantaken +
            420 * xantaken
        )
        
        S_drugs = drug_energy / 1440
        
        print(f"   - 药物使用详情:")
        print(f"     * Ecstasy: {exttaken}, Vicodin: {victaken}, Ketamine: {kettaken}")
        print(f"     * LSD: {lsdtaken}, Opium: {opitaken}, PCP: {pcptaken}")
        print(f"     * Shrooms: {shrtaken}, Speed: {spetaken}, Cannabis: {cantaken}, Xanax: {xantaken}")
        print(f"   - 药物总能量: {drug_energy:.1f}")
        print(f"   - 药物活跃度(S_drugs): {S_drugs:.1f}")
        
        # 犯罪活跃度计算 (n_crimes)
        criminal_record = stats.get('criminalrecord', {})
        
        # 判断是否存在vandalism (D标志)
        D = criminal_record.get('vandalism', 0) > 0
        
        print(f"   - Vandalism存在: {D}")
        
        # 根据D值计算不同的犯罪系数
        if D:
            c2 = 0.1 * criminal_record.get('theft', 0)
            c3 = criminal_record.get('counterfeiting', 0) 
            c5 = 0.65 * criminal_record.get('theft', 0)
            c8 = criminal_record.get('illicitservices', 0) / 2
            c9 = criminal_record.get('cybercrime', 0)
            c10 = criminal_record.get('illicitservices', 0) / 2
            c11 = criminal_record.get('fraud', 0)
            c12 = 0.25 * criminal_record.get('theft', 0)
        else:
            c2 = criminal_record.get('other', 0)
            c3 = criminal_record.get('selling_illegal_products', 0)
            c5 = criminal_record.get('theft', 0)
            c8 = criminal_record.get('drug_deals', 0)
            c9 = criminal_record.get('computer_crimes', 0)
            c10 = criminal_record.get('murder', 0)
            c11 = criminal_record.get('fraud_crimes', 0)
            c12 = criminal_record.get('auto_theft', 0)
        
        print(f"   - 犯罪系数: c2={c2}, c3={c3}, c5={c5}, c8={c8}")
        print(f"                c9={c9}, c10={c10}, c11={c11}, c12={c12}")
        
        # 计算犯罪能量
        crime_energy = 5 * (
            2 * c2 +
            3 * c3 +
            5 * c5 +
            8 * (c8 / 0.8) +
            9 * (c9 / 0.75) +
            10 * (c10 / 0.75) +
            11 * (c11 / 0.95) +
            12 * (c12 / 0.7)
        )
        
        n_crimes = crime_energy / 1440
        
        print(f"   - 犯罪总能量: {crime_energy:.1f}")
        print(f"   - 犯罪活跃度(n_crimes): {n_crimes:.1f}")
        
        # 修正犯罪活跃度
        if n_crimes < F:
            F_corrected = min(F / n_crimes if n_crimes > 0 else 3, 3)
            n_crimes *= F_corrected
            print(f"   - 犯罪活跃度(修正前): {n_crimes/F_corrected:.1f}")
            print(f"   - 犯罪活跃度修正系数: {F_corrected:.2f}")
        
        print(f"   - 最终犯罪活跃度: {n_crimes:.1f}")
        
        estimate_active_days = min(age_m, max(N, S_drugs, n_crimes))
        print(f"   - 估算活跃天数: {estimate_active_days:.1f}")
        
        # 计算各部分能量
        nature_energy = y * estimate_active_days
        
        item_energy = (
            150 * stats.get('other', {}).get('refills', {}).get('energy', 0) +
            250 * xantaken +
            50 * lsdtaken +
            20 * stats.get('items', {}).get('used', {}).get('energy_drinks', 0) +
            150 * stats.get('items', {}).get('used', {}).get('boosters', 0)
        )
        
        attacking = stats.get('attacking', {}).get('attacks', {})
        expend_energy = (
            25 * (attacking.get('won', 0) + attacking.get('stalemate', 0) + attacking.get('lost', 0)) +
            25 * stats.get('hospital', {}).get('reviving', {}).get('revives', 0) +
            5 * stats.get('items', {}).get('found', {}).get('dump', 0)
        )
        
        total_energy = max(0, nature_energy + item_energy - expend_energy)
        
        print(f"   - 自然能量: {nature_energy:,.0f}")
        print(f"   - 道具能量: {item_energy:,.0f}")
        print(f"   - 消耗能量: {expend_energy:,.0f}")
        print(f"   - 总可用能量: {total_energy:,.0f}")
        
        return total_energy
    
    def calculate_training_gain_old(self, current_stats, happy, gym_level, energy_per_train, stat_type='strength'):
        """
        使用旧版训练公式计算单次训练增益（2022年8月2日之前）
        超过50m时S = 50,000,000（硬上限）
        """
        # 获取属性特定常数
        stat_constants = BS_CONSTANTS['STAT_CONSTANTS'][stat_type]
        A = stat_constants['A']
        B = stat_constants['B']
        
        # S: 旧版硬上限50m
        if current_stats <= 50000000:
            S = current_stats
        else:
            S = 50000000
        
        # H: 当前快乐值
        H = max(0, min(happy, 99999))
        
        # G: 健身房点数
        G = BS_CONSTANTS['L'][gym_level]
        
        # E: 每次训练消耗的能量
        E = energy_per_train
        
        # 旧版公式的各个部分
        ln_term = math.log(1 + H/250)
        rounded_ln = round(ln_term, 4)
        multiplier = round(1 + 0.07 * rounded_ln, 4)
        stat_component = S * multiplier
        
        happy_component = 8 * pow(H, 1.05)
        happy_adjustment = (1 - pow(H/99999, 2)) * A if H < 99999 else 0
        
        base_gain = (stat_component + happy_component + happy_adjustment + B) * (1/200000) * G * E
        
        return max(0, base_gain)
    
    def calculate_training_gain_new(self, current_stats, happy, gym_level, energy_per_train, stat_type='strength'):
        """
        使用新版训练公式计算单次训练增益（2022年8月2日之后）
        超过50m时S = 50,000,000 + (当前属性 - 50,000,000) / (8.77635 * LOG(当前属性))
        """
        # 获取属性特定常数
        stat_constants = BS_CONSTANTS['STAT_CONSTANTS'][stat_type]
        A = stat_constants['A']
        B = stat_constants['B']
        
        # S: 新版公式，超过50m时有对数衰减
        if current_stats <= 50000000:
            S = current_stats
        else:
            S = 50000000 + (current_stats - 50000000) / (8.77635 * math.log(current_stats))
        
        # H: 当前快乐值
        H = max(0, min(happy, 99999))
        
        # G: 健身房点数
        G = BS_CONSTANTS['L'][gym_level]
        
        # E: 每次训练消耗的能量
        E = energy_per_train
        
        # 新版公式的各个部分
        ln_term = math.log(1 + H/250)
        rounded_ln = round(ln_term, 4)
        multiplier = round(1 + 0.07 * rounded_ln, 4)
        stat_component = S * multiplier
        
        happy_component = 8 * pow(H, 1.05)
        happy_adjustment = (1 - pow(H/99999, 2)) * A if H < 99999 else 0
        
        base_gain = (stat_component + happy_component + happy_adjustment + B) * (1/200000) * G * E
        
        return max(0, base_gain)

    def simulate_gym_training(self, total_energy, stats, profile):
        """模拟健身房锻炼（根据账户年龄使用旧版/新版公式）"""
        print(f"\n🏋️ 开始模拟健身房锻炼（旧版+新版公式）...")
        
        # 计算能量分配
        now = int(time.time())
        formula_change_date = int(datetime(2022, 8, 2).timestamp())
        account_age = profile.get('age', 100)
        account_creation_timestamp = now - (account_age * 86400)
        
        if account_creation_timestamp >= formula_change_date:
            # 账户在公式更新后创建，全部使用新版公式
            old_energy = 0
            new_energy = total_energy
            print(f"   - 账户创建于公式更新后，全部使用新版公式")
        else:
            # 账户在公式更新前创建，需要分配能量
            days_before_change = (formula_change_date - account_creation_timestamp) / 86400
            days_after_change = account_age - days_before_change
            
            old_energy_ratio = days_before_change / account_age
            new_energy_ratio = days_after_change / account_age if days_after_change > 0 else 0
            
            old_energy = int(total_energy * old_energy_ratio)
            new_energy = total_energy - old_energy
            
            print(f"   - 账户年龄: {account_age} 天")
            print(f"   - 公式更新前: {days_before_change:.0f} 天 ({old_energy_ratio:.1%})")
            print(f"   - 公式更新后: {days_after_change:.0f} 天 ({new_energy_ratio:.1%})")
            print(f"   - 旧版公式能量: {old_energy:,}")
            print(f"   - 新版公式能量: {new_energy:,}")
        
        # 初始化变量 - 分别跟踪四个属性
        strength_stats = 0
        speed_stats = 0
        dexterity_stats = 0
        defense_stats = 0
        
        current_happy = 5000  # 恒定快乐值
        
        gym_sessions = []
        session_count = 0
        
        # 属性训练顺序
        stat_types = ['strength', 'speed', 'dexterity', 'defense']
        current_stat_index = 0
        
        # 第一阶段：使用旧版公式
        if old_energy > 0:
            print(f"\n   📜 第一阶段：旧版公式训练（{old_energy:,} 能量）")
            remaining_energy = old_energy
            current_gym = 0
            gym_capacity_left = BS_CONSTANTS['W'][0]
            
            while remaining_energy > 0 and current_gym < len(BS_CONSTANTS['L']):
                energy_per_train = BS_CONSTANTS['E'][current_gym]
                gym_dots = BS_CONSTANTS['L'][current_gym]
                
                max_trains_by_energy = remaining_energy // energy_per_train
                max_trains_by_capacity = gym_capacity_left // energy_per_train
                actual_trains = min(max_trains_by_energy, max_trains_by_capacity, 10000)
                
                if actual_trains <= 0:
                    break
                
                total_gain_this_session = 0
                trains_completed = 0
                stat_gains = {'strength': 0, 'speed': 0, 'dexterity': 0, 'defense': 0}
                
                for train in range(int(actual_trains)):
                    if remaining_energy < energy_per_train:
                        break
                    
                    current_stat = stat_types[current_stat_index]
                    
                    if current_stat == 'strength':
                        current_stat_value = strength_stats
                    elif current_stat == 'speed':
                        current_stat_value = speed_stats
                    elif current_stat == 'dexterity':
                        current_stat_value = dexterity_stats
                    else:
                        current_stat_value = defense_stats
                    
                    # 使用旧版公式
                    gain = self.calculate_training_gain_old(
                        current_stat_value,
                        current_happy,
                        current_gym,
                        energy_per_train,
                        current_stat
                    )
                    
                    # 更新对应属性的值
                    if current_stat == 'strength':
                        strength_stats += gain
                    elif current_stat == 'speed':
                        speed_stats += gain
                    elif current_stat == 'dexterity':
                        dexterity_stats += gain
                    else:
                        defense_stats += gain
                    
                    stat_gains[current_stat] += gain
                    total_gain_this_session += gain
                    
                    remaining_energy -= energy_per_train
                    gym_capacity_left -= energy_per_train
                    trains_completed += 1
                    current_stat_index = (current_stat_index + 1) % 4
                
                if trains_completed > 0:
                    session_count += 1
                    gym_sessions.append({
                        'phase': '旧版公式',
                        'gym_level': current_gym + 1,
                        'trains_completed': trains_completed,
                        'energy_used': trains_completed * energy_per_train,
                        'attribute_gain': total_gain_this_session,
                        'stat_gains': stat_gains.copy(),
                    })
                    
                    if session_count <= 5 or session_count % 5 == 0:
                        print(f"     - 旧版会话 {session_count}: 健身房{current_gym + 1}, 训练{trains_completed}次, 增长{total_gain_this_session:.0f}")
                
                if gym_capacity_left <= energy_per_train and current_gym < len(BS_CONSTANTS['L']) - 1:
                    current_gym += 1
                    gym_capacity_left = BS_CONSTANTS['W'][current_gym]
                elif actual_trains == 0:
                    break
        
        # 第二阶段：使用新版公式
        if new_energy > 0:
            print(f"\n   🆕 第二阶段：新版公式训练（{new_energy:,} 能量）")
            remaining_energy = new_energy
            
            # 如果第一阶段没有训练，从健身房1开始
            if old_energy == 0:
                current_gym = 0
                gym_capacity_left = BS_CONSTANTS['W'][0]
            # 否则继续使用第一阶段的健身房状态
            
            while remaining_energy > 0 and current_gym < len(BS_CONSTANTS['L']):
                energy_per_train = BS_CONSTANTS['E'][current_gym]
                gym_dots = BS_CONSTANTS['L'][current_gym]
                
                max_trains_by_energy = remaining_energy // energy_per_train
                max_trains_by_capacity = gym_capacity_left // energy_per_train
                actual_trains = min(max_trains_by_energy, max_trains_by_capacity, 10000)
                
                if actual_trains <= 0:
                    break
                
                total_gain_this_session = 0
                trains_completed = 0
                stat_gains = {'strength': 0, 'speed': 0, 'dexterity': 0, 'defense': 0}
                
                for train in range(int(actual_trains)):
                    if remaining_energy < energy_per_train:
                        break
                    
                    current_stat = stat_types[current_stat_index]
                    
                    if current_stat == 'strength':
                        current_stat_value = strength_stats
                    elif current_stat == 'speed':
                        current_stat_value = speed_stats
                    elif current_stat == 'dexterity':
                        current_stat_value = dexterity_stats
                    else:
                        current_stat_value = defense_stats
                    
                    # 使用新版公式
                    gain = self.calculate_training_gain_new(
                        current_stat_value,
                        current_happy,
                        current_gym,
                        energy_per_train,
                        current_stat
                    )
                    
                    # 更新对应属性的值
                    if current_stat == 'strength':
                        strength_stats += gain
                    elif current_stat == 'speed':
                        speed_stats += gain
                    elif current_stat == 'dexterity':
                        dexterity_stats += gain
                    else:
                        defense_stats += gain
                    
                    stat_gains[current_stat] += gain
                    total_gain_this_session += gain
                    
                    remaining_energy -= energy_per_train
                    gym_capacity_left -= energy_per_train
                    trains_completed += 1
                    current_stat_index = (current_stat_index + 1) % 4
                
                if trains_completed > 0:
                    session_count += 1
                    gym_sessions.append({
                        'phase': '新版公式',
                        'gym_level': current_gym + 1,
                        'trains_completed': trains_completed,
                        'energy_used': trains_completed * energy_per_train,
                        'attribute_gain': total_gain_this_session,
                        'stat_gains': stat_gains.copy(),
                    })
                    
                    if session_count <= 5 or session_count % 5 == 0:
                        print(f"     - 新版会话 {session_count}: 健身房{current_gym + 1}, 训练{trains_completed}次, 增长{total_gain_this_session:.0f}")
                
                if gym_capacity_left <= energy_per_train and current_gym < len(BS_CONSTANTS['L']) - 1:
                    current_gym += 1
                    gym_capacity_left = BS_CONSTANTS['W'][current_gym]
                elif actual_trains == 0:
                    break
        
        # SE增强剂加成 - 重新实现
        stat_enhancers = stats.get('items', {}).get('used', {}).get('stat_enhancers', 0)
        if stat_enhancers > 0:
            print(f"\n   💊 SE增强剂处理: {stat_enhancers}个")
            
            # 计算总的SE增长潜力
            # 使用原来的公式计算总增长量
            original_total = strength_stats + speed_stats + dexterity_stats + defense_stats
            se_enhanced_total = 0.5 * original_total + 0.25 * original_total * (1 + 0.85 * (pow(1.01, 0.8 * stat_enhancers) - 1)) + 0.25 * original_total * (1 + 0.85 * (pow(1.01, 0.2 * stat_enhancers) - 1))
            total_se_growth = se_enhanced_total - original_total
            
            print(f"   - 总SE增长潜力: {total_se_growth:,.0f}")
            
            # SE分配策略：优先级为力量 → 速度 → 敏捷 → 防御
            se_cap_per_stat = 500000000000000  # 500T
            remaining_se_cap = 5000000000000   # 5T
            
            # 原始属性值（SE前）
            original_strength = strength_stats
            original_speed = speed_stats
            original_dexterity = dexterity_stats
            original_defense = defense_stats
            
            remaining_se_growth = total_se_growth
            
            # 第一优先级：力量
            strength_se_growth = 0
            if remaining_se_growth > 0:
                max_strength_growth = se_cap_per_stat - original_strength
                if max_strength_growth > 0:
                    strength_se_growth = min(remaining_se_growth, max_strength_growth)
                    strength_stats += strength_se_growth
                    remaining_se_growth -= strength_se_growth
                    print(f"   - 力量SE增长: {strength_se_growth:,.0f} (总计: {strength_stats:,.0f})")
            
            # 第二优先级：速度
            speed_se_growth = 0
            if remaining_se_growth > 0:
                max_speed_growth = se_cap_per_stat - original_speed
                if max_speed_growth > 0:
                    speed_se_growth = min(remaining_se_growth, max_speed_growth)
                    speed_stats += speed_se_growth
                    remaining_se_growth -= speed_se_growth
                    print(f"   - 速度SE增长: {speed_se_growth:,.0f} (总计: {speed_stats:,.0f})")
            
            # 第三优先级：敏捷
            dexterity_se_growth = 0
            if remaining_se_growth > 0:
                max_dexterity_growth = se_cap_per_stat - original_dexterity
                if max_dexterity_growth > 0:
                    dexterity_se_growth = min(remaining_se_growth, max_dexterity_growth)
                    dexterity_stats += dexterity_se_growth
                    remaining_se_growth -= dexterity_se_growth
                    print(f"   - 敏捷SE增长: {dexterity_se_growth:,.0f} (总计: {dexterity_stats:,.0f})")
            
            # 第四优先级：防御（只能增长5T）
            defense_se_growth = 0
            if remaining_se_growth > 0:
                max_defense_growth = min(remaining_se_cap, remaining_se_growth)
                defense_se_growth = max_defense_growth
                defense_stats += defense_se_growth
                remaining_se_growth -= defense_se_growth
                print(f"   - 防御SE增长: {defense_se_growth:,.0f} (总计: {defense_stats:,.0f})")
            
            # 更新总属性
            total_stats = strength_stats + speed_stats + dexterity_stats + defense_stats
            
            print(f"   - SE前总属性: {original_total:,.0f}")
            print(f"   - SE后总属性: {total_stats:,.0f}")
            print(f"   - 实际SE增长: {total_stats - original_total:,.0f}")
            if remaining_se_growth > 0:
                print(f"   - 剩余未分配SE: {remaining_se_growth:,.0f}")
        else:
            # 计算总属性
            total_stats = strength_stats + speed_stats + dexterity_stats + defense_stats
        
        print(f"\n   📊 训练总结:")
        print(f"   - 训练会话总数: {len(gym_sessions)}")
        print(f"   - 各属性最终值:")
        print(f"     力量: {strength_stats:,.0f}")
        print(f"     速度: {speed_stats:,.0f}")
        print(f"     敏捷: {dexterity_stats:,.0f}")
        print(f"     防御: {defense_stats:,.0f}")
        print(f"   - 最终总属性: {total_stats:,.0f}")
        
        return int(total_stats)
    
    def calculate_happy_loss(self, energy_per_train):
        """
        计算快乐损失：dH = ROUND((1/10) * ENERGYPERTRAIN * RANDBETWEEN(4,6), 0)
        使用平均值5.0来避免随机性
        """
        return round((1/10) * energy_per_train * 5.0, 0)
    
    def apply_rank_correction(self, total_stats, profile, criminal_record):
        """应用Rank修正"""
        print(f"\n🎖️ 开始Rank修正...")
        
        rank = profile.get('rank', 'Average')
        c = BS_CONSTANTS['Y'].get(rank, 7)
        original_c = c
        c -= 1
        
        print(f"   - 用户Rank: {rank}")
        print(f"   - 初始c值: {original_c} -> {c}")
        
        # 根据等级修正
        level = profile.get('level', 1)
        level_reductions = 0
        for threshold in BS_CONSTANTS['J']:
            if level >= threshold:
                c -= 1
                level_reductions += 1
        
        print(f"   - 等级: {level}, 等级修正: -{level_reductions}")
        
        # 根据犯罪次数修正
        total_crimes = sum(criminal_record.values()) if isinstance(criminal_record, dict) else criminal_record.get('total', 0)
        crime_reductions = 0
        for threshold in BS_CONSTANTS['K']:
            if total_crimes >= threshold:
                c -= 1
                crime_reductions += 1
        
        print(f"   - 总犯罪次数: {total_crimes:,}, 犯罪修正: -{crime_reductions}")
        
        # 根据总资产修正
        networth = profile.get('networth', {})
        if isinstance(networth, dict):
            networth_value = networth.get('total', 0)
        else:
            networth_value = networth
        
        networth_reductions = 0
        for threshold in BS_CONSTANTS['V']:
            if networth_value >= threshold:
                c -= 1
                networth_reductions += 1
        
        print(f"   - 净资产: ${networth_value:,}, 资产修正: -{networth_reductions}")
        print(f"   - 最终c值: {c}")
        
        # 确定Rank对应的BS范围
        if c <= 0:
            lower_bound = 0
            upper_bound = BS_CONSTANTS['R'][0]
        elif c >= len(BS_CONSTANTS['B']):
            lower_bound = BS_CONSTANTS['B'][-1]
            upper_bound = float('inf')
        else:
            lower_bound = BS_CONSTANTS['B'][c - 1]
            upper_bound = BS_CONSTANTS['R'][c]
        
        print(f"   - BS范围: [{lower_bound:,} - {upper_bound:,}]")
        print(f"   - 计算属性: {total_stats:,}")
        
        # 根据计算结果与范围关系返回最终值
        if total_stats < lower_bound:
            final_bs = (total_stats + lower_bound) / 2
            print(f"   - 结果低于下限，使用中间值")
        elif total_stats > upper_bound and upper_bound != float('inf'):
            final_bs = (upper_bound + total_stats) / 2
            print(f"   - 结果高于上限，使用中间值")
        else:
            final_bs = total_stats
            print(f"   - 结果在范围内，使用计算值")
        
        print(f"   - 修正后BS: {final_bs:,.0f}")
        
        return final_bs
    
    def calculate_bs(self, user_id):
        """计算用户BS值"""
        print(f"🎯 开始计算用户 {user_id} 的BS值")
        print("=" * 60)
        
        try:
            # 获取用户数据
            user_data = self.get_user_data(user_id)
            
            # 计算总能量消耗
            total_energy = self.calculate_total_energy(user_data['profile'], user_data['personalstats'])
            
            # 模拟健身房锻炼
            total_stats = self.simulate_gym_training(total_energy, user_data['personalstats'], user_data['profile'])
            
            # 直接使用总属性值作为最终BS（不进行Rank修正）
            final_bs = total_stats
            
            # 计算BS分数
            bs_score = math.sqrt(final_bs) * 2
            
            print(f"\n🏆 最终计算结果")
            print("=" * 60)
            print(f"   - 总属性值: {total_stats:,.0f}")
            print(f"   - 预估BS: {final_bs:,.0f}")
            print(f"   - BS分数: {bs_score:,.0f}")
            
            # 评估可信度
            confidence = "high" if total_energy > 1000000 else "medium" if total_energy > 100000 else "low"
            print(f"   - 预测可信度: {confidence}")
            
            return {
                'user_id': user_id,
                'username': user_data['profile'].get('name', 'Unknown'),
                'level': user_data['profile'].get('level', 'Unknown'),
                'rank': user_data['profile'].get('rank', 'Unknown'),
                'total_energy': total_energy,
                'total_stats': total_stats,
                'final_bs': int(final_bs),
                'bs_score': int(bs_score),
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"❌ 计算失败: {e}")
            return None

def main():

    apikey="3p5n5mHL7MggDaH7"
    userid=979003

    calculator = BSCalculator(apikey)
    result = calculator.calculate_bs(userid)
    
    if result:
        print(f"\n📊 计算完成！")
        print(f"用户: {result['username']} (ID: {result['user_id']})")
        print(f"等级: {result['level']}, Rank: {result['rank']}")
        print(f"预估BS: {result['final_bs']:,}")
        print(f"BS分数: {result['bs_score']:,}")
        print(f"可信度: {result['confidence']}")
    else:
        print(f"❌ 计算失败")

if __name__ == "__main__":
    main() 