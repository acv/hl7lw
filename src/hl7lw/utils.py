from enum import Enum
from typing import Optional
import datetime
import random
from .parser import Hl7Message, Hl7Segment


class Acks(Enum):
    """
    Enum for the acknowledgement codes from HL7 table 0008.
    """
    AA = 1
    AR = 2
    AE = 3
    CA = 4
    CE = 5
    CR = 6


def generate_message_time():
    """
    Generate a current timestamp suitable for MSH-7.
    """
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def generate_message_id():
    """
    Generate a message control ID suitable for MSH-10.

    This function is not suitable for very high volume message generation as
    it generates only 1 million possible ID for a given second and with the
    birthday paradox, you would expect a collision after 1178 messages, 50%
    of the time.
    """
    return f"{generate_message_time()}{random.randint(0, 999999):06d}"


def generate_ack(message: Hl7Message, status: Acks, details: Optional[str] = None) -> Hl7Message:
    """
    Generate an acknowledgement for `message` with the acknowledgement code `status`.
    An optional `reason` can be supplied and if so it will be put into MSA-3.

    This is a convenience function for implementing simple Hl7 sinks.
    """
    ack = Hl7Message(parser=message.parser)
    orig_msh = message.get_segment('MSH', strict=False)
    
    msh = Hl7Segment(parser=message.parser)
    msh.parse(str(orig_msh))
    msh[3] = orig_msh[5]
    msh[4] = orig_msh[6]
    msh[5] = orig_msh[3]
    msh[6] = orig_msh[4]
    msh[7] = generate_message_time()
    msh[9] = 'ACK'
    msh[10] = generate_message_id()
    
    msa = Hl7Segment(parser=message.parser)
    msa.parse("MSA|||")
    msa[1] = status.name
    msa[2] = orig_msh[10]
    if details is not None:
        msa[3] = details
    
    ack.segments = [msh, msa]
    return ack
