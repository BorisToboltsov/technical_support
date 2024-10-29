from openproject.database.request import ApiRequests


class ApiWorkPackages:
    def __init__(self):
        self.api_requests = ApiRequests()

    def save_work_packages(self, subject: str, description: str) -> dict:
        """
        :param subject:
        :param description:
        :return:
        """
        parameters = {"subject": subject,
                      "project":  {"href": "/api/v3/projects/24"},
                      "description": {
                        "format": "markdown",
                        "raw": description,
                        "html": f"<p>{description}</p>"},
                      "type": {"href": "/api/v3/types/6"}} # 6 type - user story

        response = self.api_requests.post(parameters)

        return response
