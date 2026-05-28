class Layouts:
    """Centralized layout names used by the SDK."""

    PROJECTS = "ImportProjects"
    CONTRACTS = "ImportContracts"
    RFIS = "ImportRFILog"
    SUBMITTALS = "ImportSubmittal"
    SUBMITTAL_ITEMS = "ImportSubmittalItems"
    SUBMITTAL_REVIEW = "ImportSubmittalReview"
    PEOPLE = "ImportPeople"
    CAANS = "ImportCAANs"


class ProjectFields:
    """Field names used by the projects layout."""

    ID_PRIMARY = "ID_Primary"
    PROJECT_NUMBER = "ProjectNumber"
    PROJECT_NAME = "ProjectName"


class ContractFields:
    """Field names used by the contracts layout."""

    ID_PRIMARY = "ID_Primary"
    PROJECT_ID = "ID_Projects"
    PROJECT_NUMBER_LOOKUP = "ProjectNumber_lk"
    EFFECTIVE_CONTRACT_NUMBER = "ProjectNumber_lk"
    CONTRACT_NUMBER = "ContractNumber"
    LEGACY_CONTRACT_NUMBER = "ContractNumber"


class RFIFields:
    """Field names used by the RFI layout."""

    ID_PRIMARY = "ID_Primary"
    CONTRACT_ID = "ID_Contracts"
    RFI_NUMBER = "RFINumber"


class CAANFields:
    """Field names used by the CAANs layout."""

    ID_PRIMARY = "ID_Primary"
    CAAN = "CAAN"
    NAME = "Name"
    DESCRIPTION = "Description"
