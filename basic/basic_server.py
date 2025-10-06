from fastmcp import FastMCP

mcp = FastMCP("GreetServer")


@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(transport="stdio")
