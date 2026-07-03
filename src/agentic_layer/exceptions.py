"""Domain exceptions for the FHIR query validator factory."""


class FhirValidatorError(Exception):
    """Base error for validator factory operations."""


class UnknownServerKeyError(FhirValidatorError, ValueError):
    """Raised when server_key does not match a registered server."""


class AuthenticationRequiredError(FhirValidatorError):
    """Raised when a protected server is accessed without credentials."""


class CapabilityFetchError(FhirValidatorError):
    """Raised when CapabilityStatement cannot be retrieved."""