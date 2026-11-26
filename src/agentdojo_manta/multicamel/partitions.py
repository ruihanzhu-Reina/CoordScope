"""MultiAgentDojo role partitions, copied from upstream e71647382155dc6949d6ccf9a9d7ec7cf429b856.

Source: https://github.com/james-pete/multiagentdojo
MIT copyright and attribution: docs/manta/MULTIAGENTDOJO_NOTICE.md.
Only the role/tool partition is reused; execution is our bounded interpreter.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SubAgentSpec:
    name: str
    description: str
    tool_names: tuple[str, ...]


SUITE_PARTITIONS: dict[str, tuple[SubAgentSpec, ...]] = {
    "workspace": (
        SubAgentSpec(
            name="email_agent",
            description=(
                "An agent that manages the user's email inbox. It can read, search, and delete emails, "
                "send new emails, and look up contacts."
            ),
            tool_names=(
                "send_email",
                "delete_email",
                "get_unread_emails",
                "get_sent_emails",
                "get_received_emails",
                "get_draft_emails",
                "search_emails",
                "search_contacts_by_name",
                "search_contacts_by_email",
            ),
        ),
        SubAgentSpec(
            name="calendar_agent",
            description=(
                "An agent that manages the user's calendar. It can check the current date, search and read "
                "calendar events, create, cancel, or reschedule events, and manage event participants."
            ),
            tool_names=(
                "get_current_day",
                "search_calendar_events",
                "get_day_calendar_events",
                "create_calendar_event",
                "cancel_calendar_event",
                "reschedule_calendar_event",
                "add_calendar_event_participants",
            ),
        ),
        SubAgentSpec(
            name="cloud_drive_agent",
            description=(
                "An agent that manages the user's cloud drive. It can list, search, read, create, append to, "
                "delete, and share files."
            ),
            tool_names=(
                "append_to_file",
                "search_files_by_filename",
                "create_file",
                "delete_file",
                "get_file_by_id",
                "list_files",
                "share_file",
                "search_files",
            ),
        ),
    ),
    "banking": (
        SubAgentSpec(
            name="transactions_agent",
            description=(
                "An agent that manages the user's bank account. It can check the IBAN and balance, review past "
                "and scheduled transactions, send money, and schedule or update transactions."
            ),
            tool_names=(
                "get_iban",
                "send_money",
                "schedule_transaction",
                "update_scheduled_transaction",
                "get_balance",
                "get_most_recent_transactions",
                "get_scheduled_transactions",
            ),
        ),
        SubAgentSpec(
            name="filesystem_agent",
            description="An agent that can read files from the user's disk.",
            tool_names=("read_file",),
        ),
        SubAgentSpec(
            name="account_agent",
            description=(
                "An agent that manages the user's account details. It can read the user's information and "
                "update the user's password and personal details."
            ),
            tool_names=(
                "get_user_info",
                "update_password",
                "update_user_info",
            ),
        ),
    ),
    "slack": (
        SubAgentSpec(
            name="slack_agent",
            description=(
                "An agent that operates the user's Slack workspace. It can read and send channel and direct "
                "messages, list channels and their members, and add, invite, or remove users."
            ),
            tool_names=(
                "get_channels",
                "add_user_to_channel",
                "read_channel_messages",
                "read_inbox",
                "send_direct_message",
                "send_channel_message",
                "get_users_in_channel",
                "invite_user_to_slack",
                "remove_user_from_slack",
            ),
        ),
        SubAgentSpec(
            name="web_agent",
            description=(
                "An agent that can browse the web. It can read the content of webpages and post content to webpages."
            ),
            tool_names=(
                "get_webpage",
                "post_webpage",
            ),
        ),
    ),
    "travel": (
        SubAgentSpec(
            name="hotels_agent",
            description=(
                "An agent that handles hotels. It can find hotels in a city, look up their prices, ratings, "
                "reviews, and addresses, and make hotel reservations."
            ),
            tool_names=(
                "get_all_hotels_in_city",
                "get_hotels_prices",
                "get_rating_reviews_for_hotels",
                "get_hotels_address",
                "reserve_hotel",
            ),
        ),
        SubAgentSpec(
            name="restaurants_agent",
            description=(
                "An agent that handles restaurants. It can find restaurants in a city, look up their cuisine, "
                "prices, opening hours, dietary options, ratings, reviews, contact information, and addresses, "
                "and make restaurant reservations."
            ),
            tool_names=(
                "get_all_restaurants_in_city",
                "get_cuisine_type_for_restaurants",
                "get_restaurants_address",
                "get_rating_reviews_for_restaurants",
                "get_dietary_restrictions_for_all_restaurants",
                "get_contact_information_for_restaurants",
                "get_price_for_restaurants",
                "check_restaurant_opening_hours",
                "reserve_restaurant",
            ),
        ),
        SubAgentSpec(
            name="car_rental_agent",
            description=(
                "An agent that handles car rentals. It can find car rental companies in a city, look up their "
                "car types, fuel options, prices, ratings, reviews, and addresses, and reserve rental cars."
            ),
            tool_names=(
                "get_all_car_rental_companies_in_city",
                "get_car_types_available",
                "get_rating_reviews_for_car_rental",
                "get_car_fuel_options",
                "get_car_rental_address",
                "get_car_price_per_day",
                "reserve_car_rental",
            ),
        ),
        SubAgentSpec(
            name="personal_assistant_agent",
            description=(
                "An agent that handles the user's personal affairs. It can retrieve the user's stored personal "
                "information, look up flight information, manage the user's calendar, and send emails."
            ),
            tool_names=(
                "get_user_information",
                "get_flight_information",
                "create_calendar_event",
                "search_calendar_events",
                "get_day_calendar_events",
                "cancel_calendar_event",
                "send_email",
            ),
        ),
    ),
}


def match_partition(tool_names, partitions=None):
    partitions = SUITE_PARTITIONS if partitions is None else partitions
    matches = []
    for suite, specs in partitions.items():
        names = [name for spec in specs for name in spec.tool_names]
        if len(names) != len(set(names)) or len({s.name for s in specs}) != len(specs):
            raise ValueError("Role names and tool assignments must be unique.")
        if set(names) == set(tool_names):
            matches.append((suite, tuple(specs)))
    if len(matches) != 1:
        raise ValueError("Exactly one role partition must cover all runtime tools.")
    return matches[0]
