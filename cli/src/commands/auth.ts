import chalk from 'chalk';
import ora from 'ora';
import { input, password, select } from '@inquirer/prompts';
import { apiClient } from '../client';

export async function handleLogin() {
  console.log(chalk.bold.cyan('\n🔐 Sovereign Cloud Platform Authentication\n'));

  const method = await select({
    message: 'Select login method:',
    choices: [
      { name: '👤 Local Credentials (Email/Username & Password)', value: 'local' },
      { name: '🌐 Browser Login (RFC 8628 Device Flow - GitHub/Google/Web)', value: 'device' }
    ]
  });

  if (method === 'local') {
    const emailOrUser = await input({
      message: 'Enter Email or Username:',
      validate: (v) => (v.trim().length > 0 ? true : 'Please enter your username or email')
    });

    const pass = await password({
      message: 'Enter Password:',
      mask: '*'
    });

    const spinner = ora('Authenticating with sovereign cloud server...').start();
    try {
      const res = await apiClient.login({
        email_or_username: emailOrUser,
        password: pass
      });
      spinner.succeed(chalk.green('Authentication successful!'));

      const user = res.user;
      console.log(chalk.bold.green(`\n✔ Logged in as: ${user.username} (${user.email})`));
      console.log(`  Role    : ${chalk.cyan(user.role)}`);
      console.log(`  Provider: ${chalk.gray(user.oauth_provider)}`);
      console.log(chalk.gray('\nYour token has been securely saved to ~/.deployrc\n'));
    } catch (err: any) {
      spinner.fail(chalk.red('Login failed!'));
      const msg = err.response?.data?.detail || err.message;
      console.log(chalk.red(`Error: ${msg}\n`));
    }
  } else {
    // Device code flow (RFC 8628)
    const spinner = ora('Initiating device authorization session...').start();
    try {
      const data = await apiClient.requestDeviceCode();
      spinner.succeed(chalk.green('Device authorization initiated!'));

      console.log('\n-----------------------------------------------------------');
      console.log(chalk.bold.yellow(`👉 Open URL in your browser : ${chalk.underline.cyan(data.verification_uri)}`));
      console.log(chalk.bold.white(`🔑 Enter One-Time Code      : `) + chalk.bold.bgCyan.black(` ${data.user_code} `));
      console.log('-----------------------------------------------------------\n');

      const pollSpinner = ora('Waiting for authorization in browser...').start();

      const startTime = Date.now();
      const timeoutMs = data.expires_in * 1000;

      while (Date.now() - startTime < timeoutMs) {
        await new Promise((r) => setTimeout(r, data.interval * 1000));
        try {
          const pollRes = await apiClient.pollDeviceToken(data.device_code);
          if (pollRes.access_token) {
            pollSpinner.succeed(chalk.green('Authorization confirmed!'));
            const user = pollRes.user;
            console.log(chalk.bold.green(`\n✔ Logged in as: ${user.username} (${user.email})`));
            console.log(`  Role    : ${chalk.cyan(user.role)}`);
            console.log(chalk.gray('\nYour session has been securely saved to ~/.deployrc\n'));
            return;
          }
        } catch (pollErr: any) {
          const detail = pollErr.response?.data?.detail;
          if (detail === 'expired_token' || detail === 'access_denied') {
            pollSpinner.fail(chalk.red(`Authorization ${detail}`));
            return;
          }
        }
      }

      pollSpinner.fail(chalk.red('Device authorization timed out. Please try again.'));
    } catch (err: any) {
      spinner.fail(chalk.red('Failed to request device authorization code'));
      console.log(chalk.red(err.message));
    }
  }
}

export async function handleRegister() {
  console.log(chalk.bold.cyan('\n📝 Register New Sovereign Cloud Account\n'));

  const email = await input({
    message: 'Enter Email Address:',
    validate: (v) => (v.includes('@') ? true : 'Please enter a valid email address')
  });

  const username = await input({
    message: 'Enter Username:',
    validate: (v) => (v.trim().length >= 3 ? true : 'Username must be at least 3 characters')
  });

  const fullName = await input({
    message: 'Enter Full Name (optional):'
  });

  const pass = await password({
    message: 'Enter Secure Password (min 6 characters):',
    mask: '*',
    validate: (v) => (v.length >= 6 ? true : 'Password must be at least 6 characters')
  });

  const spinner = ora('Registering account on server...').start();
  try {
    const res = await apiClient.register({
      email,
      username,
      password: pass,
      full_name: fullName.trim() || undefined
    });
    spinner.succeed(chalk.green('Account created successfully!'));

    const user = res.user;
    console.log(chalk.bold.green(`\n✔ Welcome, ${user.username}! Your account is active.`));
    console.log(`  Role: ${chalk.cyan(user.role)}`);
    console.log(chalk.gray('Your session token has been automatically configured in ~/.deployrc\n'));
  } catch (err: any) {
    spinner.fail(chalk.red('Registration failed!'));
    const msg = err.response?.data?.detail || err.message;
    console.log(chalk.red(`Error: ${msg}\n`));
  }
}

export async function handleWhoami() {
  const spinner = ora('Fetching authenticated profile...').start();
  try {
    const user = await apiClient.getMe();
    spinner.stop();

    console.log(chalk.bold.cyan('\n👤 Authenticated User Profile:\n'));
    console.log(`  ID       : ${chalk.white(user.id)}`);
    console.log(`  Username : ${chalk.bold.green(user.username)}`);
    console.log(`  Email    : ${chalk.white(user.email)}`);
    console.log(`  Full Name: ${chalk.white(user.full_name || 'N/A')}`);
    console.log(`  Role     : ${chalk.cyan(user.role)} ${user.is_superuser ? chalk.yellow('(Superuser)') : ''}`);
    console.log(`  Provider : ${chalk.gray(user.oauth_provider)}`);
    console.log(`  Status   : ${user.is_active ? chalk.green('Active') : chalk.red('Inactive')}\n`);
  } catch (err: any) {
    spinner.fail(chalk.yellow('Not currently logged in.'));
    console.log(chalk.gray('Log in with: deploy login\n'));
  }
}

export async function handleLogout() {
  const spinner = ora('Revoking session on sovereign server...').start();
  await apiClient.logout();
  spinner.succeed(chalk.green('Successfully logged out.'));
  console.log(chalk.gray('Local credentials cleared from ~/.deployrc\n'));
}
