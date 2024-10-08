from typing import Optional
from parser import Hl7Parser
from segment import Hl7Segment


class Hl7Message:
    def __init__(self, parser: Optional[Hl7Parser] = None) -> None:
        self.parser = parser
        if self.parser is None:
            self.parser = Hl7Parser()
        self.segments: list[Hl7Segment] = []

    def parse(self, message: str) -> None:
        tmp_msg = self.parser.parse_message(message)
        self.segments = tmp_msg.segments
    