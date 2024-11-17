import pytest
import pathlib


SAMPLE_PATH = pathlib.Path(__file__).parent.resolve() / 'samples'


def get_message_from_file(filename):
    p = SAMPLE_PATH / filename
    with p.open('rb') as f:
        return f.read().replace(b'\r\n', b'\r')  # Deal with encoding


@pytest.fixture
def trivial_a08():
    return get_message_from_file('trivial_a08.hl7')


@pytest.fixture
def expected_ack():
    return get_message_from_file('expected_ack.hl7')


@pytest.fixture
def empty_orm():
    return get_message_from_file('empty_orm.hl7')


@pytest.fixture
def full_orm():
    return get_message_from_file('full_orm.hl7')
