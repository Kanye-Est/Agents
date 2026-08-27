"""良性 skill：计算器。"""
# 安全的算式求值：只允许数字和加减乘除括号，防止代码注入。
import ast
import operator

# 白名单：只允许这几种 AST 节点（数字 + 基础运算符）
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,   # 负号
    ast.Pow: operator.pow,
}


def _eval(node):
    if isinstance(node, ast.Num):           # 数字
        return node.n
    if isinstance(node, ast.BinOp):         # 二元运算 a + b
        return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):       # 一元运算 -a
        return _SAFE_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("不支持的表达式")


def run(args):
    expr = (args or {}).get("input", "").strip()
    if not expr:
        return "请提供算式，例如：3+5*2"
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree.body)
        return f"{expr} = {result}"
    except Exception as e:
        return f"无法计算「{expr}」: {e}"
