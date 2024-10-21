from __future__ import annotations
from typing import Union, Optional

from .exceptions import *


class Hl7Field:
    pass

    
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


class Hl7Message:
    def __init__(self, parser: Optional[Hl7Parser] = None) -> None:
        self.parser = parser
        if self.parser is None:
            self.parser = Hl7Parser()
        self.segments: list[Hl7Segment] = []

    def parse(self, message: str) -> None:
        tmp_msg = self.parser.parse_message(message)
        self.segments = tmp_msg.segments
    
    def get_segment(self, segment: str,
                       strict: bool = True) -> Optional[Hl7Segment]:
        segments = self.get_segments(segment)
        if len(segments) > 0:
            if strict and len(segments) > 1:
                raise MultipleSegmentsFound(f"Found multiple {segments} segments " + \
                                             "in message and strict mode set.")
            return segments[0]
        else:
            return None
    
    def get_segments(self, segment: str) -> list[Hl7Segment]:
        return [s for s in self.segments if s.name == segment]


class Hl7Parser:
    def __init__(self,
                 newline_as_terminator: bool = False,
                 ignore_invalid_segments: bool = False,
                 allow_unterminated_last_segment: bool = False,
                 ignore_msh_values_for_parsing: bool = False,
                 allow_multiple_msh: bool = False) -> None:
        """

        """
        
        # Grammar defaults
        self.segment_separator = '\r'
        self.field_separator = '|'
        self.component_separator = '^'
        self.repetition_separator = '~'
        self.escape_character = '\\'
        self.subcomponent_separator = '&'

        # Parsing options/
        self.newline_as_terminator = newline_as_terminator
        self.ignore_invalid_segments = ignore_invalid_segments
        self.allow_unterminated_last_segment = allow_unterminated_last_segment
        self.ignore_msh_values_for_parsing = ignore_msh_values_for_parsing
        self.allow_multiple_msh = allow_multiple_msh
    
    def parse_message(self,
                      message: Union[bytes, str],
                      encoding: Optional[str] = 'ascii') -> Hl7Message:
        if isinstance(message, bytes):
            message = message.decode(encoding=encoding)
        hl7_msg = Hl7Message(parser=self)
        if self.newline_as_terminator:
            # We do \r\n collapsing as \r\r would yield illegal empty segments
            message = message.replace('\r\n', '\r').replace('\n', '\r')
        raw_segments = message.split(self.segment_separator)
        if raw_segments[-1] != '':  # Counter-intuitive but last segment should be terminated.
            if not self.allow_unterminated_last_segment:
                raise InvalidHl7Message(f"Last segment unterminated: [{raw_segments[-1]}]")
        else:
            del raw_segments[-1]
        first_seg = True
        for segment in raw_segments:
            try:
                if first_seg or self.allow_multiple_msh:
                    first_seg = False
                    seg_obj = self.parse_segment(segment)
                else:
                    seg_obj = self.parse_segment(segment, allow_msh=False)
                hl7_msg.segments.append(seg_obj)
            except InvalidSegment as e:
                if self.ignore_invalid_segments:
                    pass
                else:
                    raise InvalidHl7Message(str(e))
        return hl7_msg
    
    def parse_segment(self,
                      segment: Union[bytes, str],
                      allow_msh: Optional[bool] = True,
                      encoding: Optional[str] = 'ascii') -> Hl7Segment:
        if isinstance(segment, bytes):
            segment = segment.decode(encoding=encoding)
        if len(segment) < 4:
            raise InvalidSegment(f"Segment is too short to be valid: [{segment}]")
        if segment.startswith('MSH'):
            if not allow_msh:
                raise InvalidSegment("MSH segment found when not expected.")
            if not self.ignore_msh_values_for_parsing:
                self.sniff_out_grammar_from_msh_definition(segment)
        name, *fields = segment.split(self.field_separator)
        if name == 'MSH':
            fields.insert(0, self.field_separator)  # Quirk of the spec, MSH-1 is special
        hl7_seg = Hl7Segment(parser=self)
        hl7_seg.name = name
        hl7_seg.fields = fields
        return hl7_seg
    
    def sniff_out_grammar_from_msh_definition(self, segment: str) -> None:
        field_separator = segment[3]  # Local var in case rest of MSH invalid
        _, control_characters, _ = segment.split(field_separator, maxsplit=2)
        if len(control_characters) != 4:
            raise InvalidSegment(f"Invalid MSH-2, it must be exactly 4 chars [{segment[1]}]")
        self.field_separator = field_separator
        self.component_separator = control_characters[0]
        self.repetition_separator = control_characters[1]
        self.escape_character = control_characters[2]
        self.subcomponent_separator = control_characters[3]
    
    def format_segment(self, segment: Hl7Segment) -> str:
        fields = segment.fields[:]  # shallow copy
        if segment.name == 'MSH':
            del fields[0]
        fields.insert(0, segment.name)
        return self.field_separator.join(fields)
    
    def format_message(self,
                       message: Hl7Message, 
                       encoding: Optional[str]) -> Union[str, bytes]:
        formatted_segments = []
        for segment in message.segments:
            formatted_segments.append(self.format_segment(segment))
        formatted_segments.append('')  # will force termination of last segment
        formatted_message = self.segment_separator.join(formatted_segments)
        if encoding is not None:
            return formatted_message.encode(encoding=encoding)
        else:
            return formatted_message

