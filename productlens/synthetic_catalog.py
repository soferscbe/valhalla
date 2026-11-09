"""Authored synthetic request families, not observations from real customers.

Each family is one specific requested capability with three paraphrases. Families
are the indivisible split and semantic-duplicate annotation unit. Related but
different capabilities share a broader theme, not a duplicate-group label.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Family:
    key: str
    themes: tuple[str, ...]
    kind: str
    phrases: tuple[str, str, str]


def family(key, theme, *phrases):
    return Family(key, (theme,), "clear", tuple(phrases))


FAMILIES = (
    family("scheduled_email", "reporting",
           "Email the usage report to our team automatically every Monday.",
           "Can we schedule a weekly usage summary to arrive in our inbox?",
           "I download and send the same report each week; please automate that email."),
    family("report_csv", "reporting",
           "Let me download the report rows as a CSV file.",
           "We need a comma-separated export of the data behind a report.",
           "Copying report cells into a spreadsheet is slow. Add a CSV download."),
    family("report_filters", "reporting",
           "Remember my report filters so I do not enter them again next time.",
           "Please save the date and team filters as a reusable report view.",
           "Every visit resets our reporting criteria; let us keep a saved filter preset."),
    family("report_timezone", "reporting",
           "Show daily report totals using our local time zone.",
           "Our reporting day should follow the workspace timezone instead of UTC.",
           "Midnight UTC splits our working day in two; group report dates in local time."),
    family("audit_actor", "audit_history",
           "Record which administrator changed a workspace setting and when.",
           "We need an audit trail that names the person behind every configuration change.",
           "Who altered these settings? Keep an administrator change history with timestamps."),
    family("audit_export", "audit_history",
           "Let our compliance team export the audit log for a selected date range.",
           "We need to download historical security events for an external review.",
           "Give reviewers a file containing the audit entries between two dates."),
    family("audit_retention", "audit_history",
           "Keep audit events for a full year before deleting them.",
           "Our security review needs twelve months of retained activity history.",
           "The event history expires too soon; extend log retention to one year."),
    family("audit_search", "audit_history",
           "Allow searching the audit history by actor and action type.",
           "Finding one administrator's events requires scrolling through everything. Add log filters.",
           "Can I narrow security records to a person and a particular kind of change?"),
    family("saml_login", "identity_access",
           "Support SAML single sign-on with our corporate identity provider.",
           "We want employees to use the company SAML login for this workspace.",
           "Separate passwords are a rollout blocker; integrate our SAML-based sign-in."),
    family("scim_provisioning", "identity_access",
           "Provision and deactivate users automatically through SCIM.",
           "Sync employee joiners and leavers from our directory using SCIM.",
           "Manual account offboarding is risky. Add SCIM lifecycle management."),
    family("enforce_mfa", "identity_access",
           "Let workspace owners require multi-factor authentication for everyone.",
           "We need an organisation policy that enforces a second factor at sign-in.",
           "Users can skip MFA today; give administrators a way to make it mandatory."),
    family("session_timeout", "identity_access",
           "Allow admins to set an inactivity timeout for user sessions.",
           "Automatically sign people out after an administrator-defined idle period.",
           "Unattended sessions stay open too long. We need configurable idle logout."),
    family("dashboard_colours", "dashboard_customisation",
           "Let me choose the accent colour on my dashboard.",
           "I would like a different colour palette for the overview screen.",
           "Please add personal colour choices to the dashboard tiles."),
    family("dashboard_order", "dashboard_customisation",
           "Let me drag dashboard tiles into a different order.",
           "Can I rearrange the overview cards to match how I work?",
           "The dashboard layout is fixed; let users move the tiles around."),
    family("dashboard_density", "dashboard_customisation",
           "Add a compact view with less space between dashboard cards.",
           "The overview has too much padding. Offer a denser layout.",
           "I want more tiles visible at once without scrolling; reduce dashboard spacing."),
    family("dashboard_icons", "dashboard_customisation",
           "Let me choose an icon for each dashboard tile.",
           "Custom symbols on overview cards would help me recognise them.",
           "Please allow personalising the little icons used on dashboard widgets."),
    family("usage_threshold", "usage_alerts",
           "Notify us when we reach eighty percent of our monthly usage allowance.",
           "Send a warning before our included quota runs out.",
           "We only notice limits after hitting them; add an early threshold alert."),
    family("usage_forecast", "usage_alerts",
           "Predict whether our current usage rate will exceed this month's allowance.",
           "Show an end-of-month quota forecast based on recent consumption.",
           "At this pace will we run out? Estimate how much of our plan we will use."),
    family("usage_recipients", "usage_alerts",
           "Send quota warnings to a configurable list of team members.",
           "Our billing contact is not the only person who needs usage alerts; add more recipients.",
           "Let us choose several email addresses for consumption notifications."),
    family("usage_webhook", "usage_alerts",
           "Fire a webhook when usage crosses a configured quota threshold.",
           "We want our own automation to receive a usage-limit callback.",
           "Post threshold alerts to our endpoint so we can respond automatically."),
    family("bulk_owner", "bulk_editing",
           "Reassign the owner of many selected records in one action.",
           "Changing ownership one item at a time is tedious; support bulk reassignment.",
           "Let us select a batch of items and give all of them to another teammate."),
    family("bulk_tags", "bulk_editing",
           "Apply a tag to all selected records at once.",
           "Please add batch tagging instead of opening every item separately.",
           "We need to label a whole selection of items with the same tag."),
    family("bulk_archive", "bulk_editing",
           "Archive multiple selected records with one confirmation.",
           "Cleaning up old items takes too many clicks; let us archive a batch.",
           "Can I select several completed entries and move them all to the archive?"),
    family("bulk_undo", "bulk_editing",
           "Allow undoing the most recent bulk edit.",
           "If a batch update changes the wrong items, we need a single rollback action.",
           "Please restore the previous values after an accidental mass update."),
    Family("mixed_report_audit", ("reporting", "audit_history"), "overlapping", (
        "Email a weekly usage report and include a downloadable history of admin changes.",
        "We need scheduled reporting as well as an export of security events.",
        "Could the weekly summary arrive by email, with the administrator audit trail attached?")),
    Family("mixed_identity_audit", ("identity_access", "audit_history"), "overlapping", (
        "Require a second factor when signing in and retain a history of admin changes.",
        "We need mandatory MFA plus a searchable trail of configuration updates.",
        "Security needs both enforced two-step login and visibility into who changed settings.")),
    Family("mixed_usage_report", ("usage_alerts", "reporting"), "overlapping", (
        "Warn us before our quota runs out and include those numbers in a weekly emailed report.",
        "Please send early consumption alerts as well as scheduled usage summaries.",
        "Our team needs quota notifications and recurring report delivery together.")),
    Family("mixed_dashboard_bulk", ("dashboard_customisation", "bulk_editing"), "overlapping", (
        "Let me rearrange dashboard cards and change the owner of selected records together.",
        "We want a personalised tile layout and a way to reassign items in bulk.",
        "Moving overview widgets and batch ownership changes would both help our team.")),
    Family("vague_workflow", (), "ambiguous", (
        "This workflow needs to be easier.", "There are too many steps here.",
        "Please make the whole process less confusing.")),
    Family("vague_visibility", (), "ambiguous", (
        "I cannot find what I need in this screen.", "The information is difficult to follow.",
        "Can you make things clearer for our team?")),
    Family("vague_reliability", (), "ambiguous", (
        "It did not work as expected yesterday.", "Something seems wrong, but I cannot reproduce it.",
        "We sometimes get unexpected behaviour.")),
    Family("vague_change", (), "ambiguous", (
        "Could you improve this in the next update?", "We need something better than this.",
        "The current experience does not quite fit our needs.")),
)
