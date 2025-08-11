from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CalculatorMCP", log_level="ERROR")


@mcp.tool("add")
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    """
    return a + b


@mcp.tool("subtract")
def subtract(a: float, b: float) -> float:
    """
    Subtract b from a.
    """
    return a - b


@mcp.tool("multiply")
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.
    """
    return a * b


@mcp.tool("divide")
def divide(a: float, b: float) -> float:
    """
    Divide a by b.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@mcp.tool("power")
def power(base: float, exponent: float) -> float:
    """
    Raise base to the power of exponent.
    """
    return base ** exponent


if __name__ == "__main__":
    mcp.run(transport="stdio") 