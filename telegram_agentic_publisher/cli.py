"""Command-line interface for telegram-agentic-publisher."""

import asyncio
import sys
import json
from pathlib import Path
import click
from colorama import init, Fore, Style
from .auth.authenticator import TelegramAuthenticator
from .auth.session_manager import SessionManager
from .core.publisher import TelegramPublisher
from .utils.config import Config
from .utils.logger import setup_logger

# Initialize colorama
init(autoreset=True)

logger = setup_logger("cli")


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to .env config file")
@click.pass_context
def cli(ctx, config):
    """Telegram Agentic Publisher - Post to Telegram channels via user accounts."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = Config(config)
    except ValueError as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--phone", "-p", prompt=True, help="Phone number in international format")
@click.option("--name", "-n", help="Session name for identification")
@click.pass_context
def auth(ctx, phone, name):
    """Authenticate and create a new session."""
    config = ctx.obj["config"]

    async def do_auth():
        # Create session manager
        session_mgr = SessionManager(config.session_storage_path, config.session_encryption_key)

        # Create authenticator
        auth = TelegramAuthenticator(config.api_id, config.api_hash)

        try:
            # Authenticate
            click.echo(f"{Fore.CYAN}Sending authentication code to {phone}...{Style.RESET_ALL}")
            user_info = await auth.authenticate(phone)

            if not user_info:
                click.echo(f"{Fore.RED}Authentication failed{Style.RESET_ALL}", err=True)
                return

            # Save session
            session_string = auth.get_session_string()
            if not session_string:
                click.echo(f"{Fore.RED}Failed to get session string{Style.RESET_ALL}", err=True)
                return

            session_name = name or f"{user_info['username'] or user_info['first_name']}_session"
            session_id = session_mgr.create_session(
                session_name, phone, session_string, user_info
            )

            click.echo(f"{Fore.GREEN}✓ Successfully authenticated as @{user_info['username']} ({user_info['first_name']}){Style.RESET_ALL}")
            click.echo(f"{Fore.GREEN}✓ Session saved with ID: {session_id}{Style.RESET_ALL}")

        finally:
            await auth.disconnect()

    asyncio.run(do_auth())


@cli.command()
@click.pass_context
def sessions(ctx):
    """List all saved sessions."""
    config = ctx.obj["config"]
    session_mgr = SessionManager(config.session_storage_path, config.session_encryption_key)

    sessions_list = session_mgr.list_sessions()

    if not sessions_list:
        click.echo(f"{Fore.YELLOW}No sessions found{Style.RESET_ALL}")
        return

    click.echo(f"\n{Fore.CYAN}Available Sessions:{Style.RESET_ALL}")
    click.echo("-" * 80)

    for session in sessions_list:
        status_color = Fore.GREEN if session["status"] == "active" else Fore.RED
        click.echo(f"ID: {Fore.WHITE}{session['id']}{Style.RESET_ALL}")
        click.echo(f"  Name: {session['name']}")
        click.echo(f"  Username: @{session['username']}")
        click.echo(f"  Status: {status_color}{session['status']}{Style.RESET_ALL}")
        click.echo(f"  Created: {session['created_at']}")
        click.echo(f"  Last Used: {session['last_used']}")
        click.echo(f"  Usage Count: {session['usage_count']}")
        click.echo("-" * 80)


@cli.command()
@click.argument("channel")
@click.option("--session", "-s", help="Session ID or name to use")
@click.option("--content", "-t", help="Text content to post")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read content from file")
@click.option("--media", "-m", multiple=True, help="Media files or URLs (can be used multiple times)")
@click.option("--template", help="Template file path")
@click.option("--data", help="JSON data for template (file or string)")
@click.option("--no-preview", is_flag=True, help="Disable link previews")
@click.option("--silent", is_flag=True, help="Send silently (no notification)")
@click.pass_context
def post(ctx, channel, session, content, file, media, template, data, no_preview, silent):
    """Post content to a Telegram channel."""
    config = ctx.obj["config"]

    # Get content
    if file:
        content = Path(file).read_text()
    elif not content and not media:
        click.echo(f"{Fore.RED}Error: No content or media provided{Style.RESET_ALL}", err=True)
        return

    # Parse template data if provided
    template_content = None
    template_data = None
    if template:
        template_content = Path(template).read_text()
        if data:
            if Path(data).exists():
                template_data = json.loads(Path(data).read_text())
            else:
                template_data = json.loads(data)

    async def do_post():
        # Create session manager
        session_mgr = SessionManager(config.session_storage_path, config.session_encryption_key)

        # Get session
        if not session:
            sessions_list = session_mgr.list_sessions()
            if not sessions_list:
                click.echo(f"{Fore.RED}No sessions available. Run 'auth' first.{Style.RESET_ALL}", err=True)
                return

            # Use first active session
            active_sessions = [s for s in sessions_list if s["status"] == "active"]
            if not active_sessions:
                click.echo(f"{Fore.RED}No active sessions available{Style.RESET_ALL}", err=True)
                return

            session_info = active_sessions[0]
            session_id = session_info["id"]
            click.echo(
                f"{Fore.CYAN}Using session: {session_info['name']} "
                f"(@{session_info['username']}){Style.RESET_ALL}"
            )
        else:
            # Find session by ID or name
            session_info = session_mgr.get_session(session) or session_mgr.get_session_by_name(session)
            if not session_info:
                click.echo(f"{Fore.RED}Session '{session}' not found{Style.RESET_ALL}", err=True)
                return
            session_id = session_info["id"]

        # Create publisher
        publisher = TelegramPublisher(
            config.api_id,
            config.api_hash,
            session_id=session_id,
            session_manager=session_mgr
        )

        try:
            # Connect
            click.echo(f"{Fore.CYAN}Connecting to Telegram...{Style.RESET_ALL}")
            if not await publisher.connect():
                click.echo(f"{Fore.RED}Failed to connect{Style.RESET_ALL}", err=True)
                return

            # Publish
            click.echo(f"{Fore.CYAN}Publishing to {channel}...{Style.RESET_ALL}")
            message_id, message_url = await publisher.publish(
                channel=channel,
                content=content,
                media=list(media) if media else None,
                template=template_content,
                template_data=template_data,
                link_preview=not no_preview,
                silent=silent,
            )

            if message_id:
                click.echo(f"{Fore.GREEN}✓ Successfully published!{Style.RESET_ALL}")
                click.echo(f"{Fore.GREEN}Message URL: {message_url}{Style.RESET_ALL}")
            else:
                click.echo(f"{Fore.RED}Failed to publish{Style.RESET_ALL}", err=True)

        finally:
            await publisher.disconnect()

    asyncio.run(do_post())


@cli.command()
@click.argument("channel")
@click.option("--session", "-s", help="Session ID or name to use")
@click.pass_context
def info(ctx, channel, session):
    """Get information about a Telegram channel."""
    config = ctx.obj["config"]

    async def do_info():
        # Create session manager
        session_mgr = SessionManager(config.session_storage_path, config.session_encryption_key)

        # Get session
        if not session:
            sessions_list = session_mgr.list_sessions()
            if sessions_list:
                session_info = sessions_list[0]
                session_id = session_info["id"]
            else:
                click.echo(f"{Fore.RED}No sessions available{Style.RESET_ALL}", err=True)
                return
        else:
            session_info = session_mgr.get_session(session) or session_mgr.get_session_by_name(session)
            if not session_info:
                click.echo(f"{Fore.RED}Session '{session}' not found{Style.RESET_ALL}", err=True)
                return
            session_id = session_info["id"]

        # Create publisher
        publisher = TelegramPublisher(
            config.api_id,
            config.api_hash,
            session_id=session_id,
            session_manager=session_mgr
        )

        try:
            # Connect
            if not await publisher.connect():
                click.echo(f"{Fore.RED}Failed to connect{Style.RESET_ALL}", err=True)
                return

            # Get channel info
            info = await publisher.get_channel_info(channel)

            if info:
                click.echo(f"\n{Fore.CYAN}Channel Information:{Style.RESET_ALL}")
                click.echo("-" * 40)
                click.echo(f"Title: {info['title']}")
                click.echo(f"ID: {info['id']}")
                click.echo(f"Username: @{info['username']}" if info['username'] else "Username: None (private)")
                click.echo(f"Members: {info['participants_count']}")
                click.echo(f"Type: {'Channel' if info['is_channel'] else 'Group'}")
                click.echo(f"Private: {'Yes' if info['is_private'] else 'No'}")
            else:
                click.echo(f"{Fore.RED}Failed to get channel info{Style.RESET_ALL}", err=True)

        finally:
            await publisher.disconnect()

    asyncio.run(do_info())


def main():
    """Main entry point."""
    cli()
