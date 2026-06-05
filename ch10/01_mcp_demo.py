"""第10章 MCP demo：自定义一个合法 MCP server，并用 MCPTool 连接、发现、调用它。
这套"发现→调用"机制就是 Capstone 里"第三方 skill"的真实形态。
运行: cd hello-agents-lab && .venv/bin/python ch10/01_mcp_demo.py
"""
from fastmcp import FastMCP
from hello_agents.tools import MCPTool

# ---------- 1) 构建一个合法的自定义 MCP server（FastMCP）----------
weather = FastMCP("WeatherSkill")
_FAKE_DB = {"北京": "晴 26°C", "上海": "多云 24°C", "广州": "雷阵雨 30°C"}

@weather.tool()
def get_weather(city: str) -> str:
    """查询某城市的当前天气。"""
    return _FAKE_DB.get(city, f"暂无 {city} 的数据")

@weather.tool()
def list_cities() -> list:
    """列出支持的城市。"""
    return list(_FAKE_DB.keys())

# ---------- 2) 用 MCPTool 把 server 挂成 agent 可用的工具（内存传输）----------
mcp = MCPTool(name="weather", server=weather)

print("=" * 60)
print("MCP：自动发现 server 暴露的工具（list_tools）")
print("=" * 60)
print(mcp.run({"action": "list_tools"}))

print("\n" + "=" * 60)
print("MCP：调用工具")
print("=" * 60)
print(mcp.run({"action": "call_tool", "tool_name": "get_weather", "arguments": {"city": "北京"}}))
print(mcp.run({"action": "call_tool", "tool_name": "list_cities", "arguments": {}}))
