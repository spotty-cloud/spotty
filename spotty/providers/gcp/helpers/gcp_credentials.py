from google.auth import default


class GcpCredentials(object):
    def __init__(self):
        credentials, effective_project_id = default()

        self._credentials = credentials
        self._project_id = effective_project_id

    @property
    def project_id(self):
        return self._project_id

    @property
    def service_account_email(self):
        return self._credentials.service_account_email
