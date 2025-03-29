# Torn Faction Attacks Collector

这是一个用于收集Torn City派系攻击记录的Python程序。程序会查找最新的ranked war开始时间戳，并收集从该时间戳开始至今的所有攻击记录。

## 功能

- 获取指定派系的最新ranked war开始时间戳
- 收集从该时间戳开始至今的所有攻击记录
- 支持分批获取攻击记录（每次最多1000条）
- 限制API请求速率为每秒一条
- 将结果保存为JSON文件

## 安装

1. 确保您安装了Python 3.6或更高版本
2. 安装必要的依赖：

```bash
pip install requests
```

## 使用方法

```bash
python faction_attacks.py --api_key YOUR_API_KEY --faction_id YOUR_FACTION_ID [--output OUTPUT_FILE]
```

### 参数说明

- `--api_key`: 您的Torn API密钥，需要有faction API访问权限
- `--faction_id`: 您想要查询的派系ID
- `--output`: （可选）输出文件名，默认为`faction_attacks.json`

### 示例

```bash
python faction_attacks.py --api_key 1234567890abcdef --faction_id 12345 --output my_faction_attacks.json
```

## 注意事项

- API密钥需要有faction API访问权限
- 程序会限制API请求速率，每秒只发送一个请求
- 获取的攻击记录最多为1000条/请求，程序会自动分批获取所有记录

## 许可

MIT 