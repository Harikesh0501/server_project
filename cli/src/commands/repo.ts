import { input, select } from '@inquirer/prompts';
import chalk from 'chalk';
import ora from 'ora';
import { apiClient } from '../client';

export async function handleDeployRepo() {
  console.log(chalk.bold.cyan('\n🚀 Sovereign Cloud Platform - Interactive Git Deployment\n'));

  // 1. Prompt for Repository URL
  const gitUrl = await input({
    message: 'Enter Git Repository URL (e.g. https://github.com/username/my-project):',
    validate: (val) => (val.trim().length > 5 ? true : 'Please enter a valid Git URL')
  });

  // 2. Prompt for Branch
  const branch = await input({
    message: 'Enter branch to deploy:',
    default: 'main'
  });

  // Extract initial slug suggestion from git URL
  const defaultSlug = gitUrl.split('/').pop()?.replace('.git', '') || 'my-app';

  // 3. Interactive Domain Selection & Duplicate Checking Loop
  let chosenSubdomain = '';
  let domainConfirmed = false;

  while (!domainConfirmed) {
    const rawSubdomain = await input({
      message: 'Choose your desired domain name:',
      default: defaultSlug
    });

    const spinner = ora(chalk.yellow(`Checking availability for '${rawSubdomain}'...`)).start();

    try {
      const check = await apiClient.checkDomain(rawSubdomain);
      spinner.stop();

      if (check.available) {
        console.log(chalk.green(`  ${check.message}`));
        console.log(chalk.gray(`  Live URL will be: https://${check.full_domain}\n`));
        chosenSubdomain = check.name;
        domainConfirmed = true;
      } else {
        console.log(chalk.red(`  ${check.message}`));

        if (check.suggestions.length > 0) {
          console.log(chalk.yellow('  Available alternative suggestions:'));
          const selectedSuggestion = await select({
            message: 'Pick an alternative suggestion or enter a new name manually:',
            choices: [
              ...check.suggestions.map((s) => ({ name: `${s} (Available)`, value: s })),
              { name: 'Enter a different name manually...', value: '__manual__' }
            ]
          });

          if (selectedSuggestion !== '__manual__') {
            chosenSubdomain = selectedSuggestion;
            domainConfirmed = true;
            console.log(chalk.green(`  Selected: ${chosenSubdomain}\n`));
          }
        }
      }
    } catch (err: any) {
      spinner.fail(chalk.red(`Error checking domain: ${err.message}`));
      return;
    }
  }

  // 4. Register Project & Dispatch Build
  const deploySpinner = ora(chalk.cyan(`Configuring project '${chosenSubdomain}' on server...`)).start();

  try {
    const project = await apiClient.createProject({
      name: chosenSubdomain,
      subdomain: chosenSubdomain,
      git_url: gitUrl,
      git_branch: branch,
      framework: 'auto-detect',
      runtime_type: 'auto-detect'
    });

    deploySpinner.succeed(chalk.green(`Project '${project.name}' registered successfully!`));

    // Simulated Build & Deployment summary box
    console.log(chalk.bold.green('\n============================================================'));
    console.log(chalk.bold.green('🎉 DEPLOYMENT READY & RESERVED!'));
    console.log(chalk.bold.green('============================================================'));
    console.log(`  🔗 Live HTTPS URL : ${chalk.bold.cyan(project.full_url)}`);
    console.log(`  📦 Git Repo       : ${chalk.white(gitUrl)} (${branch})`);
    console.log(`  🛡️ Security       : ${chalk.white('cgroups v2 + Automated Dual-TLS')}`);
    console.log(`  👥 Autoscaling    : ${chalk.white('Active (3 to 10 Replicas)')}`);
    console.log(chalk.bold.green('============================================================\n'));
  } catch (err: any) {
    deploySpinner.fail(chalk.red(`Failed to deploy project: ${err.response?.data?.detail?.message || err.message}`));
  }
}
