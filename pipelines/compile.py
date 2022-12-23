import json
from kfp.v2 import compiler
from pipelines.pipeline_android import pipeline_android
from pipelines.pipeline_ios import pipeline_ios


# load universal pipeline settings
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# pipeline version
pipeline_version = config["pipeline_version"]


def compile_pipeline(platform):
    pipeline_func = get_pipeline_func(platform)
    template_path = get_template_path(platform)
    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=template_path
    )
    return template_path


def get_pipeline_func(platform):
    if platform == "ios":
        return pipeline_ios
    elif platform == "android":
        return pipeline_android
    else:
        raise Exception(f"invalid platform {platform}")


def get_template_path(platform):
    if platform == "ios" or platform == "android":
        return f"firestore-export-bigquery-import-{platform}-{pipeline_version}.json"
    else:
        raise Exception(f"invalid platform {platform}")