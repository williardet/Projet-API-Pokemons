from dataclasses import dataclass, asdict
from typing import Union
from fastapi import FastAPI, Path, HTTPException
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

# 1) Chargement du fichier JSON contenant les pokémons
try:
    json_path = os.path.join(os.path.dirname(__file__), "pokemon.json")
    with open(json_path, "r") as f:
        pokemon_list = json.load(f)
    list_pokemons = {k + 1: v for k, v in enumerate(pokemon_list)}
except Exception as e:
    pokemon_list = []
    list_pokemons = {}
    @app.get("/")
    def error_root():
        return JSONResponse(status_code=500, content={"error": str(e)})

# 2) Définition de la classe Pokemon (dataclass)
@dataclass
class Pokemon:
    id: int
    name: str
    types: list[str]
    total: int
    hp: int
    attack: int
    defense: int
    attack_special: int
    defense_special: int
    speed: int
    evolution_id: Union[int, None] = None  # optionnel

# 3) Route racine (si tout va bien)
@app.get("/")
def read_root():
    return {"message": "API Pokémon opérationnelle"}

# 4) Route : nombre total de pokémons
@app.get("/total_pokemons")
def get_total_pokemons() -> dict:
    return {"total": len(list_pokemons)}

# 5) Route : récupérer tous les pokémons
@app.get("/pokemons")
def get_all_pokemons() -> list[Pokemon]:
    return [Pokemon(**list_pokemons[id]) for id in list_pokemons]

# 6) Route : récupérer un pokémon par son ID
@app.get("/pokemon/{id}")
def get_pokemon_by_id(id: int = Path(..., ge=1)) -> Pokemon:
    if id not in list_pokemons:
        raise HTTPException(status_code=404, detail="Ce pokemon n'existe pas")
    return Pokemon(**list_pokemons[id])

# 7) Route : créer un nouveau pokémon
@app.post("/pokemon/")
def create_pokemon(pokemon: Pokemon) -> Pokemon:
    if pokemon.id in list_pokemons:
        raise HTTPException(status_code=400, detail=f"Le pokemon {pokemon.id} existe déjà")
    list_pokemons[pokemon.id] = asdict(pokemon)
    return pokemon

# 8) Route : modifier un pokémon
@app.put("/pokemon/{id}")
def update_pokemon(pokemon: Pokemon, id: int = Path(ge=1)) -> Pokemon:
    if id not in list_pokemons:
        raise HTTPException(status_code=404, detail=f"Le pokemon {pokemon.id} n'existe pas")
    list_pokemons[id] = asdict(pokemon)
    return pokemon

# 9) Route : supprimer un pokémon
@app.delete("/pokemon/{id}")
def delete_pokemon(id: int = Path(ge=1)) -> Pokemon:
    if id in list_pokemons:
        pokemon = Pokemon(**list_pokemons[id])
        del list_pokemons[id]
        return pokemon
    raise HTTPException(status_code=404, detail="Ce pokemon n'existe pas")

# 10) Route : afficher les types de pokémon
@app.get("/types")
def get_all_types() -> list[str]:
    types = []
    for pokemon in pokemon_list:
        for type in pokemon["types"]:
            if type not in types:
                types.append(type)
    types.sort()
    return types

# 11) Route : recherche avancée
@app.get("/pokemon/search/")
def search_pokemon(
    types: Union[str, None] = None,
    evo: Union[str, None] = None,
    totalgt: Union[int, None] = None,
    totallt: Union[int, None] = None,
    sortby: Union[str, None] = None,
    order: Union[str, None] = None
) -> Union[list[Pokemon], None]:

    filtered_list = []
    res = []

    if types is not None:
        for pokemon in pokemon_list:
            if set(types.split(",")).issubset(pokemon["types"]):
                filtered_list.append(pokemon)

    if evo is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = []
        for pokemon in tmp:
            if evo == "true" and "evolution_id" in pokemon:
                new.append(pokemon)
            if evo == "false" and "evolution_id" not in pokemon:
                new.append(pokemon)
        filtered_list = new

    if totalgt is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = [p for p in tmp if p["total"] > totalgt]
        filtered_list = new

    if totallt is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = [p for p in tmp if p["total"] < totallt]
        filtered_list = new

    if sortby is not None and sortby in ["id", "name", "total"]:
        filtered_list = filtered_list if filtered_list else pokemon_list
        sorting_order = order == "desc"
        filtered_list = sorted(filtered_list, key=lambda d: d[sortby], reverse=sorting_order)

    if filtered_list:
        return [Pokemon(**p) for p in filtered_list]

    raise HTTPException(status_code=404, detail="Aucun Pokemon ne répond aux critères de recherche")
