import json
from google.cloud import bigquery


class Config:
    def __init__(self, scope=None):
        self.project_name = self.get_project_name()
        self.client = bigquery.Client(project=self.project_name)
        self.config = self.get_config(scope)
        self.pipeline_version = "v3"

    @staticmethod
    def get_project_name():
        # load universal pipeline settings
        with open("../settings.json", "r") as settings_file:
            settings = json.load(settings_file)
        return settings["project_name"]

    @staticmethod
    def get_config(scope) -> {}:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        if scope:
            return config[scope]
        return config
