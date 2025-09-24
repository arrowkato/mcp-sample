import asyncio

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def amain() -> None:
    server_params = StdioServerParameters(command="python", args=["server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool("echo", {"text": "hello mcp"})
            texts = [c.text for c in result.content if hasattr(c, "text")]
            print("echo ->", texts)

            result = await session.call_tool("add", {"a": 1, "b": 2})
            # structuredContent が設定される実装もあるが、ここでは content の Text を拾う
            structured = getattr(result, "structuredContent", None)
            print(
                "add ->",
                structured
                or [getattr(c, "text", None) for c in result.content],
            )


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
