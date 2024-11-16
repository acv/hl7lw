from __future__ import annotations
from typing import Union, Optional
import re

from .exceptions import *


class Hl7Component:
    def __init__(self, parser: Hl7Parser, content: Optional[str] = None) -> None:
        self.parser = parser
        self.components = []
        self.parse(content)
    
    def parse(self, content: Optional[str]) -> None:
        if content is None:
            self.components = [Hl7Subcomponent(self.parser, content)]
        else:
            self.components = [Hl7Subcomponent(self.parser, k) for k in 
                               content.split(self.parser.component_separator)]
    
    def __getitem__(self, key: int) -> Hl7Subcomponent:
        if key < 1:
            raise InvalidHl7FieldReference(f"Component index must be 1 indexed and positive not [{key}]")
        if key > len(self.components):
            return Hl7Subcomponent(self.parser, None)  # Create an implicit empty arborescence
        key -= 1
        return self.components[key]

    def __setitem__(self, key: int, value: str) -> None:
        if key < 1:
            raise InvalidHl7FieldReference(f"Component index must be 1 indexed and positive not [{key}]")
        while key > len(self.components):
            self.components.append(Hl7Subcomponent(self.parser, None))
        key -= 1
        self.components[key] = value
        
    def __str__(self) -> str:
        return self.parser.component_separator.join([str(k) for k in self.components])


class Hl7Subcomponent:
    def __init__(self, parser: Hl7Parser, content: Optional[str] = None) -> None:
        self.parser = parser
        self.subcomponents = []
        self.parse(content)
    
    def parse(self, content: Optional[str]) -> None:
        if content is None:
            self.subcomponents = [""]
        else:
            self.subcomponents = [k for k in 
                                  content.split(self.parser.subcomponent_separator)]
    
    def __getitem__(self, key: int) -> str:
        if key < 1:
            raise InvalidHl7FieldReference(f"Subcomponent index must be 1 indexed and positive not [{key}]")
        if key > len(self.subcomponents):
            return ''  # Create an implicit empty arborescence
        key -= 1
        return self.subcomponents[key]

    def __setitem__(self, key: int, value: str) -> None:
        if key < 1:
            raise InvalidHl7FieldReference(f"Subcomponent index must be 1 indexed and positive not [{key}]")
        while key > len(self.subcomponents):
            self.subcomponents.append('')
        key -= 1
        self.subcomponents[key] = value
        
    def __str__(self) -> str:
        return self.parser.subcomponent_separator.join(self.subcomponents)


