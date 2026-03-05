import { Command } from "commander";
import chalk from "chalk";
import ora from "ora";
import { getConfig } from "../utils/config.js";
import { createApiClient } from "../utils/client.js";

export const statusCommand = new Command("status")
  .description(
    "check the status of your configuration and connection to the backend",
  )
  .action(async () => {
    const config = getConfig();
    const api = createApiClient();

    // check local config
    console.log(chalk.bold("local configuration:"));
    console.log(`- user_id: ${chalk.cyan(config.user_id || "not set")}`);
    console.log(
      `- session: ${config.session_token ? chalk.green("logged in") : chalk.yellow("anonymous")}`,
    );
    console.log(
      `- gemini_key: ${config.gemini_key ? chalk.green("configured") : chalk.red("missing")}`,
    );
    console.log(
      `- openrouter_key: ${config.openrouter_key ? chalk.green("configured") : chalk.red("missing")}`,
    );
    console.log(
      `- openai_key: ${config.openai_key ? chalk.green("configured") : chalk.gray("optional")}`,
    );
    console.log(
      `- default_vault: ${chalk.cyan(config.default_vault || "not set")}`,
    );
    console.log("");

    // check backend connection
    const spinner = ora("connecting to brainlattice backend...").start();
    try {
      const start = Date.now();
      const res = await api.get("projects/list");
      const latency = Date.now() - start;

      spinner.succeed(`connected to backend (${latency}ms)`);
      console.log(
        chalk.gray(
          `\nyou have ${chalk.white(res.data.length)} remote projects available.`,
        ),
      );

      if (!config.gemini_key || !config.openrouter_key) {
        console.log(
          chalk.yellow(
            "\nwarning: gemini_key or openrouter_key is missing. `gen` will fail until you add them.",
          ),
        );
      } else {
        console.log(
          chalk.green(
            "\n✔ your cli is fully configured and ready to generate!",
          ),
        );
      }
    } catch (error: any) {
      spinner.fail("could not connect to backend.");
    }
    console.log("");
  });
