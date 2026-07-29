from __future__ import annotations

from LSP.plugin import AbstractPlugin
from LSP.plugin import register_plugin
from LSP.plugin import unregister_plugin
from shutil import which
from typing_extensions import override
import io
import os
import shutil
import sublime
import urllib.request
import zipfile

SERVER_VERSION = '0.4.8'
RELEASE_URL = 'https://github.com/idleberg/nsis-lsp/releases/download/v{version}/nsis-lsp-{version}-{target}.zip'
USER_AGENT = 'Sublime Text LSP'
SETTINGS_FILE = 'LSP-nsis.sublime-settings'

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


class NsisLsp(AbstractPlugin):
    @classmethod
    @override
    def name(cls) -> str:
        return 'nsis'

    @classmethod
    def basedir(cls) -> str:
        return os.path.join(cls.storage_path(), str(__package__))

    @classmethod
    def managed_binary(cls) -> str:
        return os.path.join(cls.basedir(), 'bin', binary_name())

    @classmethod
    def version_file(cls) -> str:
        return os.path.join(cls.basedir(), 'VERSION')

    @classmethod
    def server_path_setting(cls) -> str:
        value = sublime.load_settings(SETTINGS_FILE).get('server_path')
        return str(value) if isinstance(value, str) and value else 'auto'

    @classmethod
    def manages_server(cls) -> bool:
        return cls.server_path_setting() == 'auto'

    @classmethod
    def server_path(cls) -> str:
        """Resolve the binary the client should spawn.

        With the default `auto` this is the version-pinned copy in package storage. A custom
        value is used verbatim when it looks like a path, and resolved against PATH otherwise.
        Note that Sublime Text launched from Finder or the Dock inherits a minimal PATH that
        usually excludes /opt/homebrew/bin, so an absolute path is the reliable choice.
        """
        setting = cls.server_path_setting()
        if setting == 'auto':
            return cls.managed_binary()
        expanded = os.path.expanduser(setting)
        if os.path.sep in expanded or (os.path.altsep and os.path.altsep in expanded):
            return expanded
        return which(expanded) or expanded

    @classmethod
    @override
    def additional_variables(cls) -> dict[str, str] | None:
        return {'server_path': cls.server_path()}

    @classmethod
    def installed_version(cls) -> str | None:
        try:
            with open(cls.version_file(), 'r') as fp:
                return fp.read().strip()
        except OSError:
            return None

    @classmethod
    @override
    def needs_update_or_installation(cls) -> bool:
        if not cls.manages_server():
            return False
        if target() is None:
            raise ValueError('Platform "{} ({})" is not supported by nsis-lsp'.format(
                sublime.platform(), sublime.arch()))
        return not os.path.isfile(cls.managed_binary()) or cls.installed_version() != SERVER_VERSION

    @classmethod
    @override
    def install_or_update(cls) -> None:
        platform_target = target()
        if platform_target is None:
            raise ValueError('Platform "{} ({})" is not supported by nsis-lsp'.format(
                sublime.platform(), sublime.arch()))

        destination = cls.managed_binary()
        shutil.rmtree(cls.basedir(), ignore_errors=True)
        os.makedirs(os.path.dirname(destination), exist_ok=True)

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
                raise ValueError('No {} in {}'.format(binary_name(), url))
            with archive.open(member) as source, open(destination, 'wb') as sink:
                shutil.copyfileobj(source, sink)

        os.chmod(destination, 0o700)
        with open(cls.version_file(), 'w') as fp:
            fp.write(SERVER_VERSION)


def plugin_loaded() -> None:
    register_plugin(NsisLsp)


def plugin_unloaded() -> None:
    unregister_plugin(NsisLsp)
