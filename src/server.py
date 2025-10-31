from fastmcp import FastMCP
from pathlib import Path
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from typing import Any

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_PATH = PROJECT_ROOT_DIR / "data"


def _validate_alcohol_related_field(value: Any) -> bool | None:
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
    def _validate_alcohol(cls, value: Any) -> bool | None:
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
    def _validate_alcoholic(cls, value: Any) -> bool | None:
        return _validate_alcohol_related_field(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _validate_tags(cls, value: Any) -> list:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


server = FastMCP(
    name="main_server",
    instructions="""
        Answers questions about cocktails.
        Suggests cocktails based on taste preferences, preferred ingredients, etc.
    """,
)


def load_ingredients_data() -> list[Ingredient]:
    ingredients: list[Ingredient] = []
    for cocktail in COCKTAILS:
        for ingredient in cocktail.ingredients:
            # Ignore measure to avoid dupplicates in INGREDIENTS list
            copy = ingredient.model_copy(update={"measure": None})
            if copy not in ingredients:
                ingredients.append(copy)

    return ingredients


def load_cocktails_data() -> list[Cocktail]:
    cocktail_dataset_path = (DATA_DIR_PATH / "cocktail_dataset.json").resolve()
    try:
        with cocktail_dataset_path.open("r", encoding="utf-8") as file:
            raw_data: list[dict[str, Any]] = json.load(file)
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
            cocktail_id = entry.get("id", "<missing_id>")
            print(f"Validation error. Skipping {cocktail_id} LOG: {e}")

    return cocktails


@server.tool(
    description="""
            Tells user informations about cocktail.
        """,
)
def get_cocktail_info(name: str) -> dict:
    for curr_cocktail in COCKTAILS:
        if curr_cocktail.name.lower() == name.lower():
            return curr_cocktail.model_dump()

    return {"error": "Not found"}


@server.tool(
    description="""
            Tells user information about ingredient.
    """,
)
def get_ingredient_info(name: str) -> dict:
    for ingredient in INGREDIENTS:
        if ingredient.name and (ingredient.name.lower() == name.lower()):
            return ingredient.model_dump()

    return {"error": "Not found"}


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


COCKTAILS = load_cocktails_data()
INGREDIENTS = load_ingredients_data()

if __name__ == "__main__":
    server.run(transport="http", host="127.0.0.1", port=8000)
