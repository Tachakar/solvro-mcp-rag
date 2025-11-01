from fastmcp import FastMCP
from rag import COCKTAILS, INGREDIENTS, get_cocktails_query_engine

server = FastMCP(
    name="main_server",
    instructions="""
        Answers questions about cocktails.
        Suggests cocktails based on taste preferences, preferred ingredients, etc.
    """,
)
query_engine = get_cocktails_query_engine()

@server.tool(
    description="""
        Answers general questions about cocktails and ingredients.
    """
)
def ask_question(question:str)-> dict:
    response = query_engine.query(question)
    return {"answer": str(response)}


@server.tool(
    description="""
            Tells user informations about cocktail.
        """,
)
def get_cocktail_info(name: str) -> dict:
    for curr_cocktail in COCKTAILS:
        if curr_cocktail.name.lower() == name.lower():
            return curr_cocktail.model_dump()

    fallback = query_engine.query(f"Tell me about {name}")

    return {"answer": str(fallback)}


@server.tool(
    description="""
            Tells user information about ingredient.
    """,
)
def get_ingredient_info(name: str) -> dict:
    for ingredient in INGREDIENTS:
        if ingredient.name and (ingredient.name.lower() == name.lower()):
            return ingredient.model_dump()

    fallback = query_engine.query(f"Tell me about {name}")

    return {"answer": str(fallback)}


@server.tool(
    description="""
        Suggests cocktails to the user based
        on the ingredients that are mentioned.
    """,
)
def suggest_cocktails_based_on_ingredients(
    ingredients: list[str], limit: int = 3
) -> dict:
    ingredients_lower = {ing.lower() for ing in ingredients}
    results = []
    for cocktail in COCKTAILS:
        matches = 0
        for ingr in cocktail.ingredients:
            if ingr.name and (ingr.name.lower() in ingredients_lower):
                matches += 1
        if matches:
            results.append({"name": cocktail.name, "matches": matches})
    results = sorted(results, key=lambda cocktail: cocktail["matches"], reverse=True)
    return {"suggested_cocktails": results[:limit]}



if __name__ == "__main__":
    server.run(transport="http", host="127.0.0.1", port=8000)
