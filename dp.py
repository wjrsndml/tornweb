from functools import lru_cache

def allocate_rewards(cache_prices, a_caches, b_caches, a_target_percentage, b_target_percentage):
    """
    根据 A、B 两派系各自拥有的 cache 数量和单价，以及目标奖励比例，
    计算从一方转移到另一方时需要转移各类 cache 的数量以及用现金补偿的金额。
    
    如果 A 的当前价值比例 >= a_target_percentage，则从 A 转移到 B，
    否则从 B 转移到 A。
    """
    if a_target_percentage + b_target_percentage!=1:
        print("a_target_percentage + b_target_percentage!=1")
    total_value = sum((a_caches[cache] + b_caches[cache]) * cache_prices[cache] for cache in cache_prices)
    totala = sum(a_caches[cache] * cache_prices[cache] for cache in cache_prices)

    if totala / total_value >= a_target_percentage:
        # A 的价值过高，需从 A 转移到 B，使 A 的价值降到目标比例
        cash, state_info = allocate_rewards_dp(cache_prices, a_caches, a_target_percentage, total_value)
        keys, transfers_tuple = state_info
        transfers = {keys[i]: transfers_tuple[i] for i in range(len(keys))}
        print("需要从A转移到B的各类cache数量:")
        for k, v in transfers.items():
            print(f"  {k}: {v}")
        print("需要从A转移到B的现金:", cash)
    else:
        # 否则 B 的价值过高，从 B 转移到 A，使得 B 的价值降到目标比例（或 A 提升到 b_target_percentage）
        cash, state_info = allocate_rewards_dp(cache_prices, b_caches, b_target_percentage, total_value)
        keys, transfers_tuple = state_info
        transfers = {keys[i]: transfers_tuple[i] for i in range(len(keys))}
        print("需要从B转移到A的各类cache数量:")
        for k, v in transfers.items():
            print(f"  {k}: {v}")
        print("需要从B转移到A的现金:", cash)


def allocate_rewards_dp(cache_prices, faction_caches, target_percentage, total_value):
    """
    计算某一派系（A 或 B）经过转移后，使其总价值降到目标比例以下时，
    最小化需要现金补偿的数额。
    
    参数：
      - cache_prices: 各类 cache 的单价（字典）
      - faction_caches: 当前派系拥有的各类 cache 数量（字典）
      - target_percentage: 目标的价值比例（例如 0.1 或 0.9）
      - total_value: A、B 总的 cache 价值
    返回：
      - (min_cash, (keys, optimal_state)) 其中 optimal_state 是一个元组，
        表示各类 cache 转移的数量，keys 为 cache 的列表顺序。
        
    逻辑：
      我们定义状态 state 为一个长度为 n 的元组，表示各类 cache 已转移数量，
      按 cache_prices 的 key 顺序排列。
      
      当前派系转出 cache 后的总价值为：
         totala = Σ[(faction_caches[k] - state[i]) * cache_prices[k]]
      差额 diff = totala - target_percentage * total_value
      
      如果 diff 小于当前仍可转移 cache 中最小的一件的价值，
      则不再转移 cache，用现金补足 diff；否则，尝试对每个可转移类型增加1个，
      递归搜索获得现金补偿最小的方案。
    """
    keys = list(cache_prices.keys())
    n = len(keys)

    @lru_cache(maxsize=None)
    def dp(state):
        # state: 元组，长度为 n，表示各类 cache 已转移的数量
        totala = sum((faction_caches[keys[i]] - state[i]) * cache_prices[keys[i]] for i in range(n))
        # 如果已经转移过多，导致 totala 小于目标价值，则返回无穷大，避免选择此分支
        if totala < target_percentage * total_value:
            return float('inf'), state

        # 差额，即还需补偿的价值
        diff = totala - (target_percentage * total_value)
        # 如果刚好达到目标，则现金补偿为 0
        if diff == 0:
            return 0, state

        # 查找仍能转移的 cache 类型（即尚未全部转移完毕）
        available = [i for i in range(n) if state[i] < faction_caches[keys[i]]]
        if not available:
            # 若没有可转移的 cache，则只能用现金补差
            return diff, state

        # 当前可转移 cache 中最小的一件价值
        min_available_val = min(cache_prices[keys[i]] for i in available)
        if diff < min_available_val:
            # 再转移一个 cache 会使补偿超出需要，因此不转移更多，用现金补差
            return diff, state

        best_cash = float('inf')
        best_state = None
        # 尝试对每个可转移类型增加1个 cache
        for i in available:
            # 只有当当前差额至少能抵消一个 cache 的价值时才尝试转移
            if diff >= cache_prices[keys[i]]:
                new_state = list(state)
                new_state[i] += 1
                new_state = tuple(new_state)
                cash, final_state = dp(new_state)
                if cash < best_cash:
                    best_cash = cash
                    best_state = final_state
        return best_cash, best_state

    init_state = tuple(0 for _ in range(n))
    cash, final_state = dp(init_state)
    return cash, (keys, final_state)


if __name__ == "__main__":
    cache_prices = {
        "Small Arms Cache": 124_499_894,
        "Medium Arms Cache": 225_561_874,
        "Heavy Arms Cache": 404_999_998,
        "Armor Cache": 351_908_331,
        "Melee Cache": 175_233_915
    }

    # Order Through Chaos (A派系)
    a_caches = {
        "Small Arms Cache": 1,
        "Medium Arms Cache": 10,
        "Heavy Arms Cache": 1,
        "Armor Cache": 7,
        "Melee Cache": 0
    }

    # SMTH - Concord (B派系)
    b_caches = {
        "Heavy Arms Cache": 0,
        "Small Arms Cache": 1,
        "Medium Arms Cache": 2,
        "Armor Cache": 4,
        "Melee Cache": 4
    }

    # a_target_percentage 与 b_target_percentage 分别代表 A、B 的目标价值比例
    allocate_rewards(cache_prices, a_caches, b_caches, 0.6, 0.4)
