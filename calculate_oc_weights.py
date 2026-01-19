import json
import sys
import os

# Ensure we're in the script's directory (d:\code\test\tornweb)
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

def calculate_ev(nodes, node_id, current_rates, memo):
    if node_id in memo:
        return memo[node_id]

    node = nodes.get(node_id)
    if not node:
        return 0.0

    if node['type'] == 'end':
        money = 0.0
        if 'reward' in node and 'money' in node['reward']:
            money = float(node['reward']['money'])
        memo[node_id] = money
        return money

    if node['type'] == 'step':
        node_roles = node.get('roles', [])
        if not node_roles:
            p = 0.0
        else:
            total_rate = sum(current_rates.get(rid, 0.0) for rid in node_roles)
            p = total_rate / len(node_roles)

        e_pass = calculate_ev(nodes, node.get('pass'), current_rates, memo)
        e_fail = calculate_ev(nodes, node.get('fail'), current_rates, memo)

        ev = p * e_pass + (1 - p) * e_fail
        memo[node_id] = ev
        return ev
    
    if node['type'] == 'start':
        next_node = node.get('next')
        ev = calculate_ev(nodes, next_node, current_rates, memo)
        memo[node_id] = ev
        return ev
    
    return 0.0

def calculate_reach_probs(nodes, seed_nodes, current_rates):
    probs = {k: 0.0 for k in nodes}
    probs['start'] = 1.0
    
    if seed_nodes:
        process_list = seed_nodes
    else:
        process_list = list(nodes.keys())

    for key in process_list:
        if key not in nodes: continue
        node = nodes[key]
        p_in = probs[key]
        
        if p_in <= 0:
            continue
            
        if node['type'] == 'start':
            if node.get('next'):
                probs[node['next']] += p_in
        elif node['type'] == 'step':
            node_roles = node.get('roles', [])
            if not node_roles:
                p = 0.0
            else:
                total_rate = sum(current_rates.get(rid, 0.0) for rid in node_roles)
                p = total_rate / len(node_roles)
            
            p_pass = p_in * p
            p_fail = p_in * (1 - p)
            
            if node.get('pass'):
                probs[node['pass']] += p_pass
            if node.get('fail'):
                probs[node['fail']] += p_fail
    
    return probs

def main():
    try:
        with open('oc_data.json', 'r', encoding='utf-8') as f:
            ocs = json.load(f)
    except FileNotFoundError:
        print("Error: oc_data.json not found. Run 'node export_oc.mjs' first.")
        return

    final_output = {}

    for oc in ocs:
        oc_key = oc.get('key', oc['name']) # Fallback if key missing
        oc_name = oc['name']
        print(f"Processing {oc_name}...")
        
        roles = oc['roles']
        nodes = oc['nodes']
        order = oc.get('order')
        
        # Structure: map[rate_int] = { total_ev, roles: [ ... ] }
        oc_results = {}

        for x_int in range(1, 101):
            x = x_int / 100.0
            
            # 1. Set rates
            current_rates = {r['id']: x for r in roles}
            
            # 2. Total EV
            ev_memo = {}
            total_ev = calculate_ev(nodes, 'start', current_rates, ev_memo)
            
            # 3. Reach Probs
            reach_probs = calculate_reach_probs(nodes, order, current_rates)
            
            # 4. Calculate Raw Weights
            raw_weights = {}
            total_weight_sum = 0.0
            
            for role in roles:
                rid = role['id']
                w = 0.0
                
                for nid, node in nodes.items():
                    if node['type'] == 'step' and rid in node.get('roles', []):
                        node_roles = node['roles']
                        k = len(node_roles)
                        
                        p_reach = reach_probs.get(nid, 0.0)
                        if p_reach <= 0:
                            continue
                            
                        e_pass = ev_memo.get(node.get('pass'), 0.0)
                        e_fail = ev_memo.get(node.get('fail'), 0.0)
                        
                        # Marginal gain (derivative)
                        marginal = (1.0 / k) * (e_pass - e_fail)
                        w += p_reach * marginal
                
                raw_weights[rid] = w
                total_weight_sum += w
                
            # 5. Normalize and Calculate Income
            role_breakdown = []
            for role in roles:
                rid = role['id']
                raw = raw_weights.get(rid, 0.0)
                
                percent = 0.0
                income = 0.0
                
                if total_weight_sum > 0:
                    percent = raw / total_weight_sum
                    income = total_ev * percent
                
                role_breakdown.append({
                    "id": rid,
                    "name": role['name'],
                    "percent": round(percent, 4), # 0.1234
                    "income": round(income, 2)
                })
            
            oc_results[x_int] = {
                "total_ev": round(total_ev, 2),
                "roles": role_breakdown
            }

        final_output[oc_key] = oc_results

    # Write to JS file
    output_path = 'src/data/oc_analysis_data.js'
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            js_content = f"// Generated by calculate_oc_weights.py\n"
            js_content += f"export const OC_ANALYSIS_DATA = {json.dumps(final_output, indent=2)};"
            f.write(js_content)
        print(f"Done. Results saved to {output_path}")
    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == '__main__':
    main()
