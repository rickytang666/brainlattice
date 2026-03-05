# brainlattice cli

a high-performance CLI to orchestrate the brainlattice extraction engine. turn dense pdfs into obsidian vaults with a single command.

> [!NOTE]
> the heavy lifting happens on the remote backend. this cli is designed for a **bring-your-own-key (byok)** workflow.

## quick start

```bash
# install globally
npm i -g brainlattice

# enter interactive shell mode (persistent session)
brainlattice

# enter your keys and default vault
config

# generate directly (one-shot mode)
gen path/to/textbook.pdf
```

## commands

| command  | description                                                                     |
| :------- | :------------------------------------------------------------------------------ |
| `login`  | authenticate your terminal via the brainlattice dashboard.                      |
| `whoami` | display current authenticated user and project usage stats.                     |
| `config` | interactive setup for API keys (Gemini, OpenRouter) and default obsidian vault. |
| `list`   | list all your remote projects in a clean table view.                            |
| `delete` | delete a project (matches by exact title).                                      |
| `info`   | display info of this project and repository link.                               |
| `gen`    | upload, extract, and download a vault directly to your obsidian folder.         |
| `export` | interactively pick and download any previously generated project.               |
| `status` | verify your local configuration and backend connectivity.                       |
| `logout` | clear local session data and disconnect from the backend.                       |
| `help`   | details of all commands                                                         |
| `exit`   | exit the interactive shell mode                                                 |

- **interactive shell mode**: running `brainlattice` with no arguments opens a persistent REPL.
- **static header**: the brand banner stays at the top of your session—no more repetitive logs.
- **resilient loop**: prompt stays open even after syntax errors or cancelled logins.
- **rich extraction summaries**: `gen` displays stats (nodes, links) after each process.
- **dual progress bars**: separate tracking for _graph extraction_ and _vault generation_.
- **resilient matching**: `export` accepts human-readable titles.
- **update notifier**: automatic 24-hour checks to ensure you're always on the latest version.
- **project info**: quick access to repo links and contribution info via `info`.

## development

fill out the .env file first:

```env
BRAINLATTICE_API_URL=
BRAINLATTICE_FRONTEND_URL=
```

```bash
npm install
npm run dev    # watch mode
npm run build  # production build via tsup
npm link       # expose 'brainlattice' command locally
```
