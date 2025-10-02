"""Cloud folder connectors for GDrive, OneDrive, SharePoint, Dropbox, Box, S3, GCS."""

from src.connectors.cloud.base import CloudConnector, ConnectorConfig, StagedItem
from src.connectors.cloud.box import BoxConnector
from src.connectors.cloud.dropbox import DropboxConnector
from src.connectors.cloud.gcs import GCSConnector
from src.connectors.cloud.gdrive import GDriveConnector
from src.connectors.cloud.onedrive import OneDriveConnector
from src.connectors.cloud.s3 import S3Connector
from src.connectors.cloud.sharepoint import SharePointConnector

__all__ = [
    "CloudConnector",
    "StagedItem",
    "ConnectorConfig",
    "GDriveConnector",
    "OneDriveConnector",
    "SharePointConnector",
    "DropboxConnector",
    "BoxConnector",
    "S3Connector",
    "GCSConnector",
]
