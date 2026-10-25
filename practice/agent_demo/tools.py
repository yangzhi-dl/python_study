"""三个领域工具：查工单、查质检、查 BOM

这一层的设计原则（来自 Pi Agent 的「副作用边界」）：
- 模型只能"提议"调用哪个工具
- 真正执行发生在这里，是普通 Python 代码
- 以后要加权限控制、日志、缓存，都在这一层加

真实场景里，这里的字典查询会换成数据库 / MES 接口调用。
先用假数据，是为了让你专注在 Agent 逻辑上，不被数据接入卡住。
"""

from langchain_core.tools import tool


# ============================================================
# 假数据区（真实场景替换成数据库查询）
# ============================================================

WORKORDERS: dict[tuple[str, str], list[dict]] = {
    ("3号线", "2026-10-24"): [
        {"batch_id": "B001", "product": "A型阀体", "status": "正常"},
        {"batch_id": "B002", "product": "A型阀体", "status": "异常"},
        {"batch_id": "B003", "product": "A型阀体", "status": "异常"},
        {"batch_id": "B004", "product": "A型阀体", "status": "正常"},
        {"batch_id": "B005", "product": "A型阀体", "status": "异常"},
    ],
    ("3号线", "2026-10-23"): [
        {"batch_id": "B010", "product": "A型阀体", "status": "正常"},
        {"batch_id": "B011", "product": "A型阀体", "status": "正常"},
    ],
}

QUALITY_RECORDS: dict[str, dict] = {
    "B002": {
        "defect": "焊缝气孔",
        "parameters": {"回流焊峰值温度": "228°C", "标准": "235-245°C"},
        "operator": "张三",
    },
    "B003": {
        "defect": "焊缝气孔",
        "parameters": {"回流焊峰值温度": "226°C", "标准": "235-245°C"},
        "operator": "张三",
    },
    "B005": {
        "defect": "虚焊",
        "parameters": {"回流焊峰值温度": "229°C", "标准": "235-245°C"},
        "operator": "李四",
    },
}

BOM_DATA: dict[str, list[dict]] = {
    "A型阀体": [
        {"material": "焊锡膏", "supplier": "S001", "batch": "M2026-10-20"},
        {"material": "铜基板", "supplier": "S002", "batch": "M2026-10-18"},
    ],
}


# ============================================================
# 工具定义
#
# 关键：docstring 不是写给人看的，是写给 LLM 看的。
# 模型靠它判断"什么时候该用这个工具"、"参数怎么填"。
# 写得含糊，模型就调不对——这是 Agent 调优的第一优先级。
# ============================================================


@tool
def query_workorder(line: str, date: str) -> str:
    """查询指定产线在某天的工单记录。

    适用于：用户询问某条产线某天的生产情况、批次数量、哪些批次异常。

    Args:
        line: 产线编号，例如 "3号线"、"装配二线"
        date: 日期，格式 YYYY-MM-DD，例如 "2026-10-24"
    """
    records = WORKORDERS.get((line, date))
    if not records:
        return f"未找到 {line} 在 {date} 的工单记录"

    lines = [f"{line} {date} 共 {len(records)} 个批次："]
    for r in records:
        lines.append(f"  {r['batch_id']} - {r['product']} - {r['status']}")
    return "\n".join(lines)


@tool
def query_quality(batch_id: str) -> str:
    """查询指定批次的质检记录。

    适用于：已知批次号，需要查看该批次的不良项、检测参数、操作人员。

    Args:
        batch_id: 批次号，例如 "B002"
    """
    record = QUALITY_RECORDS.get(batch_id)
    if not record:
        return f"未找到批次 {batch_id} 的质检记录"

    params = "，".join(f"{k}: {v}" for k, v in record["parameters"].items())
    return (
        f"批次 {batch_id}\n"
        f"  不良项: {record['defect']}\n"
        f"  参数: {params}\n"
        f"  操作员: {record['operator']}"
    )


@tool
def query_bom(product: str) -> str:
    """查询指定产品的 BOM（物料清单）。

    适用于：需要了解产品用了哪些物料、来自哪个供应商、哪个批次。
    当怀疑是来料问题时使用。

    Args:
        product: 产品名称，例如 "A型阀体"
    """
    items = BOM_DATA.get(product)
    if not items:
        return f"未找到 {product} 的 BOM 数据"

    lines = [f"{product} 的物料清单："]
    for i in items:
        lines.append(f"  {i['material']} - 供应商 {i['supplier']} - 批次 {i['batch']}")
    return "\n".join(lines)


# 这个列表在 main.py 里传给 create_agent
ALL_TOOLS = [query_workorder, query_quality, query_bom]
