import pytest
from src.hl7lw import Hl7Message, Hl7Parser, Hl7Segment
from src.hl7lw.exceptions import *


def test_a08_parsing(trivial_a08: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)
    assert isinstance(m, Hl7Message)
    assert len(m.segments) == 3


def test_segments(trivial_a08: bytes) -> None:
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


def test_by_reference(trivial_a08: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)

    assert m["PID-3[2].4"] == 'EPI'
    assert m["PID-3[2].5.1"] == 'MR'
    assert m["PID-3[2].5"] == 'MR&1.2.3.4'
    with pytest.raises(SegmentNotFound):
        m["OBX-5"]
    assert m["PID-3"] == 'E3843677^^^EPIC^MRN~900070078^^^EPI^MR&1.2.3.4'
    assert m["PID-100"] == ''
    m["PID-4[3].2.8"] = 'beep'
    assert m["PID-4[3].2.8"] == 'beep'
    assert m["PID-4"] == "~~^&&&&&&&beep"
    m["PID-4.1"] = "test"
    m["PID-4[2]"] = "red"
    assert m["PID-4"] == "test~red~^&&&&&&&beep"
    m["PID-4"] = "test2"
    assert m["PID-4"] == "test2"
    m["PID-4[5]"] = "rep"
    assert m["PID-4"] == "test2~~~~rep"
    m["PID-4[3].6"] = "random"
    assert m["PID-4"] == "test2~~^^^^^random~~rep"


def test_complex_by_reference(trivial_a08: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)

    m["PID-4"] = "12345^EPI^MR&1.2.3.4"
    assert m["PID-4"] == "12345^EPI^MR&1.2.3.4"
    assert m["PID-4[1].3.2"] == "1.2.3.4"


def test_bad_references(trivial_a08: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)

    with pytest.raises(InvalidHl7FieldReference):
        m["0ID-1"]
    with pytest.raises(InvalidHl7FieldReference):
        m["0ID-1"] = "test"
    with pytest.raises(InvalidHl7FieldReference):
        m["PIDD-1"]
    with pytest.raises(InvalidHl7FieldReference):
        m["PIDD-1"] = "test"
    with pytest.raises(InvalidHl7FieldReference):
        m["PID"]
    with pytest.raises(InvalidHl7FieldReference):
        m["PID"] = "test"
    with pytest.raises(InvalidSegmentIndex):
        m["PID-0"]
    with pytest.raises(InvalidSegmentIndex):
        m["PID-0"] = "test"
    with pytest.raises(InvalidHl7FieldReference):
        m["PID-1[0]"]
    with pytest.raises(InvalidHl7FieldReference):
        m["PID-1[0]"] = "test"
    with pytest.raises(InvalidHl7FieldReference):
        m["PID-1[-1]"]
    with pytest.raises(InvalidHl7FieldReference):
        m["PID-1[-1]"] = "test"
    with pytest.raises(InvalidSegmentIndex):
        m["PID--1"]
    with pytest.raises(InvalidSegmentIndex):
        m["PID--1"] = "test"


def test_format_message(trivial_a08: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(message=trivial_a08)

    reencoded = p.format_message(m, encoding="ascii")
    assert trivial_a08 == reencoded
    just_assembled = p.format_message(m)
    assert trivial_a08.decode(encoding="ascii") == just_assembled


def test_invalid_segment(trivial_a08: bytes) -> None:
    p = Hl7Parser()

    bad_a08 = trivial_a08 + b"INVALID|\r"
    with pytest.raises(InvalidHl7Message):
        m = p.parse_message(message=bad_a08)
    p2 = Hl7Parser(ignore_invalid_segments=True)
    m = p2.parse_message(message=bad_a08)
    assert p2.format_message(m, encoding="ascii") == trivial_a08
    bad_a08 = trivial_a08 + b"1NV|\r"
    with pytest.raises(InvalidHl7Message):
        m = p.parse_message(message=bad_a08)
    p2 = Hl7Parser(ignore_invalid_segments=True)
    m = p2.parse_message(message=bad_a08)
    assert p2.format_message(m, encoding="ascii") == trivial_a08