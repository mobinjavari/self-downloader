class ConfigErrors:
    MISSING_CREDENTIALS = "API_ID and API_HASH must be set in the .env file"
    PLACEHOLDER_CREDENTIALS = (
        "API_ID/API_HASH in .env still have placeholder values — "
        "replace them with your real credentials from my.telegram.org"
    )
    INVALID_API_ID = "API_ID must be a valid integer, got: {value!r}"


class ClientMessages:
    ACTION_DOWNLOADING = "Downloading"
    ACTION_UPLOADING = "Uploading"
    PROGRESS = "{action}: {percent:.1f}% complete"
    MEDIA_TYPE_VIDEO = "video"
    MEDIA_TYPE_PHOTO = "photo"
    INCOMING_MEDIA = "Incoming {media_type} from `{sender_id}` at {timestamp}\nDownloading/uploading..."
    SAVED = "{media_type} from `{sender_id}` saved to Saved Messages."
    OPERATION_FAILED = "Operation failed:\n\n`{error}`"
    RETRY_BUTTON = "Retry"
    RETRY_FAILED_ALERT = "Retry failed"
    DOWNLOAD_NO_PATH = "Download returned no file path"


class ClientLogs:
    FORWARDED = "[%s] Forwarded media from %s"
    FORWARD_FAILED = "[%s] Forward failed (%s), falling back to download/upload"
    PROCESS_FAILED = "[%s] Failed to process media from %s"
    RETRY_FAILED = "[%s] Retry failed"


class RunnerLogs:
    NO_ENABLED_ACCOUNTS = "No enabled accounts found. Add one with: ./manage.sh accounts"
    NOT_AUTHORIZED = "[%s] Session not authorized. Log in first with: ./manage.sh accounts"
    CLIENT_START_FAILED = "[%s] Failed to start client: %s"
    CLIENT_STARTED = "[%s] Client started"
    CLIENT_CRASHED = "[%s] Client crashed: %s"
    NO_AUTHORIZED_ACCOUNTS = "No authorized accounts to run. Exiting."


class ConsoleMessages:
    MENU = """
[bold cyan]Self-Downloader Account Manager[/bold cyan]
1) List accounts
2) Add account (and log in)
3) Edit account
4) Delete account
0) Exit
"""
    TABLE_TITLE = "Self-Downloader Accounts"
    COLUMN_ID = "ID"
    COLUMN_LABEL = "Label"
    COLUMN_ENABLED = "Enabled"
    COLUMN_NORMAL_MEDIA = "Normal media"
    COLUMN_TIMED_MEDIA = "Timed media"
    COLUMN_UPDATED_AT = "Updated at"
    YES = "Yes"
    NO = "No"
    NO_ACCOUNTS = "[yellow]No accounts yet.[/yellow]"

    PROMPT_BOOL = "{question} [{suffix}]: "
    SUFFIX_DEFAULT_YES = "Y/n"
    SUFFIX_DEFAULT_NO = "y/N"
    PROMPT_LABEL = "Account label (unique, e.g. main): "
    LABEL_EMPTY = "[red]Label cannot be empty.[/red]"
    LABEL_EXISTS = "[red]An account with this label already exists.[/red]"
    ASK_SAVE_NORMAL_MEDIA = "Save normal media?"
    ASK_SAVE_TIMED_MEDIA = "Save timed (self-destructing) media?"
    ASK_ENABLED = "Enabled?"
    STARTING_LOGIN = "Starting Telegram login..."
    LOGIN_SUCCESS = "[green]Logged in as {name} ({user_id})[/green]"
    LOGIN_FAILED = "[red]Login failed: {error}[/red]"
    ACCOUNT_ADDED = "[green]Account added.[/green]"
    PROMPT_EDIT_LABEL = "Label of the account to edit: "
    ACCOUNT_NOT_FOUND = "[red]Account not found.[/red]"
    ACCOUNT_UPDATED = "[green]Account updated.[/green]"
    PROMPT_DELETE_LABEL = "Label of the account to delete: "
    CONFIRM_DELETE = "Delete '{label}'? This cannot be undone."
    ACCOUNT_DELETED = "[green]Account deleted.[/green]"
    CHOOSE_OPTION = "Choose an option: "
    INVALID_OPTION = "[red]Invalid option.[/red]"
    UNEXPECTED_ERROR = "[red]Unexpected error: {error}[/red]"
    CONFIG_ERROR = "[red]Configuration error: {error}[/red]"
