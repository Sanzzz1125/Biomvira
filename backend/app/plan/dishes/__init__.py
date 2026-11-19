"""Standard home recipes, one serving each, written in grams of raw edible ingredients.

How the amounts are written:
- Ingredients are weighed raw, cleaned and peeled (rice before cooking, onion without its skin). Water is not listed.
- serving_g is the cooked weight of one serving in the household measure given (1 katori, 1 roti, 1 plate).
- Oil for deep-fried items is the amount the food absorbs, not what is in the pan.
- A line can carry its own cooking method; tempering (popu, tadka) is always fried, and what is added after cooking
  (lemon juice, curd, garnish) is "none".
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    role: str
    meals: tuple
    regions: tuple
    serving: str
    serving_g: int
    method: str
    ingredients: tuple  # ((name, grams) or (name, grams, method), ...)
    also_called: tuple = ()
    max_per_week: int = 7
    note: str = ""


def dish(id, name, role, meals, regions, serving, serving_g, method, ingredients, *, also_called=(), max_per_week=7,
         note=""):
    """Meals and regions are written as space-separated words: "lunch dinner", "telangana andhra"."""
    return Dish(id=id, name=name, role=role, meals=tuple(meals.split()), regions=tuple(regions.split()),
                serving=serving, serving_g=serving_g, method=method, ingredients=tuple(ingredients),
                also_called=tuple(also_called), max_per_week=max_per_week, note=note)


def tempering(oil, *, mustard=0.5, cumin=0.3, urad=1, chana=1, red_chilli=0.5, curry_leaves=1, garlic=0, hing=0.05,
              fenugreek=0, oil_name="oil"):
    """The usual South Indian tempering (popu, tiragamata) for one serving; every part is fried."""
    parts = [(oil_name, oil), ("mustard seeds", mustard), ("cumin seeds", cumin), ("urad dal", urad),
             ("chana dal", chana), ("dry red chilli", red_chilli), ("curry leaves", curry_leaves), ("garlic", garlic),
             ("asafoetida", hing), ("fenugreek seeds", fenugreek)]
    return [(name, grams, "frying") for name, grams in parts if grams > 0]
