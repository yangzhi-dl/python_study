"""LangGraph 图结构打印工具（ch02_0x 共用）。

用法（一行）：
    from graph_flow import draw_flow
    draw_flow(app, title="Demo 3 · 流程图")

两种画法自动选择：
  1. 直线图（每个节点最多一进一出）
     竖排方框 + 箭头，箭头上可以写这一步 State 怎么变
  2. 分支 / 循环 / 合并
     每个节点一个方框，框右边列出它的所有出边

⚠ 一个必须知道的坑
  条件边如果【没传显式映射表】，例如：
      builder.add_conditional_edges("judge", route)
  LangGraph 自己也记不住分支能去哪 —— get_graph() 里只剩一条伪造的
  "judge → END"。这种图必须用 branch_targets 告诉绘制器：
      draw_flow(app, branch_targets={"judge": ["pass", "retry"]})
"""

from __future__ import annotations

import unicodedata
from typing import Any

_DISPLAY = {"__start__": "START", "__end__": "END"}


# ============================================================
# 一、基础工具
# ============================================================

def display_width(text: str) -> int:
    """终端显示宽度：中文占 2 格，英文占 1 格。"""
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


# ============================================================
# 二、从编译后的图里读结构
# ============================================================

def _normalize(name: str) -> str:
    if name in ("__start__", "START"):
        return "START"
    if name in ("__end__", "END"):
        return "END"
    return _DISPLAY.get(name, name)


def _collect(
    app: Any,
    branch_targets: dict[str, list[str]] | None = None,
) -> tuple[list[str], list[dict], set[str]]:
    """返回 (节点列表, 边列表, 隐式条件边的源节点集合)。

    每条边是 dict：{"src": 起点, "dst": 终点, "cond": 是否条件边, "label": 分支键}
    """
    graph = app.get_graph()
    builder = getattr(app, "builder", None)

    nodes = [_normalize(name) for name in graph.nodes]

    # 找出"没有映射表"的条件边 —— 这种边 LangGraph 自己都记不住目标
    implicit: set[str] = set()
    if builder is not None:
        for raw_src, specs in (getattr(builder, "branches", {}) or {}).items():
            for _name, spec in specs.items():
                if not getattr(spec, "ends", None):
                    implicit.add(_normalize(raw_src))

    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(src: str, dst: str, cond: bool, label: str | None = None) -> None:
        key = (src, dst)
        if key in seen:
            return
        seen.add(key)
        edges.append({"src": src, "dst": dst, "cond": cond, "label": label})

    # ① 普通边：以 builder.edges 为准
    #    编译后的图会给隐式条件边伪造一条 → END，所以不能直接用 graph.edges
    if builder is not None:
        for raw_src, raw_dst in getattr(builder, "edges", set()):
            add(_normalize(raw_src), _normalize(raw_dst), False)
    else:
        for edge in graph.edges:
            if not edge.conditional:
                add(_normalize(edge.source), _normalize(edge.target), False)

    # ② 有显式映射表的条件边：graph.edges 里能读出来
    for edge in graph.edges:
        if edge.conditional:
            add(_normalize(edge.source), _normalize(edge.target), True, edge.data)

    # ③ 隐式条件边：分支目标只能由调用方提供
    for src in implicit:
        for raw_dst in (branch_targets or {}).get(src, []):
            add(src, _normalize(raw_dst), True)

    return nodes, edges, implicit


def _back_edges(nodes: list[str], edges: list[dict]) -> set[tuple[str, str]]:
    """DFS 找回边 —— 指回"当前递归路径上"的边就是循环。"""
    outgoing: dict[str, list[str]] = {}
    for edge in edges:
        if edge["dst"] in nodes:
            outgoing.setdefault(edge["src"], []).append(edge["dst"])

    state: dict[str, int] = {}
    back: set[tuple[str, str]] = set()

    def dfs(node: str) -> None:
        state[node] = 1
        for nxt in outgoing.get(node, []):
            if nxt == node:
                back.add((node, nxt))
            elif state.get(nxt) == 1:
                back.add((node, nxt))
            elif nxt not in state:
                dfs(nxt)
        state[node] = 2

    for node in nodes:
        if node not in state:
            dfs(node)
    return back


def _is_linear(nodes: list[str], edges: list[dict], back: set) -> bool:
    """每个节点最多一条入边、一条出边，且没有回边、没有孤立节点 → 可以竖排画。"""
    if back:
        return False
    out_count: dict[str, int] = {}
    in_count: dict[str, int] = {}
    for edge in edges:
        out_count[edge["src"]] = out_count.get(edge["src"], 0) + 1
        in_count[edge["dst"]] = in_count.get(edge["dst"], 0) + 1
    for node in nodes:
        if out_count.get(node, 0) > 1 or in_count.get(node, 0) > 1:
            return False
        # 孤立节点：既没有入边也没有出边，竖排硬连会画出假箭头
        if node not in ("START", "END"):
            if out_count.get(node, 0) == 0 and in_count.get(node, 0) == 0:
                return False
    return True


def _linear_order(nodes: list[str], edges: list[dict]) -> list[str]:
    """按连线顺序排出执行链。"""
    nxt = {edge["src"]: edge["dst"] for edge in edges}
    order: list[str] = []
    cursor = "START"
    while True:
        order.append(cursor)
        if cursor == "END" or cursor not in nxt:
            break
        cursor = nxt[cursor]
    for node in nodes:
        if node not in order:
            order.append(node)
    return order


# ============================================================
# 三、画法 A：竖排（直线图）
# ============================================================

