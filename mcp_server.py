from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool("read_document")
def read_document(doc_id: str) -> str:
    """
    Returns the content of the specified document.
    """
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found.")
    return docs[doc_id]

@mcp.tool("edit_document")
def edit_document(doc_id: str, new_content: str) -> str:
    """
    Updates the content of the specified document.
    """
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found.")
    docs[doc_id] = new_content
    return f"Document '{doc_id}' updated successfully."

# TODO: Write a resource to return all doc id's
# TODO: Write a resource to return the contents of a particular doc
# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
