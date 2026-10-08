# Client failures stay below the service layer: services translate them into domain errors.
class ClientError(Exception):
    pass


class LoginThrottleUnavailableError(ClientError):
    pass
