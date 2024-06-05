"""This package implements the tentaclio gsheets client """

from tentaclio import STREAM_HANDLER_REGISTRY, StreamURLHandler  # noqa

from .clients.gsheets_client import GoogleSheetsFsClient  # noqa

STREAM_HANDLER_REGISTRY.register("gsheet", StreamURLHandler(GoogleSheetsFsClient))
STREAM_HANDLER_REGISTRY.register("gsheets", StreamURLHandler(GoogleSheetsFsClient))
