# Solvro ML - MCP+RAG solution
Implementation of MCP using FastMCP, integrated with a RAG system built on LlamaIndex.
The tool answers questions about cocktails and their ingredients, and can suggest drinks based on given ingredients or flavor preferences.

# Video preview - [> here <](https://youtu.be/XrUeqt3Ih5A)

# Installation
1. Clone this repo `git clone git@github.com:Tachakar/solvro-mcp-rag.git` and run `cd solvro-mcp-rag`
2. Make sure you have installed [uv](https://github.com/astral-sh/uv)
3. Run `uv sync --locked` 
4. Install [ollama](https://ollama.com/download/linux) and [llama3.2:3b](https://ollama.com/library/llama3.2:3b)
5. Run `python3 src/server.py`

Now your server is running, for testing I've connected it to Codex CLI

```codex mcp add --url http://127.0.0.1:8000/mcp <server_name>```

For different AI CLIs you might want to read official docs on how to do it.

# How it works
1. Load data from data/cocktail_dataset.json file and clean it using Pydantic models.
2. Prepare [Documents and Nodes](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/), build [Indexes](https://developers.llamaindex.ai/python/framework/module_guides/indexing/) from them,
   then build our [Query Engine](https://developers.llamaindex.ai/python/framework/module_guides/deploying/query_engine/usage_pattern/).
3. On the server side we have server class with tools that handle questions. For simple information about specific cocktail/ingredient we don't use our RAG, for more complex queries/general questions, we use it.

The data comes from [TheCocktailDB](https://www.thecocktaildb.com/)
