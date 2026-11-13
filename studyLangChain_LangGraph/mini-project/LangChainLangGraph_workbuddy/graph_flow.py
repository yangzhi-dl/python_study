"""LangGraph 图结构打印工具（ch02_0x 共用）。

用法（一行）：
    from graph_flow import draw_flow
    draw_flow(app, title="Demo 3 · 流程图")

三种画法自动选择：
  1. 直线图（每个节点最多一进一出，且没有子图）
     竖排方框 + 箭头，箭头上可以写这一步 State 怎么变
  2. 分支 / 循环 / 合并
     每个节点一个方框，框右边列出它的所有出边
  3. 含子图
     子图节点画成一个"大框"，框里再画子图自己的
     START → 节点 → END，和 LangGraph 官方图里那个
     黄底方框的位置、含义一致

⚠ 一个必须知道的坑
  条件边如果【没传显式映射表】，例如：
      builder.add_conditional_edges("judge", route)
  LangGraph 自己也记不住分支能去哪 —— get_graph() 里只剩一条伪造的
  "judge → END"。这种图必须用 branch_targets 告诉绘制器：
      draw_flow(app, branch_targets={"judge": ["pass", "retry"]})

⚠ 第二个坑（子图相关）
  子图是自动识别的：只要 add_node 传进去的是 builder.compile() 的
  结果，就会被当成子图展开。如果外层又套了 Runnable / lambda，
  自动识别会失败，这时显式告诉绘制器：
      draw_flow(app, subgraphs={"child": sub_graph})
"""

from __future__ import annotations

import unicodedata
from typing import Any

_DISPLAY = {"__start__": "START", "__end__": "END"}

# 子图最多展开几层，防止三层嵌套把终端刷爆
_MAX_SUBGRAPH_DEPTH = 3


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


def _builder_nodes(builder: Any):
    """遍历 builder 里注册的每个节点，产出 (节点名, 该节点实际执行的对象)。"""
    specs = getattr(builder, "nodes", None)
    if not isinstance(specs, dict):
        return
    for name, spec in specs.items():
        runnable = getattr(spec, "runnable", None)
        if runnable is None and isinstance(spec, dict):
            runnable = spec.get("runnable")
        if runnable is not None:
            yield name, runnable


def _detect_subgraphs(app: Any) -> dict[str, Any]:
    """找出哪些节点本身是一张编译好的图。

    判据：这个 runnable 既能 get_graph()，又带着自己的 builder.nodes，
    那就是 StateGraph(...).compile() 的产物（Pregel / CompiledStateGraph）。
    """
    found: dict[str, Any] = {}
    for name, runnable in _builder_nodes(getattr(app, "builder", None)):
        inner_builder = getattr(runnable, "builder", None)
        if inner_builder is None or not hasattr(inner_builder, "nodes"):
            continue
        if not hasattr(runnable, "get_graph"):
            continue
        found[_normalize(name)] = runnable
    return found


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

def _set_char(line: str, col: int, char: str) -> str:
    """把 line 里"显示第 col 列"的字符换成 char（中文占两格也不串位）。"""
    out: list[str] = []
    width = 0
    for ch in line:
        w = display_width(ch)
        if width == col:
            out.append(char)
            if w == 2:
                # 原来这里是个汉字，被替换后空出一格
                out.append(" ")
        else:
            out.append(ch)
        width += w
    return "".join(out)


def _box_lines(
    node: str,
    shapes: dict[str, tuple[str, str, list[str], int, int]],
    total: int,
) -> tuple[list[str], int]:
    """把这个节点画成一个方框（子图则是带标题的容器），在 total 宽里居中。

    返回 (行列表, 框中心所在的列)。
    """
    kind, label, inner, bw, _bh = shapes[node]

    if kind == "plain":
        body = _plain_rows(label, bw)
    else:
        body = _sub_rows(label, bw, inner)

    shift = (total - bw) // 2
    # 框宽是奇数，中心列（0 起算）就是 shift + bw // 2
    return [" " * shift + row for row in body], shift + bw // 2


