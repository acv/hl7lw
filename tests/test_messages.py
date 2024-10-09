import pytest
from hl7lw import Hl7Message, Hl7Parser


def test_a08_parsing(trivial_a08):
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)
    assert isinstance(m, Hl7Message)
    assert len(m.segments) == 3
