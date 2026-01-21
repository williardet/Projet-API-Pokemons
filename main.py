from dataclasses import dataclass, asdict
from typing import Union
from fastapi import FastAPI, Path, HTTPException
import json
import os
import uvicorn

# 1) Chargement du fichier JSON contenant les pokémons
with open("pokemon.json", "r") as f:
    pokemon_list = json.load(f)

list_pokemons = {k + 1: v for k, v in enumerate(pokemon_list)}

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

# 3) Création de l'application FastAPI
app = FastAPI()

# 4) Route : nombre total de pokémons
@app.get("/total_pokemons")
def get_total_pokemons() -> dict:
    return {"total": len(list_pokemons)}

# 5) Route : récupérer tous les pokémons
@app.get("/pokemons")
def get_all_pokemons() -> list[Pokemon]:
    res = []
    for id in list_pokemons:
        res.append(Pokemon(**list_pokemons[id])) # ** refait la structure du dictionnaire
    return res

# 6) Route : récupérer un pokémon par son ID
@app.get("/pokemon/{id}")
def get_pokemon_by_id(
    id: int = Path(..., ge=1)  # "..." => obligatoire, ge=1 => id ≥ 1
) -> Pokemon:
 
    if id not in list_pokemons:
        raise HTTPException(status_code=404, detail="Ce pokemon n'existe pas")
    return Pokemon(**list_pokemons[id])

# 7) Route : créer un nouveau pokémon
@app.post("/pokemon/")
def create_pokemon(pokemon: Pokemon) -> Pokemon:

    if pokemon.id in list_pokemons:
        raise HTTPException(status_code=400, detail=f"Le pokemon {pokemon.id} existe déjà")

    # asdict(pokemon) convertit l'objet dataclass → dictionnaire
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
            if type not in types :
                types.append(type)

    types.sort()
    return types

# 11) Route : afficher les types de pokémon
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

    #on filtre les types:
    if types is not None:
        for pokemon in pokemon_list:
            if set(types.split(",")).issubset(pokemon["types"]): # vérifie si les types appartiennent au pokémon
                filtered_list.append(pokemon)

    #on filtre les evo:
    if evo is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = []

        for pokemon in tmp:
            if evo == "true" and "evolution_id" in pokemon:
                new.append(pokemon)

            if evo == "false" and "evolution_id" not in pokemon:
                new.append(pokemon)

        filtered_list = new

    #on filtre sur greater than total
    if totalgt is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = []

        for pokemon in tmp:
            if pokemon["total"] > totalgt:
                new.append(pokemon)
        
        filtered_list = new

    #on filtre sur less than total
    if totallt is not None:
        tmp = filtered_list if filtered_list else pokemon_list
        new = []

        for pokemon in tmp:
            if pokemon["total"] < totalgt:
                new.append(pokemon)
            
        filtered_list = new

    #on gère le tri
    if sortby is not None and sortby in ["id","name","total"]:
        filtered_list = filtered_list if filtered_list else pokemon_list
        sorting_order = False
        # vérifie si la nature de l'élément entré en paramètre est asc ou dsc
        if order == "asc" : sorting_order = False
        if order == "desc" : sorting_order = True

        filtered_list = sorted(filtered_list, key=lambda d: d[sortby], reverse = sorting_order)

    #Réponse
    if filtered_list :
        for pokemon in filtered_list:
            res.append(Pokemon(**pokemon))
        return res
    
    raise HTTPException(status_code=404, detail="Aucun Pokemon ne répond aux critères de recherche")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

@app.get("/")
def read_root():
    return {"message": "API Pokémon opérationnelle"}
