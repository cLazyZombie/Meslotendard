# Monatendard

**A Korean coding font that pairs Monaspace Neon with Pretendard.**

[Website & live preview](https://monatendard.github.io/) ·
[Download](https://monatendard.github.io/#download) ·
[한국어 README](README.ko.md)

Monatendard keeps the distinctive punctuation, ligatures, and character of
Monaspace Neon while adding the clear Korean texture of Pretendard. It is tuned
for mixed Korean and Latin code: every Hangul character occupies exactly two
Latin cells, with spacing that stays readable without feeling unnecessarily
wide.

<p align="center">
  <img src="assets/codex-cli-preview.png"
       alt="Monatendard Nerd Font Mono rendering aligned Korean, Latin, ligatures, and Nerd Font glyphs in Codex CLI"
       width="900">
</p>

<p align="center">
  <sub>Monatendard Nerd Font Mono in Codex CLI on Windows Terminal</sub>
</p>

## Highlights

- Monaspace Neon 1.400 Latin glyphs, horizontally tuned to 92.5%
- Pretendard 1.3.9 Korean glyphs with an exact 1:2 Latin-to-Hangul cell ratio
- Balanced Korean spacing for comfortable reading in code and comments
- 14 styles across seven weights, with matching italics
- Optional `Monatendard Nerd Font Mono` family for terminal icons
- Reproducible builds from pinned, checksum-verified upstream sources

## Download and install

Download the latest package from the
[official website](https://monatendard.github.io/#download).

For Windows:

1. Choose **Desktop** for editors and general use, or **Desktop Nerd** for
   terminals with icon-powered prompts.
2. Extract the ZIP file.
3. Run `Install-Monatendard.ps1` in PowerShell.
4. Restart the application and select `Monatendard` or
   `Monatendard Nerd Font Mono`.

The installer works per user and does not require administrator privileges.
Matching uninstall scripts are included in each package.

### VS Code

Open **Settings (JSON)** and add:

```json
{
  "editor.fontFamily": "Monatendard, Consolas, monospace",
  "editor.fontLigatures": true
}
```

Restart VS Code after installing the font.

TTF files can also be installed manually on macOS and Linux. Automated
installers for those platforms are planned for a future release.

## Build from source

Building requires Python 3.11 or later and
[uv](https://docs.astral.sh/uv/).

```powershell
uv sync --all-groups
uv run monatendard fetch
uv run monatendard build --all
uv run monatendard verify --reproducible
uv run monatendard build-nerd --all
uv run monatendard verify --nerd --reproducible
```

See the [Korean README](README.ko.md) for the complete build, packaging, and
release workflow.

## Upstream fonts and license

Monatendard is built from
[Monaspace Neon](https://github.com/githubnext/monaspace) and
[Pretendard](https://github.com/orioncactus/pretendard). The optional terminal
variant adds [Nerd Fonts Symbols Only](https://github.com/ryanoasis/nerd-fonts).

The font software is distributed under the SIL Open Font License 1.1. Nerd
Fonts symbols are distributed under the MIT License. See [LICENSE](LICENSE) and
[third-party notices](licenses/THIRD_PARTY_NOTICES.md) for details.
