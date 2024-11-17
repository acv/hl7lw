from freezegun import freeze_time
import datetime
from src.hl7lw import Hl7Message, Hl7Segment, Hl7Parser, utils


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


def test_patient_id():
    p_w_issuer = utils.PatientID(patient_id="123456", issuer="EPIC")
    p_w_o_issuer = utils.PatientID(patient_id="7890283")

    assert str(p_w_issuer) == "123456^^^EPIC"
    assert str(p_w_o_issuer) == "7890283"


def test_patient():
    patient = utils.Patient(
        patient_ids=[
            utils.PatientID(patient_id="1234", issuer="EPIC"),
            utils.PatientID(patient_id="921380912", issuer="EMPI"),
        ],
        name="Smith^John^Q",
        birthdate="20240823",
        sex="M"
    )
    pid = patient.as_segment()
    assert isinstance(pid, Hl7Segment)
    assert pid.name == 'PID'
    assert str(pid) == "PID|||1234^^^EPIC~921380912^^^EMPI||Smith^John^Q||20240823|M"


@freeze_time(CONSTANT_TIME)
def test_orm_builde_empty(mocker, empty_orm: bytes):
    p = Hl7Parser()
    mocker.patch("random.randint", return_value=999999)
    orm = utils.OrmBuilder(
        sending_application="sa",
        sending_facility="sf",
        receiving_application="ra",
        receiving_facility="rf",
        hl7_version="2.4",
        processing_mode=utils.ProcessingMode.Training
    ).build(parser=p)
    assert p.format_message(orm, encoding="ascii") == empty_orm


@freeze_time(CONSTANT_TIME)
def test_orm_builder_full(mocker, full_orm: bytes):
    p = Hl7Parser()
    mocker.patch("random.randint", return_value=999999)
    orm = utils.OrmBuilder(
        sending_application="sa",
        sending_facility="sf",
        receiving_application="ra",
        receiving_facility="rf",
        hl7_version="2.4",
        processing_mode=utils.ProcessingMode.Training
    ).set_patient(
        patient=utils.Patient(
            patient_ids=[utils.PatientID('1234'), utils.PatientID('456', 'EPIC')],
            name="Smith^John^Q",
            birthdate="18911230",
            sex="M"
        )
    ).set_visit(
        visit=utils.Visit(
            patient_class=utils.PatientClass.Emergency,
            patient_location="EMERG^^^Medical Center",
            referring_physician="1234567^Referring^Doctor",
            visit_number="12345",
            visit_indicator=utils.VisitIndicator.VisitLevel
        )
    ).add_order_group(
        order_group=utils.OrderGroup(
            order_control=utils.OrderControl.ChangeOrder,
            placer_order_number="P1234",
            filler_order_number="F1234",
            accession_number="A1234",
            entering_organization="MCH^Medical Center",
            reason_for_exam="Patient swallowed a whole tuna can"
        ).add_procedure(
            procedure=utils.Procedure(
                requested_procedure_id="RP123401",
                order_status="IP",
                procedure_code="8102",
                procedure_description="Lung",
                quantity_timing=utils.QuantityTiming(start_time="202411171456", end_time="202411171611", priority="R"),
                ordering_provider="12345^Ordering^Provider",
                modality_or_service="CR",
                result_status=None
            )
        ).add_procedure(
            procedure=utils.Procedure(
                requested_procedure_id="RP123402",
                order_status="IP",
                procedure_code="8114",
                procedure_description="Stomach",
                quantity_timing=utils.QuantityTiming(start_time="202411171456", end_time="202411171617", priority="R"),
                ordering_provider="12345^Ordering^Provider",
                modality_or_service="CR",
                result_status=None
            )
        )
    ).build(parser=p)
    assert p.format_message(orm, encoding="ascii") == full_orm