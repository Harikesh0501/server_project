import fs from "fs";
import path from "path";
import { SourcePackager } from "./src/packager/archive";
import { QuarantineScanner } from "./src/scanner/quarantine";

async function testQuarantine() {
  const tempDir = path.join(__dirname, "test_fixtures");
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
  fs.mkdirSync(tempDir, { recursive: true });

  // Create mock files
  fs.writeFileSync(path.join(tempDir, "package.json"), '{"name":"test-app"}');
  fs.writeFileSync(path.join(tempDir, "index.ts"), 'console.log("hello");');
  fs.writeFileSync(path.join(tempDir, ".env"), "SECRET_TOKEN=dont_leak_me");
  fs.writeFileSync(path.join(tempDir, ".env.local"), "LOCAL_DEBUG=1");
  fs.writeFileSync(path.join(tempDir, "id_rsa"), "MOCK_SSH_PRIVATE_KEY");

  // Create mock node_modules
  const nmDir = path.join(tempDir, "node_modules", "mock-pkg");
  fs.mkdirSync(nmDir, { recursive: true });
  fs.writeFileSync(path.join(nmDir, "index.js"), "// node module file");

  console.log("[*] Testing QuarantineScanner.scan()...");
  const scan = QuarantineScanner.scan(tempDir);
  console.log("    Allowed files:", scan.allowedFiles);
  console.log("    Quarantined secrets:", scan.quarantinedSecrets);
  console.log("    Ignored artifacts:", scan.ignoredArtifacts);

  if (!scan.quarantinedSecrets.includes(".env")) {
    throw new Error("FAIL: .env was not quarantined!");
  }
  if (!scan.quarantinedSecrets.includes("id_rsa")) {
    throw new Error("FAIL: id_rsa was not quarantined!");
  }
  if (scan.allowedFiles.includes(".env")) {
    throw new Error("FAIL: .env leaked into allowed files!");
  }

  console.log("[*] Testing SourcePackager.packageDirectory()...");
  const outTar = path.join(__dirname, "test_output.tar.gz");
  const res = await SourcePackager.packageDirectory(tempDir, outTar);
  console.log("    Package created:", res);

  if (!fs.existsSync(outTar) || fs.statSync(outTar).size === 0) {
    throw new Error("FAIL: Archive was not created or is empty!");
  }

  // Cleanup
  fs.rmSync(tempDir, { recursive: true, force: true });
  console.log("\n[SUCCESS] CLI QUARANTINE SCANNER & PACKAGER PASSED 100%!");
}

testQuarantine().catch((err) => {
  console.error("Test failed:", err);
  process.exit(1);
});
