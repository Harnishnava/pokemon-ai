from langchain.llms import OpenAI
from langchain.tools import RequestsGetTool

# Use your Glama MCP Server URL
pokemon_api = RequestsGetTool(
    name="Get Pokemon List",
    description="Fetches all Pokémon names",
    url="https://your-mcp-server.glama.ai/getPokemonList"
)

# AI Model
llm = OpenAI(model="gpt-4", openai_api_key="your-api-key")

query = "List all Pokémon"
pokemon_list = pokemon_api.run({})
response = llm(f"Here are all Pokémon: {pokemon_list}")

print(response)
