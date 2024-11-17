from freezegun import freeze_time
import datetime
from src.hl7lw import Hl7Message, Hl7Parser, utils


CONSTANT_TIME = datetime.datetime(year=2024, month=7, day=12, hour=15, minute=6, second=3)


@freeze_time(CONSTANT_TIME)
def test_ack(mocker, trivial_a08: bytes, expected_ack: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(trivial_a08)
    # Ensure that the ACK is always identical.
    mocker.patch("random.randint", return_value=999999)
    a = p.format_message(utils.generate_ack(m, utils.Acks.AA), encoding="ascii")
    assert a == expected_ack


@freeze_time(CONSTANT_TIME)
def test_ack_with_details(mocker, trivial_a08: bytes, expected_ack: bytes) -> None:
    p = Hl7Parser()
    m = p.parse_message(trivial_a08)
    # Ensure that the ACK is always identical.
    mocker.patch("random.randint", return_value=999999)
    a = p.format_message(utils.generate_ack(m, utils.Acks.AA, details="bad"))
    expected = p.parse_message(expected_ack)
    expected["MSA-3"] = "bad"
    assert a == str(expected)
