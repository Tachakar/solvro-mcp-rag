from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document, Settings, VectorStoreIndex
from pathlib import Path
import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_PATH = PROJECT_ROOT_DIR / "data"

EMBED_MODEL = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
LLM = Ollama(
    model="llama3.2:3b",
    context_window=5000,
    temperature=0.2,
)

Settings.llm = LLM
Settings.embed_model = EMBED_MODEL


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


def load_ingredients_data() -> list[Ingredient]:
    ingredients: list[Ingredient] = []
    for cocktail in COCKTAILS:
        for ingredient in cocktail.ingredients:
            # Ignore measure to avoid dupplicates in INGREDIENTS list
            copy = ingredient.model_copy(update={"measure": None})
            if copy not in ingredients:
                ingredients.append(copy)

    return ingredients


COCKTAILS = load_cocktails_data()
INGREDIENTS = load_ingredients_data()


def cocktail_to_document(c: Cocktail) -> Document:
    text = [
        f"Name: {c.name}\n",
        f"Category: {c.category or 'Unknown'}\n",
        f"Glass: {c.glass or 'Unknown'}\n",
        f"Alcoholic: {c.alcoholic}\n",
        f"Tags: {', '.join(c.tags) if c.tags else 'None'}\n",
        "Ingredients:\n",
    ]
    for ingredient in c.ingredients:
        text.append(
            f"- {ingredient.name}"
            f"{f' - {ingredient.measure}' if ingredient.measure else ''}"
            f"{' - alcoholic' if ingredient.alcohol else ''}\n"
        )
    if c.instructions:
        text.append(f"Instructions: {c.instructions}")
    return Document(text="".join(text), metadata={"cocktail_id": c.id})


def build_indexes(cocktails: list[Cocktail]) -> VectorStoreIndex:
    documents = [cocktail_to_document(c) for c in cocktails]
    nodes = SimpleNodeParser.from_defaults().get_nodes_from_documents(documents)
    return VectorStoreIndex(nodes)

def get_cocktails_query_engine():
    index = build_indexes(COCKTAILS)
    retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
    return RetrieverQueryEngine(retriever=retriever)
