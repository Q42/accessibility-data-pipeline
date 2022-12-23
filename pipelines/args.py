def get_platform_from_args(args):
    platform = args[1] if len(args) > 1 else "<missing>"
    if platform != "android" and platform != "ios":
        raise Exception(f"Invalid platform: {platform}, pass 'android' or 'ios' as first argument")
    return platform


def get_project_from_args(args):
    project = args[2] if len(args) > 2 else None
    if not project:
        raise Exception("Pass project as second argument")
    return project
