from typing import Optional, Union
from parser import Hl7Parser
from exceptions import InvalidSegmentIndex
from field import Hl7Field


class Hl7Segment:
    def __init__(self, parser: Optional[Hl7Parser]) -> None:
        self.parser = parser
        if self.parser is None:
            self.parser = Hl7Parser()
        self.name: Optional[str] = None
        self.fields: list[str] = []  # 0 indexed, usually don't touch.
    
    def parse(self, segment: str) -> None:
        tmp_seg = self.parser.parse_segment(segment)
        self.name = tmp_seg.name
        self.fields = tmp_seg.fields
    
    def __getitem__(self, key: int) -> str:
        if key == 0:
            raise InvalidSegmentIndex("Segments do not have a 0 index.")
        elif key > 0:
            key -= 1  # 0 index array but 1 index access
        return self.fields[key]
    
    def __setitem__(self, key: int, value: Union[str, Hl7Field]) -> str:
        if key == 0:
            raise InvalidSegmentIndex("Segments do not have a 0 index.")
        elif key > 0:
            key -= 1  # 0 index array but 1 index access
        self.fields[key] = str(value)
        return self.fields[key]

    def __str__(self):
        return self.parser.format_segment(self)