class Hl7Exception(Exception):
    pass


class InvalidHl7Message(Hl7Exception):
    pass


class InvalidSegment(Hl7Exception):
    pass


class InvalidSegmentIndex(Hl7Exception):
    pass