def _render_linear(
    order: list[str],
    edges: list[dict],
    node_notes: dict[str, str],
    edge_notes: dict[tuple[str, str], list[str]],
    title: str,
    shapes: dict[str, tuple[str, str, list[str], int, int]] | None = None,
) -> list[str]:
    edge_of = {edge["src"]: edge for edge in edges}
    shapes = dict(shapes or {})

    for node in order:
        if node not in shapes:
            shapes[node] = ("plain", node, [], _box_width(node), 3)

    indent = 2
    # 所有框宽都是奇数，总宽也取奇数，(总宽 - 框宽) 才能整除，框才能真正居中
    total = max(shapes[n][3] for n in order)
    if total % 2 == 0:
        total += 1

    lines: list[str] = [f"\n【{title}】"]
    if any(shape[0] == "sub" for shape in shapes.values()):
        lines.append("  （带标题的大框 = 子图，框里是子图自己那张图）")

    for index, node in enumerate(order):
        box, mid = _box_lines(node, shapes, total)
        is_last = index == len(order) - 1
        note = node_notes.get(node)
        is_sub = shapes[node][0] == "sub"

        for i, row in enumerate(box):
            text = " " * indent + row.rstrip()
            # 说明统一推到同一列，多行说明才不会锯齿
            text += " " * max(indent + total + 3 - display_width(text), 0)
            if note and ((not is_sub and i == 1) or (is_sub and i == 0)):
                text += note
            lines.append(text.rstrip())

        if is_last:
            break

        # 底边中间挖个 ┬，接出竖线
        bottom = lines[-1]
        if display_width(bottom) <= indent + mid:
            bottom += " " * (indent + mid + 1 - display_width(bottom))
        lines[-1] = _set_char(bottom, indent + mid, "┬").rstrip()

        spine = " " * (indent + mid)
        key = (node, order[index + 1])
        note_lines = edge_notes.get(key, [])
        if not note_lines:
            edge = edge_of.get(node)
            if edge is not None:
                if edge["cond"]:
                    note_lines = ["条件边"]
                if edge["label"] is not None:
                    note_lines = note_lines + ["[" + str(edge["label"]) + "]"]

        # 只有一条说明时并到箭头那一行，省掉两行竖线
        if len(note_lines) <= 1:
            tag = (" " + note_lines[0]) if note_lines else ""
            lines.append(spine + "▼" + tag)
        else:
            lines.append(spine + "┆")
            for text in note_lines[:-1]:
                lines.append(spine + "┆  " + text)
            lines.append(spine + "▼  " + note_lines[-1])

    return lines


# ============================================================
# 四、画法 B：分层布线（分支 / 循环 / 合并 / 子图）
#
# 原理：先把节点按执行层级排成一行行，再让每条边走"下 → 横 → 下"。
# 关键技巧：画布不直接写字符，而是记录每格"往哪几个方向有线段"，
# 最后统一翻译成 ┌┐└┘├┤┬┴┼ —— 拐角、十字、丁字永远不会画错。
# 条件边用 ┆┄ 虚线，普通边用 │─ 实线。
#
# 子图：节点尺寸不再是统一大小时，布局仍然成立 ——
# 每个节点单独记 (宽, 高)，父节点按"子节点中心"对齐。
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


def _box_width(label: str) -> int:
    """普通节点方框的宽度（含左右边框）。奇数宽 → 才能精确居中。"""
    width = display_width(label) + 4
    return width if width % 2 == 1 else width + 1


def _container_top(label: str, width: int) -> str:
    """子图容器的顶边，标题居中：┌──── child ────┐"""
    inner = width - 2
    text = f" {label} "
    dash = inner - display_width(text)
    if dash < 0:
        return "┌" + label + "┐"
    left = dash // 2
    right = dash - left
    return "┌" + "─" * left + text + "─" * right + "┐"


