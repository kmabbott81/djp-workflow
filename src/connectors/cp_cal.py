"""Cross-Platform Connector Abstraction Layer (CP-CAL).

Provides unified endpoint mapping and schema normalization for
multiple communication platforms (Teams, Outlook, Slack, etc.).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EndpointMap:
    """Endpoint URL templates for a resource type on a service.

    Attributes:
        list_url: URL template for listing resources
        get_url: URL template for getting a specific resource
        create_url: URL template for creating a resource
        update_url: URL template for updating a resource
        delete_url: URL template for deleting a resource
    """

    list_url: str
    get_url: str
    create_url: str
    update_url: str
    delete_url: str


class SchemaAdapter:
    """Schema adapter for normalizing resource data across services.

    Converts service-specific schemas to a unified format and back.
    """

    @staticmethod
    def normalize_message(service: str, message: dict) -> dict:
        """Normalize message from service-specific schema to unified format.

        Args:
            service: Service name (teams, outlook, slack)
            message: Raw message from service

        Returns:
            Normalized message dict with fields:
                - id: Message ID
                - subject: Message subject (if applicable)
                - body: Message body text
                - from: Sender info
                - timestamp: Send/receive timestamp
                - metadata: Service-specific extras
        """
        if service == "teams":
            return {
                "id": message.get("id", ""),
                "subject": message.get("subject", ""),
                "body": message.get("body", {}).get("content", ""),
                "from": message.get("from", {}).get("user", {}).get("displayName", ""),
                "timestamp": message.get("createdDateTime", ""),
                "metadata": {
                    "importance": message.get("importance"),
                    "messageType": message.get("messageType"),
                },
            }

        elif service == "outlook":
            return {
                "id": message.get("id", ""),
                "subject": message.get("subject", ""),
                "body": message.get("body", {}).get("content", ""),
                "from": message.get("from", {}).get("emailAddress", {}).get("address", ""),
                "timestamp": message.get("receivedDateTime", ""),
                "metadata": {
                    "importance": message.get("importance"),
                    "hasAttachments": message.get("hasAttachments"),
                },
            }

        elif service == "slack":
            return {
                "id": message.get("ts", ""),
                "subject": "",  # Slack doesn't have message subjects
                "body": message.get("text", ""),
                "from": message.get("user", ""),
                "timestamp": message.get("ts", ""),
                "metadata": {
                    "thread_ts": message.get("thread_ts"),
                    "channel": message.get("channel"),
                },
            }

        else:
            raise ValueError(f"Unsupported service: {service}")

    @staticmethod
    def denormalize_message(service: str, normalized: dict) -> dict:
        """Convert unified message format back to service-specific schema.

        Args:
            service: Service name
            normalized: Normalized message dict

        Returns:
            Service-specific message dict
        """
        if service == "teams":
            return {
                "subject": normalized.get("subject", ""),
                "body": {
                    "contentType": "text",
                    "content": normalized.get("body", ""),
                },
                "importance": normalized.get("metadata", {}).get("importance", "normal"),
            }

        elif service == "outlook":
            return {
                "subject": normalized.get("subject", ""),
                "body": {
                    "contentType": "text",
                    "content": normalized.get("body", ""),
                },
                "toRecipients": normalized.get("metadata", {}).get("toRecipients", []),
                "importance": normalized.get("metadata", {}).get("importance", "normal"),
            }

        elif service == "slack":
            return {
                "text": normalized.get("body", ""),
                "thread_ts": normalized.get("metadata", {}).get("thread_ts"),
            }

        else:
            raise ValueError(f"Unsupported service: {service}")

    @staticmethod
    def normalize_contact(service: str, contact: dict) -> dict:
        """Normalize contact from service-specific schema to unified format.

        Args:
            service: Service name
            contact: Raw contact from service

        Returns:
            Normalized contact dict with fields:
                - id: Contact ID
                - name: Display name
                - email: Primary email address
                - phone: Primary phone number (if applicable)
                - metadata: Service-specific extras
        """
        if service == "outlook":
            emails = contact.get("emailAddresses", [])
            primary_email = emails[0].get("address", "") if emails else ""

            return {
                "id": contact.get("id", ""),
                "name": contact.get("displayName", ""),
                "email": primary_email,
                "phone": contact.get("mobilePhone", ""),
                "metadata": {
                    "jobTitle": contact.get("jobTitle"),
                    "companyName": contact.get("companyName"),
                },
            }

        elif service == "teams":
            return {
                "id": contact.get("id", ""),
                "name": contact.get("displayName", ""),
                "email": contact.get("mail", ""),
                "phone": contact.get("businessPhones", [None])[0] if contact.get("businessPhones") else "",
                "metadata": {
                    "userPrincipalName": contact.get("userPrincipalName"),
                },
            }

        elif service == "slack":
            # Slack users
            profile = contact.get("profile", {})
            return {
                "id": contact.get("id", ""),
                "name": contact.get("real_name", "") or contact.get("name", ""),
                "email": profile.get("email", ""),
                "phone": profile.get("phone", ""),
                "metadata": {
                    "is_bot": contact.get("is_bot", False),
                    "is_admin": contact.get("is_admin", False),
                    "display_name": profile.get("display_name", ""),
                },
            }

        else:
            raise ValueError(f"Unsupported service for contacts: {service}")

    @staticmethod
    def normalize_event(service: str, event: dict) -> dict:
        """Normalize calendar event from service-specific schema to unified format.

        Args:
            service: Service name
            event: Raw event from service

        Returns:
            Normalized event dict with fields:
                - id: Event ID
                - title: Event title/subject
                - start: Start time
                - end: End time
                - location: Location info
                - metadata: Service-specific extras
        """
        if service == "outlook":
            return {
                "id": event.get("id", ""),
                "title": event.get("subject", ""),
                "start": event.get("start", {}).get("dateTime", ""),
                "end": event.get("end", {}).get("dateTime", ""),
                "location": event.get("location", {}).get("displayName", ""),
                "metadata": {
                    "organizer": event.get("organizer", {}),
                    "isOnlineMeeting": event.get("isOnlineMeeting"),
                },
            }

        else:
            raise ValueError(f"Unsupported service for events: {service}")


# Endpoint Registry: Maps (service, resource_type) to EndpointMap
ENDPOINT_REGISTRY: dict[tuple[str, str], EndpointMap] = {
    # Microsoft Teams
    ("teams", "messages"): EndpointMap(
        list_url="teams/{team_id}/channels/{channel_id}/messages",
        get_url="teams/{team_id}/channels/{channel_id}/messages/{resource_id}",
        create_url="teams/{team_id}/channels/{channel_id}/messages",
        update_url="teams/{team_id}/channels/{channel_id}/messages/{resource_id}",
        delete_url="teams/{team_id}/channels/{channel_id}/messages/{resource_id}/softDelete",
    ),
    ("teams", "channels"): EndpointMap(
        list_url="teams/{team_id}/channels",
        get_url="teams/{team_id}/channels/{resource_id}",
        create_url="teams/{team_id}/channels",
        update_url="teams/{team_id}/channels/{resource_id}",
        delete_url="teams/{team_id}/channels/{resource_id}",
    ),
    # Microsoft Outlook
    ("outlook", "messages"): EndpointMap(
        list_url="users/{user_id}/messages",
        get_url="users/{user_id}/messages/{resource_id}",
        create_url="users/{user_id}/sendMail",
        update_url="users/{user_id}/messages/{resource_id}",
        delete_url="users/{user_id}/messages/{resource_id}",
    ),
    ("outlook", "folders"): EndpointMap(
        list_url="users/{user_id}/mailFolders",
        get_url="users/{user_id}/mailFolders/{resource_id}",
        create_url="users/{user_id}/mailFolders",
        update_url="users/{user_id}/mailFolders/{resource_id}",
        delete_url="users/{user_id}/mailFolders/{resource_id}",
    ),
    ("outlook", "contacts"): EndpointMap(
        list_url="users/{user_id}/contacts",
        get_url="users/{user_id}/contacts/{resource_id}",
        create_url="users/{user_id}/contacts",
        update_url="users/{user_id}/contacts/{resource_id}",
        delete_url="users/{user_id}/contacts/{resource_id}",
    ),
    # Slack
    ("slack", "channels"): EndpointMap(
        list_url="conversations.list",
        get_url="conversations.info",
        create_url="conversations.create",
        update_url="conversations.rename",
        delete_url="conversations.archive",
    ),
    ("slack", "messages"): EndpointMap(
        list_url="conversations.history",
        get_url="conversations.history",
        create_url="chat.postMessage",
        update_url="chat.update",
        delete_url="chat.delete",
    ),
    ("slack", "users"): EndpointMap(
        list_url="users.list",
        get_url="users.info",
        create_url="",  # Not supported by Slack API
        update_url="users.profile.set",
        delete_url="",  # Not supported by Slack API
    ),
}


def get_endpoint_map(service: str, resource_type: str) -> Optional[EndpointMap]:
    """Get endpoint map for service and resource type.

    Args:
        service: Service name (teams, outlook, slack)
        resource_type: Resource type (messages, folders, contacts, etc.)

    Returns:
        EndpointMap if found, None otherwise
    """
    return ENDPOINT_REGISTRY.get((service, resource_type))
