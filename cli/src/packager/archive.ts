import fs from "fs";
import path from "path";
const archiver = require("archiver");
import { QuarantineScanner, QuarantineResult } from "../scanner/quarantine";

export interface PackageResult {
  archivePath: string;
  totalFiles: number;
  archiveSizeBytes: number;
  quarantined: string[];
}

export class SourcePackager {
  /**
   * Compresses source code into an ultra-clean tar.gz archive,
   * enforcing strict zero-trust pre-flight quarantine against all .env files,
   * credentials, SSH keys, and OS binary directories.
   */
  public static async packageDirectory(
    sourceDir: string,
    outputTarPath: string
  ): Promise<PackageResult> {
    const scanResult: QuarantineResult = QuarantineScanner.scan(sourceDir);
    QuarantineScanner.printQuarantineReport(scanResult);

    const outputDir = path.dirname(outputTarPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const outputStream = fs.createWriteStream(outputTarPath);
    const archive = typeof archiver === "function" 
      ? archiver("tar", { gzip: true, gzipOptions: { level: 6 } })
      : new archiver.TarArchive({ gzip: true, gzipOptions: { level: 6 } });


    return new Promise((resolve, reject) => {
      outputStream.on("close", () => {
        const stats = fs.statSync(outputTarPath);
        resolve({
          archivePath: outputTarPath,
          totalFiles: scanResult.allowedFiles.length,
          archiveSizeBytes: stats.size,
          quarantined: scanResult.quarantinedSecrets,
        });
      });

      archive.on("error", (err: unknown) => {
        reject(err);
      });

      archive.pipe(outputStream);

      // Append exclusively allowed files
      for (const relPath of scanResult.allowedFiles) {
        const absPath = path.join(sourceDir, relPath);
        archive.file(absPath, { name: relPath.replace(/\\/g, "/") });
      }

      archive.finalize();
    });
  }
}
