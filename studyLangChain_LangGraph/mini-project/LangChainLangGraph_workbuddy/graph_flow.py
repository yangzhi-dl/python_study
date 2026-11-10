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
# 四、画法 B：分层布线（分支 / 循环 / 合并）
#
# 原理：先把节点按执行层级排成一行行，再让每条边走"下 → 横 → 下"。
# 关键技巧：画布不直接写字符，而是记录每格"往哪几个方向有线段"，
# 最后统一翻译成 ┌┐└┘├┤┬┴┼ —— 拐角、十字、丁字永远不会画错。
# 条件边用 ┆┄ 虚线，普通边用 │─ 实线。
# ============================================================

_SOLID = {
    frozenset("D"): "│", frozenset("U"): "│", frozenset("DU"): "│",
    frozenset("L"): "─", frozenset("R"): "─", frozenset("LR"): "─",
    frozenset("DR"): "┌", frozenset("DL"): "┐",
    frozenset("UR"): "└", frozenset("UL"): "┘",
    frozenset("DUR"): "├", frozenset("DUL"): "┤",
    frozenset("DLR"): "┬", frozenset("ULR"): "┴",
    frozenset("DULR"): "┼",
}
_DASHED = {
    frozenset("U"): "┆", frozenset("D"): "┆", frozenset("DU"): "┆",
    frozenset("L"): "┄", frozenset("R"): "┄", frozenset("LR"): "┄",
}


class _Grid:
    """方向掩码画布。"""

    def __init__(self) -> None:
        self.dirs: dict[tuple[int, int], set[str]] = {}
        self.text: dict[tuple[int, int], str] = {}
        self.dashed: set[tuple[int, int]] = set()

    def add(self, row: int, col: int, direction: str, dashed: bool = False) -> None:
        self.dirs.setdefault((row, col), set()).add(direction)
        if dashed:
            self.dashed.add((row, col))

    def hline(self, row: int, col1: int, col2: int, dashed: bool = False) -> None:
        lo, hi = min(col1, col2), max(col1, col2)
        for c in range(lo, hi + 1):
            if c < hi:
                self.add(row, c, "R", dashed)
            if c > lo:
                self.add(row, c, "L", dashed)

    def vline(self, col: int, row1: int, row2: int, dashed: bool = False) -> None:
        lo, hi = min(row1, row2), max(row1, row2)
        for r in range(lo, hi + 1):
            if r < hi:
                self.add(r, col, "D", dashed)
            if r > lo:
                self.add(r, col, "U", dashed)

    def put(self, row: int, col: int, text: str) -> None:
        x = col
        for char in text:
            self.text[(row, x)] = char
            if display_width(char) == 2:
                self.text[(row, x + 1)] = ""
            x += 2 if display_width(char) == 2 else 1

    def render(self) -> list[str]:
        points = list(self.dirs) + list(self.text)
        if not points:
            return []
        max_row = max(r for r, _ in points)
        max_col = max(c for _, c in points)
        lines: list[str] = []
        for r in range(max_row + 1):
            buf: list[str] = []
            for c in range(max_col + 1):
                if (r, c) in self.text:
                    buf.append(self.text[(r, c)])
                elif (r, c) in self.dirs:
                    mask = frozenset(self.dirs[(r, c)])
                    table = _DASHED if (r, c) in self.dashed else _SOLID
                    buf.append(table.get(mask) or _SOLID.get(mask) or " ")
                else:
                    buf.append(" ")
            lines.append("".join(buf).rstrip())
        while lines and not lines[-1]:
            lines.pop()
        return lines


def _ranks(nodes: list[str], edges: list[dict], back: set[tuple[str, str]]) -> dict[str, int]:
    """按最长路径分层：同一层 = 可以并行的节点。"""
    rank = {node: 0 for node in nodes}
    forward = [
        e for e in edges
        if e["dst"] in rank and (e["src"], e["dst"]) not in back
    ]
    for _ in range(len(nodes) + 2):
        changed = False
        for edge in forward:
            if edge["dst"] == "START":
                continue
            want = rank[edge["src"]] + 1
            if rank[edge["dst"]] < want:
                rank[edge["dst"]] = want
                changed = True
        if not changed:
            break
    return rank


