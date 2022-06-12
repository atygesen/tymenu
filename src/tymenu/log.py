from flask import current_app


def get_logger():
    return current_app.logger


def log_info(*args, **kwargs):
    get_logger().info(*args, **kwargs)
