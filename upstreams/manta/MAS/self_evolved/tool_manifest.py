"""Reviewed tool effects for the pinned AgentDojo tools.

This is an authority allowlist, not a name classifier. Resource domains are
coarse audit labels, not complete read/write footprints or cache dependencies.
Arguments remain sensitive even when their names sound harmless.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

Effect = Literal["read", "navigate", "send", "mutate", "consume", "unknown"]


@dataclass(frozen=True)
class ToolSpec:
    effect: Effect = "unknown"
    worker_allowed: bool = False
    argument_sensitivity: Literal["all"] = "all"
    resource_domain: str = "unknown"

    @property
    def side_effect(self) -> bool:
        """Unknown and observable reads must never be treated as pure reads."""
        return self.effect != "read"

    def is_argument_sensitive(self, name: str) -> bool:
        """Every supplied argument matters, including unrecognized arguments."""
        return True


# Migrated without effect changes from action_policy's manually reviewed table.
# Domains follow the pinned tool implementations; they confer no permission.
_DECLARATIONS = (
    ("read", "banking", """
        get_iban get_balance get_most_recent_transactions get_scheduled_transactions
    """),
    ("mutate", "banking", """
        set_balance set_iban send_money schedule_transaction update_scheduled_transaction
    """),
    ("read", "calendar", "get_day_calendar_events search_calendar_events get_current_day"),
    ("mutate", "calendar", """
        create_calendar_event cancel_calendar_event reschedule_calendar_event add_calendar_event_participants
    """),
    ("read", "email", """
        search_emails get_sent_emails get_received_emails get_draft_emails
        search_contacts_by_name search_contacts_by_email
    """),
    ("consume", "email", "get_unread_emails"),
    ("send", "email", "send_email"),
    ("mutate", "email", "delete_email"),
    ("read", "files", "search_files_by_filename get_file_by_id list_files search_files read_file"),
    ("send", "files", "share_file"),
    ("mutate", "files", "create_file delete_file append_to_file"),
    ("read", "slack", "get_channels read_channel_messages read_inbox get_users_in_channel"),
    ("send", "slack", "send_direct_message send_channel_message invite_user_to_slack"),
    ("mutate", "slack", "add_user_to_channel remove_user_from_slack"),
    ("read", "travel", """
        get_user_information get_all_hotels_in_city get_hotels_prices get_hotels_address
        get_rating_reviews_for_hotels get_all_restaurants_in_city get_restaurants_address
        get_rating_reviews_for_restaurants get_cuisine_type_for_restaurants
        get_dietary_restrictions_for_all_restaurants get_contact_information_for_restaurants
        get_price_for_restaurants check_restaurant_opening_hours get_all_car_rental_companies_in_city
        get_car_types_available get_rating_reviews_for_car_rental get_car_rental_address
        get_car_fuel_options get_car_price_per_day get_flight_information
    """),
    ("mutate", "travel", "reserve_hotel reserve_restaurant reserve_car_rental"),
    ("read", "account", "get_user_info"),
    ("mutate", "account", "update_password update_user_info"),
    ("navigate", "web", "get_webpage download_file"),
    ("mutate", "web", "post_webpage"),
)


def _build_manifest():
    specs = {}
    for kind, domain, names in _DECLARATIONS:
        for name in names.split():
            if name in specs:
                raise ValueError(f"Duplicate reviewed tool: {name}")
            specs[name] = ToolSpec(effect=kind, worker_allowed=kind == "read", resource_domain=domain)
    return MappingProxyType(specs)


TOOL_MANIFEST = _build_manifest()
_UNKNOWN = ToolSpec()


def tool_spec(name: str) -> ToolSpec:
    """Return immutable metadata, failing closed for every unreviewed name."""
    return TOOL_MANIFEST.get(name, _UNKNOWN)


def effect(name: str) -> Effect:
    return tool_spec(name).effect


PURE_READS = frozenset(name for name, spec in TOOL_MANIFEST.items() if spec.effect == "read")
NAVIGATION = frozenset(name for name, spec in TOOL_MANIFEST.items() if spec.effect == "navigate")
SEND = frozenset(name for name, spec in TOOL_MANIFEST.items() if spec.effect == "send")
MUTATE = frozenset(name for name, spec in TOOL_MANIFEST.items() if spec.effect == "mutate")
CONSUME = frozenset(name for name, spec in TOOL_MANIFEST.items() if spec.effect == "consume")

__all__ = ["CONSUME", "MUTATE", "NAVIGATION", "PURE_READS", "SEND", "TOOL_MANIFEST", "ToolSpec", "effect", "tool_spec"]
