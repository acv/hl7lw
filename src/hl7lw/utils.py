from enum import Enum
from typing import Optional
import datetime
import random
from .parser import Hl7Message, Hl7Segment, Hl7Parser, Hl7Field


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


class PatientID:
    def __init__(self, patient_id: str, issuer: Optional[str] = None) -> None:
        self.patient_id = patient_id
        self.issuer = issuer
    
    def __str__(self) -> str:
        f = Hl7Field(Hl7Parser())
        f[1][1] = self.patient_id
        if self.issuer is not None:
            f[1][4] = self.issuer
        return str(f)


class Patient:
    def __init__(self, patient_ids: list[PatientID], name: str, birthdate: str, sex: str) -> None:
        self.patient_ids = patient_ids
        self.name = name
        self.birthdate = birthdate
        self.sex = sex
    
    def as_segment(self, parser: Optional[Hl7Parser] = None) -> Hl7Segment:
        if parser is None:
            parser = Hl7Parser()
        pid = Hl7Segment(parser=parser)
        pid.parse('PID|')
        pid3 = Hl7Field(parser)
        for index, patient_id in enumerate(self.patient_ids, start=1):
            pid3[index] = str(patient_id)
        pid[3] = str(pid3)
        pid[5] = self.name
        pid[7] = self.birthdate
        pid[8] = self.sex
        return pid


class VisitIndicator(Enum):
    AccountLevel = "A"
    VisitLevel = "V"


class PatientClass(Enum):
    Emergency = "E"
    Inpatient = "I"
    Outpatient = "O"
    Preadmit = "P"
    RecurringPatient = "R"
    Obstetrics = "O"
    CommercialAccount = "C"
    NotApplicable = "N"
    Unknown = "U"


class Visit:
    def __init__(self,
                 patient_class: PatientClass = PatientClass.Outpatient,
                 patient_location: str = "",
                 referring_physician: str = "",
                 visit_number: str = "",
                 visit_indicator: VisitIndicator = VisitIndicator.AccountLevel
                 ) -> None:
        self.patient_class = patient_class
        self.patient_location = patient_location
        self.referring_physician = referring_physician
        self.visit_number = visit_number
        self.visit_indicator = visit_indicator
    
    def as_segment(self, parser: Optional[Hl7Parser] = None) -> Hl7Segment:
        if parser is None:
            parser = Hl7Parser()
        pv1 = Hl7Segment(parser=parser)
        pv1.parse('PV1|')
        pv1[2] = self.patient_class.value
        pv1[3] = self.patient_location
        pv1[8] = self.referring_physician
        pv1[19] = self.visit_number
        pv1[51] = self.visit_indicator.value
        return pv1


class OrderControl(Enum):
    """
    From HL7 Table 0119

    For brevity, I kept Order whenevent the table has Order/Service Request
    """
    NewOrder = "NW"
    OrderOK = "OK"
    UnableToAccept = "UA"
    PreviousResult = "PR"
    CancelOrder = "CA"
    OrderCancelled = "OC"
    CancelledAsRequested = "CR"
    UnableToCancel = "UC"
    DiscontinueOrder = "DC"
    OrderDiscontinued = "OD"
    DiscontinuedAsRequested = "DR"
    UnableToDiscontinue = "UD"
    Hold = "HD"
    OrderHeld = "OH"
    UnableToPutOnHold = "UH"
    OnHoldAsRequested = "HR"
    ReleasePreviousHold = "RL"
    OrderReleased = "OE"
    ReleasedAsRequested = "OR"
    UnableToRelease = "UR"
    OrderReplaceRequest = "RP"
    ReplaceUnsolicited = "RU"
    ReplacementOrder = "RO"
    ReplacedAsRequested = "RQ"
    UnableToReplace = "UM"
    ParentOrder = "PA"
    ChildOrder = "CH"
    ChangeOrder = "XO"
    OrderChangedUnsolicited = "XX"
    UnableToChange = "UX"
    ChangedAsRequested = "XR"
    DataErrors = "DE"
    ObservationToFollow = "RE"
    RequestReceived = "RR"
    ResponseToSendStatusRequest = "SR"
    SendStatusRequest = "SS"
    StatusChanged = "SC"
    SendOrderNumber = "SN"
    NumberAssigned = "NA"
    CombinedResult = "CN"
    RefillOrder = "RF"
    OrderRefillRequestApproval = "AF"
    OrderRefillRequestDenied = "DF"
    OrderRefilledUnsolicited = "FU"
    OrderRefilledAsRequested = "OF"
    UnableToRefill = "UF"
    LinkOrderToPatientCareGoal = "LI"
    UnlinkOrderFromPatientCareGoal = "UN"


class ResultStatus(Enum):
    """
    HL7 Table 0123
    """
    OrderReceived = "O"
    ProcedureIncomplete = "I"
    ProcedureScheduled = "S"
    SomeResultsAvailable = "A"
    Preliminary = "P"
    CorrectionToResults = "C"
    ResultsStoredNotYetVerified = "R"
    Final = "F"
    OrderCancelled = "X"


class QuantityTiming:
    def __init__(self, start_time: str = "", end_time: str = "", priority: str = "") -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        
    def __str__(self) -> str:
        f = Hl7Field(Hl7Parser())
        f[1][4] = self.start_time
        f[1][5] = self.end_time
        f[1][6] = self.priority
        return str(f)