class Hl7Field:
    def __init__(self, parser: Hl7Parser, content: Optional[str] = None) -> None:
        self.parser = parser
        self.repetitions = []
        self.parse(content)
    
    def parse(self, content: Optional[str]) -> None:
        if content is None:
            self.repetitions = [Hl7Component(self.parser, content)]
        else:
            self.repetitions = [Hl7Component(self.parser, k) for k in 
                                content.split(self.parser.repetition_separator)]
    
    def __getitem__(self, key: int) -> Hl7Component:
        if key < 1:
            raise InvalidHl7FieldReference(f"Repetition index must be 1 indexed and positive not [{key}]")
        if key > len(self.repetitions):
            return Hl7Component(self.parser, None)  # Create an implicit empty arborescence
        key -= 1
        return self.repetitions[key]
    
    def __setitem__(self, key: int, value: str) -> None:
        if key < 1:
            raise InvalidHl7FieldReference(f"Repetition index must be 1 indexed and positive not [{key}]")
        while key > len(self.repetitions):
            self.repetitions.append(Hl7Component(self.parser, None))
        key -= 1
        self.repetitions[key] = value

    @classmethod
    def set_by_reference(klass,
                         source: Union[Hl7Message, Hl7Segment],
                         reference: Union[str, Hl7Reference],
                         value: str) -> None:
        if isinstance(reference, str):
            reference = Hl7Reference(reference)
        if isinstance(source, Hl7Message):
            segment = source.get_segment(reference.segment_name, strict=True)
        else:
            segment = source
        if segment is None:
            raise SegmentNotFound(f"Could not find segment [{reference.segment_name}]")
        field = klass(segment.parser, segment[reference.field])
        if reference.repetition is None:
            if reference.component is None:
                # Special case. If assignment to say PID-4 directly is made, ignore repetitions. 
                segment[reference.field] = value
                return
            rep = 1
        else:
            rep = reference.repetition
        while rep > len(field.repetitions):
            field.repetitions.append(Hl7Component(field.parser, None))
        if reference.component is None:
            # trivial
            field[rep] = Hl7Component(field.parser, None)  # Instentiate the arborescence
            field[rep][1][1] = value  # Attach to leaf node
        else:
            while reference.component > len(field[rep].components):
                field[rep].components.append(Hl7Subcomponent(field.parser, None))
            if reference.subcomponent is None:
                field[rep][reference.component] = Hl7Subcomponent(field.parser, None)
                field[rep][reference.component][1] = value
            else:
                field[rep][reference.component][reference.subcomponent] = value
        segment[reference.field] = str(field)

    @classmethod
    def get_by_reference(klass,
                         source: Union[Hl7Message, Hl7Segment], 
                         reference: Union[str, Hl7Reference]) -> str:
        if isinstance(reference, str):
            reference = Hl7Reference(reference)
        if isinstance(source, Hl7Message):
            segment = source.get_segment(reference.segment_name, strict=True)
        else:
            segment = source
        if segment is None:
            raise SegmentNotFound(f"Could not find segment [{reference.segment_name}]")
        field = klass(segment.parser, segment[reference.field])
        if reference.repetition is None:
            # It's natural to ignore repetitions in the normal case
            # Might not be strictly correct, but it feels natural.
            if reference.component is None:
                return str(field)
            else:
                # First repetition
                component = field[1][reference.component]
                if reference.subcomponent is None:
                    return str(component)
                else:
                    return str(component[reference.subcomponent])
        else:
            # explicit repetition land.
            rep = field[reference.repetition]
            if reference.component is None:
                return str(rep)
            else:
                if reference.subcomponent is None:
                    return str(rep[reference.component])
                else:
                    return str(rep[reference.component][reference.subcomponent])
    
    def __str__(self) -> str:
        return self.parser.repetition_separator.join([str(k) for k in self.repetitions])


SEGMENT_ID_RE = re.compile(r'^[A-Z][A-Z0-9]{2}$')


class Hl7Reference:
    def __init__(self, definition: Optional[str] = None) -> None:
        self.segment_name: Optional[str] = None
        self.field: Optional[int] = None
        self.repetition: Optional[int] = None
        self.component: Optional[int] = None
        self.subcomponent: Optional[int] = None
        if definition is not None:
            self.parse_definition(definition)
    
    def parse_definition(self, definition: str) -> None:
        try:
            segment_name, rest_of_def = definition.split('-', maxsplit=1)
        except ValueError:
            raise InvalidHl7FieldReference("Need at least a segment id and a field index like MSH-9")
        if not SEGMENT_ID_RE.match(segment_name):
            raise InvalidHl7FieldReference(f"Invalis segment id [{segment_name}]")
        field_part, *leftover = rest_of_def.split('.')
        if len(leftover) > 2:
            raise InvalidHl7FieldReference("Too many dotted components to the field reference")
        if '[' in field_part:
            field_str, rep_part = field_part.split('[', maxsplit=1)
            rep_str = rep_part.split(']', maxsplit=1)[0]
            try:
                rep = int(rep_str)
            except ValueError:
                raise InvalidHl7FieldReference(f"Invalid field index [{rep_str}]")
            if rep < 1:
                raise InvalidHl7FieldReference(f"Invalid field index [{rep}]")
        else:
            rep = None
            field_str = field_part
        try:
            field = int(field_str)
        except ValueError:
            raise InvalidHl7FieldReference(f"Invalid field index [{field_str}]")
        if field < 1:
            raise InvalidHl7FieldReference(f"Invalid field index [{field}]")
        if len(leftover) > 0:
            try:
                component = int(leftover[0])
            except ValueError:
                raise InvalidHl7FieldReference(f"Invalid component index [{leftover[0]}]")
            if component < 1:
                raise InvalidHl7FieldReference(f"Invalid component index [{component}]")
        else:
            component = None
        if len(leftover) > 1:
            try:
                subcomponent = int(leftover[1])
            except ValueError:
                raise InvalidHl7FieldReference(f"Invalid subcomponent index [{leftover[1]}]")
            if subcomponent < 1:
                raise InvalidHl7FieldReference(f"Invalid component index [{subcomponent}]")
        else:
            subcomponent = None
        self.segment_name = segment_name
        self.field = field
        self.repetition = rep
        self.component = component
        self.subcomponent = subcomponent

    
