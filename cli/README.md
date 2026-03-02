# brainlattice cli

a command-line interface to orchestrate the [brainlattice](https://github.com/rickytang/brainlattice) backend directly from your terminal.

turn dense pdfs into beautiful obsidian knowledge graphs with a single command.

> note: the heavy lifting (llm extraction, chunking, embedding) happens on the remote aws backend. you must provide your own gemini/openai api keys to use this cli.

## getting started

```bash
# install globally
npm i -g brainlattice

# configure your api keys and default obsidian vault
brainlattice config init

# generate a knowledge graph from a local pdf
brainlattice gen path/to/textbook.pdf --vault ~/obsidian/university
```

## commands

- `brainlattice config init`: interactive setup for keys and default directories
- `brainlattice gen <pdf>`: uploads pdf, processes it on aws, and downloads directly to your vault
- `brainlattice export`: interactively select and download your previously generated cloud projects

## development

```bash
npm install
npm run dev    # watch mode for local dev
npm run build  # strict build via tsup
npm link       # expose the 'brainlattice' command locally
```
