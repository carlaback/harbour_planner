from typing import List, Dict
from datetime import date


class Boat:
    def __init__(self, id: int, width: float, arrival: date, departure: date):
        self.id = id
        self.width = width
        self.arrival = arrival
        self.departure = departure


class Slot:
    def __init__(self, id: str, max_width: float):
        self.id = id
        self.max_width = max_width
