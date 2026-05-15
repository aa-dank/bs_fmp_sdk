class FileMakerError(Exception):
    """Base exception for unrecoverable FileMaker SDK errors."""


class FileMakerAuthError(FileMakerError):
    """Raised when FileMaker authentication fails."""


class FileMakerLayoutError(FileMakerError):
    """Raised when a FileMaker layout cannot be found or accessed."""


class FileMakerNotFoundError(FileMakerError):
    """Raised when an expected record cannot be found."""


class FileMakerAmbiguousResultError(FileMakerError):
    """Raised when a query expected one record but found multiple."""


class FileMakerDuplicateError(FileMakerError):
    """Raised when a create operation would produce a duplicate record."""


class FileMakerValidationError(FileMakerError):
    """Raised when required input data is missing or invalid."""