def _render_linear(
    order: list[str],
    edges: list[dict],
    node_notes: dict[str, str],
    edge_notes: dict[tuple[str, str], list[str]],
    title: str,
) -> list[str]:
    edge_of = {edge["src"]: edge for edge in edges}

    inner = max(display_width(node) for node in order) + 6
    if inner % 2 == 0:
        inner += 1
    center = inner // 2

    lines = [f"\n【{title}】", "  框里 = 节点    框右边 = 这个节点 return 什么"]

    for index, node in enumerate(order):
        pad = inner - display_width(node)
        left = pad // 2
        right = pad - left

        lines.append("   ┌" + "─" * inner + "┐")
        row = "   │" + " " * left + node + " " * right + "│"
        if node_notes.get(node):
            row += "  " + node_notes[node]
        lines.append(row.rstrip())

        if index == len(order) - 1:
            lines.append("   └" + "─" * inner + "┘")
            break

        lines.append("   └" + "─" * center + "┬" + "─" * (inner - center - 1) + "┘")

        spine = "   " + " " * (center + 1)
        lines.append(spine + "│")

        key = (node, order[index + 1])
        note_lines = edge_notes.get(key, [])
        if note_lines:
            for text in note_lines:
                lines.append(spine + "│  " + text)
            lines.append(spine + "│")
        else:
            edge = edge_of.get(node)
            if edge is not None:
                if edge["cond"]:
                    lines.append(spine + "│  条件边")
                if edge["label"] is not None:
                    lines.append(spine + "│  [" + str(edge["label"]) + "]")

        lines.append(spine + "▼")

    return lines


# ============================================================
# 四、画法 B：节点框 + 出边列表（分支 / 循环 / 合并）
# ============================================================

def _render_edges(
    nodes: list[str],
    edges: list[dict],
    back: set[tuple[str, str]],
    node_notes: dict[str, str],
    title: str,
) -> list[str]:
    outgoing: dict[str, list[dict]] = {}
    incoming: dict[str, int] = {}
    for edge in edges:
        outgoing.setdefault(edge["src"], []).append(edge)
        incoming[edge["dst"]] = incoming.get(edge["dst"], 0) + 1

    inner = max(display_width(node) for node in nodes) + 6
    if inner % 2 == 0:
        inner += 1

    lines = [f"\n【{title}】"]
    lines.append("  每个方框是一个节点，框右边列的是它的出边")
    lines.append("  ──→ 普通边    ──条件──→ 条件边    ↺ 回边（循环）")

    for node in nodes:
        pad = inner - display_width(node)
        left = pad // 2
        right = pad - left

        outs = outgoing.get(node, [])
        note = node_notes.get(node, "")

        # 方框上边框
        lines.append("   ┌" + "─" * inner + "┐")

        # 方框中间行：节点名 + 右边挂第一条出边（或备注）
        mid = "   │" + " " * left + node + " " * right + "│"
        if outs:
            mid += "  " + _edge_text(outs[0], back)
        elif note:
            mid += "  " + note
        lines.append(mid.rstrip())

        # 其余出边：每一行都带左边框和右边框，中间留空
        blank_mid = "   │" + " " * inner + "│"
        for edge in outs[1:]:
            lines.append(blank_mid + "  " + _edge_text(edge, back))

        # 方框右边那条竖线不能断：用"空白行 + 竖线"补齐更直观
        if not outs and node != "END":
            lines.append(blank_mid)
            term = "  终点节点" if incoming.get(node, 0) > 0 else "  孤立节点（没人连进来）"
            lines.append("   " + " " * (inner + 5) + term)

        # 备注：出边占用了中间行，备注放到最后一行
        if outs and note:
            lines.append(blank_mid + "  # " + note)

        lines.append("   └" + "─" * inner + "┘")

    if back:
        lines.append("")
        lines.append("  循环（回边）：")
        for src, dst in sorted(back):
            lines.append(f"    {src} ──→ {dst}    执行完回到前面的节点")

    return lines


def _edge_text(edge: dict, back: set[tuple[str, str]]) -> str:
    """一条边画成一行文字。"""
    src, dst = edge["src"], edge["dst"]

    if edge["cond"]:
        text = "──条件──→ " + dst
        if edge["label"] is not None:
            text = f"──条件[{edge['label']}]──→ {dst}"
    else:
        text = "──→ " + dst

    if (src, dst) in back:
        text += "   ↺ 回边"

    return text


# ============================================================
# 五、对外入口
# ============================================================

def draw_flow(
    app: Any,
    node_notes: dict[str, str] | None = None,
    edge_notes: dict[tuple[str, str], list[str]] | None = None,
    branch_targets: dict[str, list[str]] | None = None,
    title: str = "流程图",
) -> None:
    """在终端打印这张图。

    参数
    ----
    app             编译后的图（builder.compile() 的返回值）
    node_notes      节点名 → 框右边的说明
    edge_notes      (起点, 终点) → 箭头上要写几行说明（只对直线图生效）
    branch_targets  源节点 → 条件边能去的节点列表
                    条件边没传显式映射表时必须给，否则分支画不出来
    title           标题
    """
    node_notes = node_notes or {}
    edge_notes = edge_notes or {}

    nodes, edges, _implicit = _collect(app, branch_targets)
    back = _back_edges(nodes, edges)

    if _is_linear(nodes, edges, back):
        order = _linear_order(nodes, edges)
        lines = _render_linear(order, edges, node_notes, edge_notes, title)
    else:
        lines = _render_edges(nodes, edges, back, node_notes, title)

    for line in lines:
        print(line)
    print()
