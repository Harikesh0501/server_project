import fs from "fs";
import path from "path";
import chalk from "chalk";

export interface QuarantineResult {
  allowedFiles: string[];
  quarantinedSecrets: string[];
  ignoredArtifacts: string[];
}

export class QuarantineScanner {
  /**
   * High-security secrets and keys patterns that must NEVER leave developer's machine
   * into any tarball or container image layer.
   */
  private static readonly SECRET_PATTERNS = [
    /^\.env(?:\..*)?$/i,                // .env, .env.local, .env.production, etc.
    /\.env$/i,                          // *.env
    /^id_rsa(?:|\.pub)$/i,              // SSH RSA keys
    /^id_ed25519(?:|\.pub)$/i,          // SSH ED25519 keys
    /\.(?:pem|key|pfx|pkcs12)$/i,       // Certificates & private keys
    /^credentials\.json$/i,             // Google / Cloud service account
    /^service-account(?:.*)\.json$/i,   // Service accounts
  ];

  /**
   * Build artifacts, OS-specific binaries, and heavy directories that must be built
   * cleanly inside Linux-native container environments.
   */
  private static readonly IGNORE_PATTERNS = [
    /^\.git$/i,
    /^\.github$/i,
    /^\.gitlab$/i,
    /^node_modules$/i,
    /^\.venv$/i,
    /^venv$/i,
    /^__pycache__$/i,
    /^\.next$/i,
    /^\.nuxt$/i,
    /^dist$/i,
    /^build$/i,
    /^\.DS_Store$/i,
    /^Thumbs\.db$/i,
  ];

  public static isSecret(filename: string): boolean {
    return this.SECRET_PATTERNS.some((pattern) => pattern.test(filename));
  }

  public static isIgnored(filename: string): boolean {
    return this.IGNORE_PATTERNS.some((pattern) => pattern.test(filename));
  }

  /**
   * Recursively scans directory and separates allowed source files from quarantined secrets
   * and ignored binary directories.
   */
  public static scan(rootDir: string): QuarantineResult {
    const allowedFiles: string[] = [];
    const quarantinedSecrets: string[] = [];
    const ignoredArtifacts: string[] = [];

    function walk(currentDir: string) {
      const entries = fs.readdirSync(currentDir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(currentDir, entry.name);
        const relativePath = path.relative(rootDir, fullPath);

        if (QuarantineScanner.isSecret(entry.name)) {
          quarantinedSecrets.push(relativePath);
          continue;
        }

        if (QuarantineScanner.isIgnored(entry.name)) {
          ignoredArtifacts.push(relativePath);
          continue;
        }

        if (entry.isDirectory()) {
          walk(fullPath);
        } else if (entry.isFile()) {
          allowedFiles.push(relativePath);
        }
      }
    }

    walk(rootDir);

    return {
      allowedFiles,
      quarantinedSecrets,
      ignoredArtifacts,
    };
  }

  /**
   * Prints bold terminal security summary to ensure full developer transparency.
   */
  public static printQuarantineReport(result: QuarantineResult): void {
    if (result.quarantinedSecrets.length > 0) {
      console.log(
        chalk.yellow.bold(
          "\n[!] ZERO-TRUST QUARANTINE: The following sensitive files are QUARANTINED and will NOT be uploaded:"
        )
      );
      for (const secret of result.quarantinedSecrets) {
        console.log(chalk.red(`    ✖ [QUARANTINED] ${secret}`));
      }
      console.log(
        chalk.cyan(
          "    ℹ Tip: Use 'deploy env set KEY=VALUE' or 'deploy env push' to securely inject environment variables.\n"
        )
      );
    }
  }
}
