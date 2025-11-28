from pydantic import BaseModel
from typing import List, Tuple

class NodoResponse(BaseModel):
    id: int
    latitud: float
    longitud: float
    
class AristaResponse(BaseModel):
    origen: int
    destino: int
    peso: float

