import copy
def allocate_rewards(cache_prices, a_caches, b_caches, a_target_percentage,b_target_percentage):
    """
    使用动态规划分配奖励，优先使用cache补偿，尽量减少现金补偿。
    
    参数:
    cache_prices: 字典，各类cache的单价
    a_caches: 字典，A派系拥有的各类cache数量
    b_caches: 字典，B派系拥有的各类cache数量
    a_target_percentage: A派系应得的总奖励百分比
    
    返回: 
    字典，包含需要从B转移到A的各类cache数量和现金数额
    """
    # 计算当前A和B的总价值

    total_value = sum((a_caches[cache]+b_caches[cache]) * cache_prices[cache] for cache in cache_prices)
    totala = sum(a_caches[cache] * cache_prices[cache] for cache in cache_prices)
    totalb = sum(b_caches[cache] * cache_prices[cache] for cache in cache_prices)
    mincachevalue=min(cache_prices.values())
    if totala/total_value >= a_target_percentage:
        transfer,result=allocate_rewards_atob(cache_prices, a_caches, b_caches, a_target_percentage,totalvalue=total_value,mincachevalue=mincachevalue)
        for i in transfer:
            print(f"\n需要从A转移到B的{i}:{transfer[i]}")
        print(f"\n需要从A转移到B的现金:{result}")
    else:
        transfer,result=allocate_rewards_atob(cache_prices, b_caches, a_caches, b_target_percentage,totalvalue=total_value,mincachevalue=mincachevalue)
        for i in transfer:
            print(f"\n需要从B转移到A的{i}:{transfer[i]}")
        print(f"\n需要从B转移到A的现金:{result}")


def allocate_rewards_atob(cache_prices, a_caches, b_caches, a_target_percentage,totalvalue,mincachevalue,transfer_caches=None):
    """
    使用动态规划分配奖励，优先使用cache补偿，尽量减少现金补偿。

    参数:
    cache_prices: 字典，各类cache的单价
    a_caches: 字典，A派系拥有的各类cache数量
    b_caches: 字典，B派系拥有的各类cache数量
    a_target_percentage: A派系应得的总奖励百分比
    
    返回: 
    字典，包含需要从B转移到A的各类cache数量和现金数额
    """
    if transfer_caches is None:
        transfer_caches = {cache: 0 for cache in cache_prices}
    totala = sum((a_caches[cache]-transfer_caches[cache]) * cache_prices[cache] for cache in cache_prices)
    totalb = sum((b_caches[cache]+transfer_caches[cache]) * cache_prices[cache] for cache in cache_prices)
    mincachevalue=min([cache_prices[cache] for cache in cache_prices if a_caches[cache]-transfer_caches[cache]>0])
    transfers=[]
    results=[]
    if totala/totalvalue >= a_target_percentage:
        if (totala/totalvalue-a_target_percentage)*totalvalue<mincachevalue:
            return transfer_caches,(totala/totalvalue-a_target_percentage)*totalvalue
        else:
            for cache in cache_prices:
                    if a_caches[cache]-transfer_caches[cache]>0:
                        if (totala/totalvalue-a_target_percentage)*totalvalue>cache_prices[cache]:
                            trancaches=copy.deepcopy(transfer_caches)
                            trancaches[cache]+=1
                            transfer,result=allocate_rewards_atob(cache_prices, a_caches, b_caches, a_target_percentage,totalvalue,mincachevalue,trancaches)
                            transfers.append(transfer)
                            results.append(result)
            return transfers[results.index(min(results))],min(results)

    


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
    allocate_rewards(cache_prices, a_caches, b_caches, 0.1,0.9)