class Hl7Segment:
    def __init__(self, parser: Optional[Hl7Parser] = None) -> None:
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
        if key < 1:
            raise InvalidSegmentIndex("Segments do not have a 0 or negative index.")
        elif key > 0:
            if key > len(self.fields):
                return ""
            key -= 1  # 0 index array but 1 index access
        return self.fields[key]
    
    def __setitem__(self, key: int, value: Union[str, Hl7Field]) -> str:
        if key < 1:
            raise InvalidSegmentIndex("Segments do not have a 0 or negative index.")
        elif key > 0:
            key -= 1  # 0 index array but 1 index access
        while len(self.fields) <= key:
            self.fields.append('')
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
    
    def __getitem__(self, key: str) -> str:
        return Hl7Field.get_by_reference(self, key)
    
    def __setitem__(self, key: str, value: str) -> None:
        Hl7Field.set_by_reference(self, key, value)
    
    def __str__(self) -> str:
        return self.parser.format_message(self)


class Hl7Parser:
    """
    Hl7Parser implements the encoding/decoding logic for Hl7 messages.

    The `parse_message()` method will extract the encoding characters from the
    MSH segment using the `sniff_out_grammar_from_msh_definition()` method. This
    can be disabled with the `ignore_msh_values_for_parsing` constructor option.

    There's a few other constructor options to relax the parser and allow some
    common and/or convenient deviations from the spec.

    Sample usage:

    ```
    p = Hl7Parser()
    m = p.parse_message(message=message_bytes, encoding="ascii")
    
    m_b = p.format_message(message=m, encoding="ascii")
    ```

    """
    def __init__(self,
                 newline_as_terminator: bool = False,
                 ignore_invalid_segments: bool = False,
                 allow_unterminated_last_segment: bool = False,
                 ignore_msh_values_for_parsing: bool = False,
                 allow_multiple_msh: bool = False) -> None:
        """
        All arguments are optional and used to alter how strict the parser
        behaviour will be.

        All options, default to disabled.

        Options:

        `newline_as_terminator` -- Newlines (`\n`) and Windows new lines (`\r\n`) will
                                   be treated as segment terminator, just like carriage
                                   returns (`\r`)

        `ignore_invalid_segments` -- Invalid segments will be discarded silently. Validity
                                     is not based on the segment being in the spec, just
                                     syntax rules.
        
        `allow_unterminated_last_segment` -- Support messages where the last segment is not
                                             followed by a segment terminator (`\r`).
        
        `ignore_msh_values_for_parsing` -- Do not use MSH-1 and MSH-2 to identify the encoding
                                           characters.
        
        `allow_multiple_msh` -- Treat any MSH segments after the first one as if they were an
                                ordinary segment instead of raising an exception.
        
        The default control characters are per the spec:

        `segment_separator`:      `\r`
        `field_separator`:        `|`
        `component_separator`:    `^`
        `repetition_separator`:   `~`
        `escape_character`:       `\`
        `subcomponent_separator`: `&`

        """
        # Grammar defaults
        self.segment_separator: str = '\r'
        self.field_separator: str = '|'
        self.component_separator: str = '^'
        self.repetition_separator: str = '~'
        self.escape_character: str = '\\'
        self.subcomponent_separator: str = '&'

        # Parsing options
        self.newline_as_terminator = newline_as_terminator
        self.ignore_invalid_segments = ignore_invalid_segments
        self.allow_unterminated_last_segment = allow_unterminated_last_segment
        self.ignore_msh_values_for_parsing = ignore_msh_values_for_parsing
        self.allow_multiple_msh = allow_multiple_msh
    
    def parse_message(self,
                      message: Union[bytes, str],
                      encoding: Optional[str] = 'ascii') -> Hl7Message:
        """
        Parse a `message` which can either be a `str` or a `bytes`. If the
        `message` is a `bytes` then then `encoding` option will be used to
        `decode` it into a `str` first. The default value of `encoding` is
        "ascii". The possibly encodings are all the encodings supported by
        the python interpreter.

        Any parsing error will cause the method to raise an Exception, all
        of which will be a subclass of `Hl7Exception`. The constructor
        options can be used to lower the strictness of the parser if
        necessary.

        Note specifically that by default MSH-1 and MSH-2 will be used to
        set the parser control character and in the case of invalid MSH-2
        specifically, you may get very strange results. This behaviour can
        be disabled with the `ignore_msh_values_for_parsing` constructor
        option.
        """
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
                    seg_obj = self.parse_segment(segment, encoding=encoding)
                else:
                    seg_obj = self.parse_segment(segment, allow_msh=False, encoding=encoding)
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
        """
        Parse a single `segment` into an `Hl7Segment` objector. MSH segments
        will only be parsed if the `allow_msh` option is `True`, which is the
        default. If `segment` is a `bytes` instead of a `str`, it will be
        decoded into a str using the value provided for `encoding`. If no
        encoding is supplied, "ascii" will be used.

        This method is primarily used by the `parse_message()` method but it
        can also be used to create an `Hl7Segment` object from a string
        representation.
        """
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
        
        if not SEGMENT_ID_RE.match(name):
            raise InvalidSegment(f"Invalid segment name [{name}]")
        if name == 'MSH':
            fields.insert(0, self.field_separator)  # Quirk of the spec, MSH-1 is special
        hl7_seg = Hl7Segment(parser=self)
        hl7_seg.name = name
        hl7_seg.fields = fields
        return hl7_seg
    
    def sniff_out_grammar_from_msh_definition(self, segment: str) -> None:
        """
        This method extracts the control character definition from an MSH segment
        and updates this parser instance with them.

        If the segment is not an MSH segment or is too short, the method will
        raise an `InvalidSegment` exception.

        There is normally no need for application code to use this method.
        """
        if not segment.startswith('MSH'):
            raise InvalidSegment("An MSH segment is required, not {segment[:3]}")
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
        """
        Returns the encoded `str` representation of the supplied `Hl7Segment`.
        """
        fields = segment.fields[:]  # shallow copy
        if segment.name == 'MSH':
            del fields[0]
        fields.insert(0, segment.name)
        return self.field_separator.join(fields)
    
    def format_message(self,
                       message: Hl7Message, 
                       encoding: Optional[str] = None) -> Union[str, bytes]:
        """
        Returns the encoded representation of the supplied `Hl7Message` object.

        If the `encoding` parameter is supplied, the result will be a `bytes`
        representation and the `encoding` will be used. If the `encoding` is
        not specified, a `str` representation will be returned and the caller
        is responsible to encode to `bytes` if necessary.
        """
        formatted_segments = []
        for segment in message.segments:
            formatted_segments.append(self.format_segment(segment))
        formatted_segments.append('')  # will force termination of last segment
        formatted_message = self.segment_separator.join(formatted_segments)
        if encoding is not None:
            return formatted_message.encode(encoding=encoding)
        else:
            return formatted_message