def _plain_rows(label: str, bw: int) -> list[str]:
    bwi = bw - 2
    pad = bwi - display_width(label)
    left = max(pad // 2, 0)
    right = max(pad - left, 0)
    # START / END 用圆角，对应官图里的椭圆
    tl, tr, bl, br = ("╭", "╮", "╰", "╯") if label in ("START", "END") else ("┌", "┐", "└", "┘")
    return [
        tl + "─" * bwi + tr,
        "│" + " " * left + label + " " * right + "│",
        bl + "─" * bwi + br,
    ]


def _sub_rows(label: str, bw: int, inner: list[str]) -> list[str]:
    """子图容器：顶边 + 内部整图（同一偏移，箭头不会错位）+ 底边。"""
    bwi = bw - 2
    inner_w = max((display_width(text) for text in inner), default=0)
    pre = max((bwi - inner_w) // 2, 0)
    rows = [_container_top(label, bw)]
    for text in inner:
        fill = max(bwi - pre - display_width(text), 0)
        rows.append("│" + " " * pre + text + " " * fill + "│")
    rows.append("└" + "─" * bwi + "┘")
    return rows


def _shapes(
    nodes: list[str],
    subgraphs: dict[str, Any],
    depth: int,
) -> dict[str, tuple[str, str, list[str], int, int]]:
    """算出每个节点的 (类型, 标签, 内部行, 宽, 高)。

    类型 "plain" ：普通方框，高 3
    类型 "sub"   ：子图容器
                  行 0     顶边 ┌──── 名字 ────┐
                  行 1..n  子图自己的图
                  行 n+1   底边
    容器做到"刚刚好包住内部那张图"，上下不留空白，整体才紧凑。
    """
    shapes: dict[str, tuple[str, str, list[str], int, int]] = {}
    for node in nodes:
        child = subgraphs.get(node)
        if child is not None and depth < _MAX_SUBGRAPH_DEPTH:
            inner = _render_body(child, depth + 1)
            inner_w = max((display_width(line) for line in inner), default=0)
            # 左右各留 2 格内边距；宽度至少放得下标题
            width = max(inner_w + 4, display_width(node) + 6, 9)
            if width % 2 == 0:
                width += 1
            # 高度 = 顶边 1 + 内部 len(inner) + 底边 1
            shapes[node] = ("sub", node, inner, width, len(inner) + 2)
        else:
            width = _box_width(node)
            shapes[node] = ("plain", node, [], width, 3)
    return shapes


def _render_body(app: Any, depth: int = 0) -> list[str]:
    """把一张图渲染成"纯图形"行列表（不带标题、不带图例），供递归嵌套使用。

    直线型子图用紧凑的 [ 节点 ] 单行卡片，含分支/循环的才走完整分层布线，
    否则一个 a → b 的子图会被撑成二十来行，父图就不堪入目了。
    """
    nodes, edges, _implicit = _collect(app)
    if not nodes:
        return []
    subgraphs = _detect_subgraphs(app)
    back = _back_edges(nodes, edges)

    if _is_linear(nodes, edges, back) and not subgraphs:
        return _body_compact(_linear_order(nodes, edges), edges)
    return _body_layered(nodes, edges, back, subgraphs, depth)


def _body_compact(order: list[str], edges: list[dict]) -> list[str]:
    """紧凑画法：一个节点一行，节点之间只有一行 ▼。"""
    arrow_of = {edge["src"]: edge for edge in edges}
    card_w = max(display_width(node) for node in order) + 2
    if card_w % 2 == 0:
        card_w += 1
    centre_col = (card_w + 2) // 2          # 卡片总宽 = card_w + 2

    lines: list[str] = []
    for index, node in enumerate(order):
        pad = card_w - display_width(node)
        left = pad // 2
        body = " " * left + node + " " * (pad - left)
        # 首尾用圆角括号，对应官图里的椭圆
        if node in ("START", "END"):
            lines.append("(" + body + ")")
        else:
            lines.append("[" + body + "]")

        if index == len(order) - 1:
            break

        edge = arrow_of.get(node)
        tag = ""
        if edge is not None and edge["label"] is not None:
            label = str(edge["label"])
            if label.lower() != order[index + 1].lower():
                tag = f" [{label}]"
        lines.append(" " * centre_col + "▼" + tag)
    return lines


def _body_layered(
    nodes: list[str],
    edges: list[dict],
    back: set[tuple[str, str]],
    subgraphs: dict[str, Any],
    depth: int,
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

    shapes = _shapes(nodes, subgraphs, depth)
    width = {n: shapes[n][3] for n in nodes}
    height = {n: shapes[n][4] for n in nodes}

    def centre(n: str) -> int:
        return x[n] + width[n] // 2

    # ---------- 横向位置：父节点居中 ----------
    gap_x = 8
    # 正文左边留白：回边车道占 2..，再空 2 格才到第一个框
    left_pad = 4 + len(backs) * 2
    widest = max(width.values()) if width else 10

    x: dict[str, float] = {}
    for key in rank_keys:
        ordered = layers[key]
        for i, node in enumerate(ordered):
            parents = [
                x[e["src"]] + width[e["src"]] // 2 - width[node] // 2
                for e in forward
                if e["dst"] == node and rank[e["src"]] < key and e["src"] in x
            ]
            x[node] = sum(parents) / len(parents) if parents else float(i * (widest + gap_x))

        ordered = sorted(ordered, key=lambda n: (x[n], index_of[n]))
        for i in range(1, len(ordered)):
            prev, cur = ordered[i - 1], ordered[i]
            min_x = x[prev] + width[prev] + gap_x
            if x[cur] < min_x:
                x[cur] = min_x
        layers[key] = ordered

    shift = min(x.values()) - left_pad
    for node in list(x):
        x[node] = int(x[node] - shift)

    # ---------- 竖向位置 ----------
    lanes: dict[int, list[dict]] = {}
    for edge in forward:
        lanes.setdefault(rank[edge["src"]], []).append(edge)

    def crossing_of(key: int) -> list[dict]:
        return [e for e in lanes.get(key, []) if x[e["src"]] + width[e["src"]] // 2
                != x[e["dst"]] + width[e["dst"]] // 2]

    y: dict[str, int] = {}
    gap_top: dict[int, int] = {}
    cursor = 0
    for key in rank_keys:
        tallest = max(height[n] for n in layers[key])
        for node in layers[key]:
            # 同一层高度不一致时（子图框比普通框高），小的那个垂直居中
            y[node] = cursor + (tallest - height[node]) // 2
        cursor += tallest
        gap_top[key] = cursor
        # 1 行留白 + 每条跨列边走一条横向通道 + 1 行留白
        cursor += 1 + len(crossing_of(key)) + 1

    # ---------- 通道行分配 ----------
    lane_row: dict[int, int | None] = {}
    for key in rank_keys:
        group = lanes.get(key, [])
        crossing = crossing_of(key)
        crossing_ids = {id(e) for e in crossing}
        straight = [e for e in group if id(e) not in crossing_ids]
        crossing.sort(key=lambda e: abs(centre(e["src"]) - centre(e["dst"])))
        for i, edge in enumerate(crossing):
            lane_row[id(edge)] = gap_top[key] + 1 + i
        for edge in straight:
            lane_row[id(edge)] = None

    # ---------- 画节点 ----------
    grid = _Grid()
    for node in nodes:
        kind, label, inner, bw, _bh = shapes[node]
        bx, by = x[node], y[node]

        rows = _plain_rows(label, bw) if kind == "plain" else _sub_rows(label, bw, inner)
        for i, row in enumerate(rows):
            grid.put(by + i, bx, row)

    # ---------- 画边 ----------
    labels: list[tuple[int, int, str]] = []
    for key in rank_keys:
        for edge in lanes.get(key, []):
            sx, tx = centre(edge["src"]), centre(edge["dst"])
            sy = y[edge["src"]] + height[edge["src"]]
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

            # 只标显式分支名，且分支名和目标节点同名时也没必要标
            #（如 {"chat": "chat"}）—— 目标框上已经写着 chat 了
            if edge["label"] is None:
                continue
            if str(edge["label"]).lower() == edge["dst"].lower():
                continue
            tag = f"[{edge['label']}]"
            room = abs(sx - tx)
            if room < display_width(tag) + 4:
                continue
            row = lane if lane is not None else join_row - 1
            # 贴着自己那条竖线的起点放，读者一眼能看出是哪一支
            if sx < tx:
                col = sx + 2
            else:
                col = sx - 2 - display_width(tag)
            if col < 0 or (sx < tx and col + display_width(tag) >= tx):
                col = min(sx, tx) + 2
            labels.append((row, col, tag))

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
        lane_col = 2 + i * 2      # 留出 0/1 列，嵌进容器时不贴边框
        s, d = edge["src"], edge["dst"]
        if s == d:
            top = y[s] - 1
            mid = y[s] + height[s] // 2
            grid.hline(mid, x[s] - 2, lane_col, True)
            grid.vline(lane_col, top, mid, True)
            grid.hline(top, lane_col, centre(s), True)
            grid.put(top, centre(s), "▼")
        else:
            src_row = y[s] + height[s] // 2
            dst_row = y[d] + height[d] // 2
            grid.hline(src_row, x[s] - 2, lane_col, True)
            grid.vline(lane_col, src_row, dst_row, True)
            grid.hline(dst_row, lane_col, x[d] - 2, True)
            grid.put(dst_row, x[d] - 2, "▶")

    return grid.render()


def _render_layered(
    nodes: list[str],
    edges: list[dict],
    back: set[tuple[str, str]],
    node_notes: dict[str, str],
    title: str,
    subgraphs: dict[str, Any],
    depth: int = 0,
) -> list[str]:
    body = _body_layered(nodes, edges, back, subgraphs, depth)
    if not body:
        return [f"\n【{title}】", "  （空图）"]

    lines = [f"\n【{title}】"]
    lines.extend("   " + row for row in body)
    lines.append("")
    lines.append("  ── 实线 = 普通边（写死，必走）")
    lines.append("  ┄┄ 虚线 = 条件边（由 route 函数决定走哪条）")
    if back:
        lines.append("  左侧虚线 = 循环回边")
    if subgraphs:
        lines.append("  ┌──── 名字 ────┐ 的大框 = 子图：框里是它自己那张图")

    notes = [(n, node_notes[n]) for n in nodes if n in node_notes]
    if notes:
        lines.append("")
        for node, note in notes:
            tag = "（子图）" if node in subgraphs else ""
            lines.append(f"    {node}{tag}：{note}")
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
    subgraphs: dict[str, Any] | None = None,
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
    subgraphs       节点名 → 子图。默认自动识别，识别不出来时用它兜底
    """
    node_notes = node_notes or {}
    edge_notes = edge_notes or {}

    nodes, edges, _ = _collect(app, branch_targets)
    back = _back_edges(nodes, edges)

    found = _detect_subgraphs(app)
    if subgraphs:
        found.update(subgraphs)
    found = {name: sub for name, sub in found.items() if name in nodes}

    if _is_linear(nodes, edges, back):
        order = _linear_order(nodes, edges)
        shapes = _shapes(nodes, found, 0) if found else None
        lines = _render_linear(order, edges, node_notes, edge_notes, title, shapes)
    else:
        lines = _render_layered(nodes, edges, back, node_notes, title, found)

    for line in lines:
        print(line)
    print()
