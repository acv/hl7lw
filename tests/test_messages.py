import pytest
from src.hl7lw import Hl7Message, Hl7Parser, Hl7Segment, InvalidSegmentIndex, SegmentNotFound


def test_a08_parsing(trivial_a08: bytes):
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)
    assert isinstance(m, Hl7Message)
    assert len(m.segments) == 3


def test_segments(trivial_a08: bytes):
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)
    pid = m.get_segment('PID')

    assert isinstance(pid, Hl7Segment)
    assert pid.name == 'PID'
    assert len(pid.fields) == 32, "Sample message should have 32 fields."

    assert pid[7] == '20181128100700'
    with pytest.raises(InvalidSegmentIndex):
        pid[0]
    pid[1] = 'Nebucadnezar'
    assert pid.fields[0] == 'Nebucadnezar', "Assignment test, direct access"
    assert pid[1] == 'Nebucadnezar', "Assignment test"

    msh = m.get_segment('MSH')
    assert msh[1] == '|', "Special handling of MSH-1"


def test_get_by_reference(trivial_a08: bytes):
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)

    assert m["PID-3[2].4"] == 'EPI'
    assert m["PID-3[2].5.1"] == 'MR'
    assert m["PID-3[2].5"] == 'MR&1.2.3.4'
    with pytest.raises(SegmentNotFound):
        m["OBX-5"]
    assert m["PID-3"] == 'E3843677^^^EPIC^MRN~900070078^^^EPI^MR&1.2.3.4'
    assert m["PID-100"] == ''
        
