from __future__ import annotations

from LSP.plugin import LspPlugin
from LSP.plugin import OnPreStartContext
from LSP.plugin import PluginStartError
from pathlib import Path
from shutil import which
from typing import final
from typing_extensions import override
import io
import os
import shutil
import sublime
import urllib.request
import zipfile

SERVER_VERSION = '0.5.3'
RELEASE_URL = 'https://github.com/idleberg/nsis-lsp/releases/download/v{version}/nsis-lsp-{version}-{target}.zip'
USER_AGENT = 'Sublime Text LSP'

# Release assets are published per platform/arch. The musl Linux variants are deliberately
# unused - Sublime Text is glibc-linked, so the plain linux-* builds are the right ones.
TARGETS = {
    ('osx', 'arm64'): 'darwin-arm64',
    ('osx', 'x64'): 'darwin-x64',
    ('linux', 'arm64'): 'linux-arm64',
    ('linux', 'x64'): 'linux-x64',
    ('windows', 'arm64'): 'windows-arm64',
    ('windows', 'x64'): 'windows-x64',
}


def target() -> str | None:
    return TARGETS.get((sublime.platform(), sublime.arch()))


def binary_name() -> str:
    return 'nsis-lsp.exe' if sublime.platform() == 'windows' else 'nsis-lsp'


@final
class LspNsisPlugin(LspPlugin):

    @classmethod
    @override
    def on_pre_start_async(cls, context: OnPreStartContext) -> None:
        setting = context.configuration.root_settings.get('server_path')
        setting = setting if isinstance(setting, str) and setting else 'auto'
        if setting == 'auto':
            if cls.needs_install():
                cls.install()
            server_path = cls.managed_binary()
        else:
            server_path = cls.resolve_custom_path(setting)
        if not server_path.is_file():
            raise PluginStartError('nsis-lsp was not found at "{}"'.format(server_path))
        context.configuration.command = [str(server_path)]

    @classmethod
    def managed_binary(cls) -> Path:
        return cls.plugin_storage_path / 'bin' / binary_name()

    @classmethod
    def version_file(cls) -> Path:
        return cls.plugin_storage_path / 'VERSION'

    @classmethod
    def resolve_custom_path(cls, setting: str) -> Path:
        """Resolve a user-provided `server_path`.

        The value is used verbatim when it looks like a path, and resolved against PATH otherwise.
        Note that Sublime Text launched from Finder or the Dock inherits a minimal PATH that
        usually excludes /opt/homebrew/bin, so an absolute path is the reliable choice.
        """
        expanded = os.path.expanduser(setting)
        if os.path.sep in expanded or (os.path.altsep and os.path.altsep in expanded):
            return Path(expanded)
        return Path(which(expanded) or expanded)

    @classmethod
    def installed_version(cls) -> str | None:
        try:
            return cls.version_file().read_text().strip()
        except OSError:
            return None

    @classmethod
    def needs_install(cls) -> bool:
        return not cls.managed_binary().is_file() or cls.installed_version() != SERVER_VERSION

    @classmethod
    def install(cls) -> None:
        platform_target = target()
        if platform_target is None:
            raise PluginStartError('Platform "{} ({})" is not supported by nsis-lsp'.format(
                sublime.platform(), sublime.arch()))

        destination = cls.managed_binary()
        shutil.rmtree(cls.plugin_storage_path, ignore_errors=True)
        destination.parent.mkdir(parents=True, exist_ok=True)

        url = RELEASE_URL.format(version=SERVER_VERSION, target=platform_target)
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(request) as fp:
            payload = fp.read()

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            member = next(
                (name for name in archive.namelist() if os.path.basename(name) == binary_name()),
                None,
            )
            if member is None:
                raise PluginStartError('No {} in {}'.format(binary_name(), url))
            with archive.open(member) as source, open(destination, 'wb') as sink:
                shutil.copyfileobj(source, sink)

        destination.chmod(0o700)
        cls.version_file().write_text(SERVER_VERSION)


def plugin_loaded() -> None:
    LspNsisPlugin.register()


def plugin_unloaded() -> None:
    LspNsisPlugin.unregister()
