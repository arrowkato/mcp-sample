from mcp.server import FastMCP

server = FastMCP(name="mcp-sample-server")


@server.tool()
async def echo(text: str) -> str:
    """与えられた文字列をそのまま返します。"""
    return text


@server.tool()
async def add(a: float, b: float) -> float:
    """2つの数値を加算して返します。"""
    return a + b


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
