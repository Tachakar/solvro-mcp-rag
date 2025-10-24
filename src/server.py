from fastmcp import FastMCP
from pathlib import Path
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from typing import Any

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_PATH = (PROJECT_ROOT_DIR / "data")

def _validate_alcohol_related_field(value: Any) -> bool|None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return None

class Ingredient(BaseModel):

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str | None = None
    alcohol: bool | None = None
    type: str | None = None
    percentage: float | None = None
    imageUrl: str | None = None
    measure: str | None = None

    @field_validator("alcohol", mode="before")
    @classmethod
    def _validate_alcohol(cls,value: Any) -> bool|None:
        return _validate_alcohol_related_field(value)

class Cocktail(BaseModel):

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    category: str | None = None
    glass: str | None = None
    tags: list[str] = Field(default_factory=list)
    instructions: str | None = None
    imageUrl: str | None = None
    alcoholic: bool | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)


    @field_validator("alcoholic", mode="before")
    @classmethod
    def _validate_alcoholic(cls,value:Any) -> bool|None:
        return _validate_alcohol_related_field(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _validate_tags(cls, value: Any) -> list:
        if value is None:
            return []
        if isinstance(value,str):
            return [value]
        return value


server = FastMCP(
    name="main_server",
    instructions="""
        Answers questions about cocktails in .json file.
        Suggests cocktails based on taste preferences, preffered ingredients, etc.
    """,
)
def load_cocktails_data():
    cocktail_dataset_path = (DATA_DIR_PATH / "cocktail_dataset.json").resolve()
    try:
        with cocktail_dataset_path.open('r', encoding='utf-8') as file:
            raw_data: list[dict[str,Any]] = json.load(file)
    except FileNotFoundError:
        print(f"File {cocktail_dataset_path} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Parsing error.\nLOG: {e}")
        return []

    cocktails: list[Cocktail] = []
    for entry in raw_data:
        try:
            cocktails.append(Cocktail.model_validate(entry))

        except ValidationError as e:
            cocktail_id = entry.get("id", "<brak_id>")
            print(f"Validation error. Skipping {cocktail_id} LOG: {e}")

    return cocktails

@server.tool(
    name="get_info_by_name",
    description="""
            Tells user informations about cocktail.
        """,
)
def get_cocktail_info(name:str) -> dict|None:
    cocktail = None
    for curr_cocktail in COCKTAILS:
        if curr_cocktail.name.lower() == name.lower():
            cocktail = curr_cocktail
            break
    if cocktail != None:
        return cocktail.model_dump()
    return None

@server.tool(
    name="get_ingredient_info",
    description="""
            Tells user information about ingredient.
    """,
)
def get_ingredient_info(name:str) -> dict|None:
    ingredient = None
    for curr_cocktail in COCKTAILS:
        found = False
        for curr_ingredient in curr_cocktail.ingredients:
            if curr_ingredient.name.lower() == name.lower():
                ingredient = curr_ingredient
                found = True
                break
        if found: break

    if ingredient: return ingredient.model_dump()

    return None

@server.tool(
    name="suggest_cocktail_based_on_ingredients",
    description="""
        Suggests cocktails to the user based
        on the igredients that are mentioned.
    """,
)
def suggest_cocktails_based_on_ingredients(ingredients: list[str], limit:int = 5) -> dict:
    ingredients_lower = {ing.lower() for ing in ingredients}
    results = []
    for cocktail in COCKTAILS:
        matches = 0
        for ingr in cocktail.ingredients:
            if ingr.name and (ingr.name.lower() in ingredients_lower):
                matches += 1
        if matches:
            results.append({"name":cocktail.name, "matches": matches})
    results = sorted(results, key=lambda cocktail: cocktail["matches"], reverse=True)
    return {"suggested_cocktails": results[:limit]}

COCKTAILS = load_cocktails_data()

if __name__ == "__main__":
    server.run(transport="http", host="127.0.0.1", port=8000)
