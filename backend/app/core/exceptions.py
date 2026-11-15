class ServiceError(Exception):
    def __init__(self, message: str, status: int = 503, retry_after_seconds: int | None = None):
        super().__init__(message)
        self.status = status
        self.retry_after_seconds = retry_after_seconds