def _render_layered(
    nodes: list[str],
    edges: list[dict],
    back: set[tuple[str, str]],
    node_notes: dict[str, str],
    title: str,
) -> list[str]:
    index_of = {node: i for i, node in enumerate(nodes)}
    forward = [e for e in edges if (e["src"], e["dst"]) not in back]
    backs = [e for e in edges if (e["src"], e["dst"]) in back]
    rank = _ranks(nodes, edges, back)

    layers: dict[int, list[str]] = {}
    for node in nodes:
        layers.setdefault(rank[node], []).append(node)
    rank_keys = sorted(layers)
    for key in rank_keys:
        layers[key].sort(key=lambda n: index_of[n])

    # ---------- 横向位置：父节点居中 ----------
    box_w = max(display_width(n) for n in nodes) + 8
    if box_w % 2 == 0:
        box_w += 1
    inner = box_w - 2
    gap_x = 12
    left_pad = 4 + len(backs) * 2

    x: dict[str, float] = {}
    for key in rank_keys:
        ordered = sorted(layers[key], key=lambda n: index_of[n])
        for i, node in enumerate(ordered):
            parents = [
                x[e["src"]] for e in forward
                if e["dst"] == node and rank[e["src"]] < key and e["src"] in x
            ]
            x[node] = sum(parents) / len(parents) if parents else float(i * (box_w + gap_x))

        ordered = sorted(ordered, key=lambda n: (x[n], index_of[n]))
        for i in range(1, len(ordered)):
            prev, cur = ordered[i - 1], ordered[i]
            min_x = x[prev] + box_w + gap_x
            if x[cur] < min_x:
                x[cur] = min_x
        layers[key] = ordered

    shift = min(x.values()) - left_pad
    x = {n: int(v - shift) for n, v in x.items()}

    # ---------- 竖向位置 ----------
    lanes: dict[int, list[dict]] = {}
    for edge in forward:
        lanes.setdefault(rank[edge["src"]], []).append(edge)

    def gap_height(key: int) -> int:
        group = lanes.get(key, [])
        if not group:
            return 0
        crossing = [e for e in group if x[e["src"]] != x[e["dst"]]]
        return 1 + len(crossing) + 1

    y: dict[str, int] = {}
    gap_top: dict[int, int] = {}
    cursor = 0
    for key in rank_keys:
        for node in layers[key]:
            y[node] = cursor
        cursor += 3
        gap_top[key] = cursor
        cursor += gap_height(key)

    # ---------- 通道行分配 ----------
    lane_row: dict[int, int | None] = {}
    for key in rank_keys:
        group = lanes.get(key, [])
        crossing = [e for e in group if x[e["src"]] != x[e["dst"]]]
        straight = [e for e in group if x[e["src"]] == x[e["dst"]]]
        crossing.sort(key=lambda e: abs(x[e["src"]] - x[e["dst"]]))
        for i, edge in enumerate(crossing):
            lane_row[id(edge)] = gap_top[key] + 1 + i
        for edge in straight:
            lane_row[id(edge)] = None

    # ---------- 画 ----------
    grid = _Grid()
    for node in nodes:
        bx, by = x[node], y[node]
        pad = inner - display_width(node)
        left = pad // 2
        right = pad - left
        grid.put(by, bx, "┌" + "─" * inner + "┐")
        grid.put(by + 1, bx, "│" + " " * left + node + " " * right + "│")
        grid.put(by + 2, bx, "└" + "─" * inner + "┘")

    labels: list[tuple[int, int, str]] = []
    for key in rank_keys:
        for edge in lanes.get(key, []):
            sx = x[edge["src"]] + box_w // 2
            tx = x[edge["dst"]] + box_w // 2
            sy = y[edge["src"]] + 3
            ty = y[edge["dst"]]
            lane = lane_row[id(edge)]
            dashed = edge["cond"]
            join_row = ty - 1

            if lane is None:
                grid.vline(sx, sy, join_row, dashed)
            else:
                grid.vline(sx, sy, lane, dashed)
                grid.hline(lane, sx, tx, dashed)
                grid.vline(tx, lane, join_row, dashed)

            grid.put(join_row, tx, "▼")

            tag = f"[{edge['label']}]" if edge["label"] is not None else ("[条件]" if edge["cond"] else None)
            if tag and abs(sx - tx) >= display_width(tag) + 6:
                labels.append((lane, min(sx, tx) + 2, tag))

    for row, col, tag in labels:
        free = True
        for c in range(col, col + display_width(tag)):
            if (row, c) in grid.text:
                free = False
                break
            directions = grid.dirs.get((row, c))
            if directions and (set(directions) - {"L", "R"}):
                free = False
                break
        if free:
            grid.put(row, col, tag)

    # ---------- 回边（循环）：走左侧 ----------
    for i, edge in enumerate(backs):
        lane_col = 1 + i * 2
        if edge["src"] == edge["dst"]:
            top = y[edge["src"]] - 1
            grid.hline(y[edge["src"]] + 1, x[edge["src"]] - 2, lane_col, True)
            grid.vline(lane_col, top, y[edge["src"]] + 1, True)
            grid.hline(top, lane_col, x[edge["src"]] + box_w // 2, True)
            grid.put(top, x[edge["src"]] + box_w // 2, "▼")
        else:
            src_row = y[edge["src"]] + 1
            dst_row = y[edge["dst"]] + 1
            grid.hline(src_row, x[edge["src"]] - 2, lane_col, True)
            grid.vline(lane_col, src_row, dst_row, True)
            grid.hline(dst_row, lane_col, x[edge["dst"]] - 2, True)
            grid.put(dst_row, x[edge["dst"]] - 2, "▶")

    lines = [f"\n【{title}】"]
    lines.extend("   " + row for row in grid.render())
    lines.append("")
    lines.append("  ── 实线 = 普通边（写死，必走）")
    lines.append("  ┄┄ 虚线 = 条件边（由 route 函数决定走哪条）")
    if backs:
        lines.append("  左侧虚线 = 循环回边")

    notes = [(n, node_notes[n]) for n in nodes if n in node_notes]
    if notes:
        lines.append("")
        for node, note in notes:
            lines.append(f"    {node}：{note}")
    return lines


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
        lines = _render_layered(nodes, edges, back, node_notes, title)

    for line in lines:
        print(line)
    print()
