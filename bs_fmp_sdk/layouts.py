class Layouts:
    """Centralized layout names used by the SDK."""

    PROJECTS = "ImportProjects"
    PROJECTS_RAW = "projects_table"
    CONTRACTS = "ImportContracts"
    RFIS = "ImportRFILog"
    RFIS_RAW = "rfilog_table"
    SUBMITTALS = "ImportSubmittal"
    SUBMITTAL_ITEMS = "ImportSubmittalItems"
    SUBMITTAL_REVIEW = "ImportSubmittalReview"
    PEOPLE = "ImportPeople"
    PEOPLE_RAW = "people_table"
    CAANS = "caan_table"


class ProjectFields:
    ID_PRIMARY = "ID_Primary"
    PROJECT_NUMBER = "ProjectNumber"
    PROJECT_NAME = "ProjectName"


class ContractFields:
    ID_PRIMARY = "ID_Primary"
    PROJECT_ID = "ID_Projects"
    PROJECT_NUMBER_LOOKUP = "ProjectNumber_lk"
    CONTRACT_NUMBER = "ContractNumber"


class RFIFields:
    ID_PRIMARY = "ID_Primary"
    CONTRACT_ID = "ID_Contracts"
    RFI_NUMBER = "RFINumber"
