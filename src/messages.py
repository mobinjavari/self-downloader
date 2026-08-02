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
    OPERATION_FAILED = "Operation failed:\n\n`{error}`"
    SENDER_UNKNOWN_NAME = "Unknown"
    SENDER_NO_USERNAME = "no username"
    SENDER_INFO = "{full_name} ({username}, id: {sender_id})"
    CAPTION_WITH_TEXT = "From {sender_info}\n\n{text}"
    CAPTION_WITHOUT_TEXT = "From {sender_info}"
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
    PROMPT_LABEL = "Account label (unique, e.g. main, empty to cancel): "
    LABEL_EXISTS = "[red]An account with this label already exists.[/red]"
    ASK_SAVE_NORMAL_MEDIA = "Save normal media?"
    ASK_SAVE_TIMED_MEDIA = "Save timed (self-destructing) media?"
    ASK_ENABLED = "Enabled?"
    STARTING_LOGIN = "Starting Telegram login..."
    LOGIN_SUCCESS = "[green]Logged in as {name} ({user_id})[/green]"
    LOGIN_FAILED = "[red]Login failed: {error}[/red]"
    ACCOUNT_ADDED = "[green]Account added.[/green]"
    PROMPT_EDIT_ID = "ID of the account to edit (0 to cancel): "
    PROMPT_DELETE_ID = "ID of the account to delete (0 to cancel): "
    INVALID_ID = "[red]Please enter a valid account ID from the table above.[/red]"
    ACCOUNT_NOT_FOUND = "[red]Account not found.[/red]"
    ACCOUNT_UPDATED = "[green]Account updated.[/green]"
    CONFIRM_DELETE = "Delete '{label}' (id {account_id})? This cannot be undone."
    ACCOUNT_DELETED = "[green]Account deleted.[/green]"
    CHOOSE_OPTION = "Choose an option: "
    INVALID_OPTION = "[red]Invalid option.[/red]"
    UNEXPECTED_ERROR = "[red]Unexpected error: {error}[/red]"
    CONFIG_ERROR = "[red]Configuration error: {error}[/red]"
    PRESS_ENTER = "\n[dim]Press Enter to continue...[/dim]"
