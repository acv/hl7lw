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
