<div align="center">

<a href="https://brainlattice.rickytang.dev"><img src="https://raw.githubusercontent.com/rickytang666/brainlattice/refs/heads/main/assets/logo.png" alt="BrainLattice Logo" width="300"></a>

</div>

# BrainLattice CLI

BrainLattice is a CLI tool that automatically turns your dense PDFs (textbooks, course notes, papers, etc.) into fully linked Obsidian vaults. Instead of spending hours manually extracting concepts and drawing boxes, you can run a single command to generate a structured knowledge graph right into your workflow.

Learn more at our [site](https://brainlattice.rickytang.dev).

## Installation

```bash
npm i -g brainlattice
```

## Quick Start

Requires API keys from [Google AI](https://aistudio.google.com/), [OpenRouter](https://openrouter.ai/settings/keys), and optionally, [OpenAI](https://openai.com/index/openai-api-platform/).

```bash
brainlattice
> config
> gen path/to/textbook.pdf
```

## Commands

| Command  | Description                                                                     |
| :------- | :------------------------------------------------------------------------------ |
| `login`  | Authenticate your terminal via the BrainLattice dashboard.                      |
| `whoami` | Display current authenticated user and project usage stats.                     |
| `config` | Interactive setup for API keys (Gemini, OpenRouter) and default Obsidian vault. |
| `list`   | List all your remote projects in a clean table view.                            |
| `delete` | Delete a project (matches by exact title).                                      |
| `info`   | Display info of this project and repository link.                               |
| `gen`    | Upload, extract, and download a vault directly to your Obsidian folder.         |
| `export` | Interactively pick and download any previously generated project.               |
| `status` | Verify your local configuration and backend connectivity.                       |
| `logout` | Clear local session data and disconnect from the backend.                       |
| `help`   | Details of all commands.                                                        |
| `exit`   | Exit the interactive shell mode.                                                |

## Features

- **BYOK (Bring Your Own Key)**: Zero SaaS lock-in. Your data, your keys, your Obsidian vault.
- **Interactive Shell Mode**: Running `brainlattice` with no arguments opens a persistent REPL.
- **Static Header**: The brand banner stays at the top of your session—no more repetitive logs.
- **Resilient Loop**: Prompt stays open even after syntax errors or cancelled logins.
- **Rich Extraction Summaries**: `gen` displays stats (nodes, links) after each process.
- **Dual Progress Bars**: Separate tracking for _graph extraction_ and _vault generation_.
- **Resilient Matching**: `export` accepts human-readable titles.
- **Update Notifier**: Automatic 24-hour checks to ensure you're always on the latest version.
- **Project Info**: Quick access to repo links and contribution info via `info`.

## Contributions and License

Please refer to [our main readme](https://github.com/rickytang666/brainlattice) for more details!