class Procedure:
    def __init__(self,
                 requested_procedure_id: str = "",
                 order_status: str = "",  # HL7 Table 0038 is ignored too often to codify
                 procedure_code: str = "",
                 procedure_description: str = "", 
                 quantity_timing: Optional[QuantityTiming] = None,
                 ordering_provider: str = "",
                 modality_or_service: str = "",
                 result_status: Optional[ResultStatus] = None
                 ) -> None:
        self.requested_procedure_id = requested_procedure_id
        self.order_status = order_status
        self.procedure_code = procedure_code
        self.procedure_description = procedure_description
        self.quantity_timing = quantity_timing
        self.ordering_provider = ordering_provider
        self.modality_or_service = modality_or_service
        self.result_status = result_status
    
    def as_universal_service_id(self):
        f = Hl7Field(Hl7Parser())
        f[1][1] = self.procedure_code
        f[1][2] = self.procedure_description
        return str(f)


class OrderGroup:
    def __init__(self,
                 order_control: OrderControl = OrderControl.NewOrder,
                 placer_order_number: str = "",
                 filler_order_number: str = "",
                 accession_number: str = "",
                 entering_organization: str = "",
                 reason_for_exam: str = "",
                 ) -> None:
        self.procedures: list[Procedure] = []
        self.order_control = order_control
        self.placer_order_number = placer_order_number
        self.filler_order_number = filler_order_number
        self.accession_number = accession_number
        self.entering_organization = entering_organization
        self.reason_for_exam = reason_for_exam

    def add_procedure(self, procedure: Procedure) -> "OrderGroup":
        self.procedures.append(procedure)
        return self

    def add_to_message(self, message: Hl7Message) -> None:
        base_orc = message.parser.parse_segment('ORC|')
        base_obr = message.parser.parse_segment('OBR|')
        
        base_orc[1] = self.order_control.value
        base_orc[2] = self.placer_order_number
        base_orc[3] = self.filler_order_number
        base_orc[17] = self.entering_organization

        base_obr[1] = "1"
        base_obr[2] = self.placer_order_number
        base_obr[3] = self.filler_order_number
        base_obr[18] = self.accession_number
        reason = Hl7Field(parser=message.parser)
        reason[1][2] = self.reason_for_exam
        base_obr[31] = str(reason)

        if len(self.procedures) == 0:
            message.segments.append(base_orc)
            message.segments.append(base_obr)
        else:
            segments_to_add = []
            p = message.parser
            for index, procedure in enumerate(self.procedures, start=1):
                # Reparse to make deep copies.
                orc = p.parse_segment(p.format_segment(base_orc))
                obr = p.parse_segment(p.format_segment(base_obr))

                if procedure.quantity_timing is not None:
                    orc[7] = str(procedure.quantity_timing)
                    obr[27] = orc[7]
                    obr[5] = procedure.quantity_timing.priority
                    obr[6] = procedure.quantity_timing.start_time
                    obr[7] = procedure.quantity_timing.start_time
                    obr[8] = procedure.quantity_timing.end_time
                    orc[15] = procedure.quantity_timing.start_time
                    obr[36] = procedure.quantity_timing.start_time
                if procedure.result_status is not None:
                    obr[25] = procedure.result_status.value
                obr[4] = procedure.as_universal_service_id()
                orc[5] = procedure.order_status
                orc[12] = procedure.ordering_provider
                obr[16] = procedure.ordering_provider
                obr[19] = procedure.requested_procedure_id
                obr[24] = procedure.modality_or_service
                obr[44] = procedure.procedure_code

                segments_to_add.append(orc)
                segments_to_add.append(obr)

            message.segments += segments_to_add


BASE_MSH = b'MSH|^~\\&|||||||||T|2.3.1||||||||||\r'


class ProcessingMode(Enum):
    Debugging = 'D'
    Production = 'P'
    Training = 'T'


class OrmBuilder:
    def __init__(self,
                 sending_application: str = "hl7lw",
                 sending_facility: str = "",
                 receiving_application: str = "",
                 receiving_facility: str = "",
                 hl7_version: str = "2.3.1",
                 processing_mode: ProcessingMode = ProcessingMode.Production 
                 ) -> None:
        self.sending_application = sending_application
        self.sending_facility = sending_facility
        self.receiving_application = receiving_application
        self.receiving_facility = receiving_facility
        self.hl7_version = hl7_version
        self.processing_mode = processing_mode

        self.patient: Optional[Patient] = None
        self.visit: Optional[Visit] = None
        self.order_group: Optional[OrderGroup] = None
    
    def set_patient(self, patient: Patient) -> "OrmBuilder":
        self.patient = patient
        return self
        
    def set_visit(self, visit: Visit) -> "OrmBuilder":
        self.visit = visit
        return self

    def add_order_group(self, order_group: OrderGroup) -> "OrmBuilder":
        self.order_group = order_group
        return self
    
    def build(self, parser: Optional[Hl7Parser] = None) -> Hl7Message:
        if parser is None:
            parser = Hl7Parser()
        m = parser.parse_message(BASE_MSH)
        msh = m.get_segment('MSH')
        msh[3] = self.sending_application
        msh[4] = self.sending_facility
        msh[5] = self.receiving_application
        msh[6] = self.sending_facility
        msh[7] = generate_message_time()
        msh[9] = 'ORM^O01'
        msh[10] = generate_message_id()
        msh[11] = self.processing_mode.value
        msh[12] = self.hl7_version

        if self.patient is None:
            m.segments.append(parser.parse_segment("PID|"))
        else:
            m.segments.append(self.patient.as_segment(parser=parser))

        if self.visit is not None:
            m.segments.append(self.visit.as_segment(parser=parser))

        if self.order_group is None:
            m.segments.append(parser.parse_segment("ORC|"))
            m.segments.append(parser.parse_segment("OBR|"))
        else:
            self.order_group.add_to_message(message=m)
        
        return m
