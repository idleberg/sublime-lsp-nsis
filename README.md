# LSP-nsis

![License](https://img.shields.io/github/license/idleberg/sublime-lsp-nsis?style=for-the-badge)
[![Release](https://img.shields.io/github/v/release/idleberg/sublime-lsp-nsis?style=for-the-badge)](https://github.com/idleberg/sublime-lsp-nsis/releases)
[![Package Control Downloads](https://img.shields.io/packagecontrol/dt/LSP-nsis?style=for-the-badge)](https://packages.sublimetext.com/packages/LSP-nsis)

NSIS support for Sublime Text, via [nsis-lsp](https://github.com/idleberg/nsis-lsp) and the
[LSP](https://packagecontrol.io/packages/LSP) package.

## Features

Code actions, completions, compiler diagnostics, document formatting, document symbols, go-to-definition,
find references, hover documentation, rename symbol, and signature help.

Diagnostics require the `makensis` compiler. Without it the server still starts, and everything else works.

## Installation

1. Install [LSP](https://packagecontrol.io/packages/LSP) and [NSIS](https://packagecontrol.io/packages/NSIS)
   — the latter provides the `source.nsis` syntax this package binds to.
2. Install `LSP-nsis`.

The language server is downloaded automatically on first use and kept in sync with the version pinned in
`plugin.py`. To use your own build instead, set an absolute path:

```jsonc
// Preferences: LSP-nsis Settings
{
  "server_path": "/usr/local/bin/nsis-lsp",
}
```

An absolute path matters here: Sublime Text launched from Finder or the Dock inherits a minimal `PATH` that
generally excludes `/usr/local/bin`, so a bare `nsis-lsp` may resolve when you launch from a shell and
fail when you launch from the Dock.

## Configuration

Open the settings via `Preferences → Package Settings → LSP → Servers → LSP-nsis`, or from the command
palette with `Preferences: LSP-nsis Settings`. Per-project overrides go under `settings.LSP.LSP-nsis` in
a `.sublime-project` file.

| Setting                       | Default | Description                                                         |
| ----------------------------- | ------- | ------------------------------------------------------------------- |
| `diagnostics.preprocess_mode` | `"ppo"` | Preprocessor mode for `makensis`: `"ppo"`, `"safe_ppo"`, or `null`. |
| `diagnostics.enabled_on_save` | `true`  | Refresh diagnostics on save.                                        |
| `formatter.end_of_line`       | `null`  | `"lf"`, `"crlf"`, or `null` to keep the document's own.             |
| `formatter.print_width`       | `0`     | Wrap column; `0` disables wrapping.                                 |
| `formatter.trim_empty_lines`  | `true`  | Strip trailing whitespace from empty lines.                         |
| `formatter.single_quote`      | `false` | Prefer single over double quotes.                                   |
| `formatter.comment_style`     | `null`  | `"hash"`, `"semi"`, or `null` to preserve comment markers.          |
| `makensis.path`               | `""`    | Path to `makensis`; empty looks it up on `PATH`.                    |

These are passed as `initializationOptions`, so changes take effect after restarting the server
(`LSP: Restart Servers`).

## License

[The MIT License](LICENSE) - Feel free to use, modify, and distribute this code.
