from pathlib import Path
from dataclasses import dataclass
from app.services.buildpack.detectors import FrameworkDetectors, DetectorMatch
from app.services.buildpack.shimmer import HostShimmer

@dataclass
class BuildPlan:
    framework: str
    runtime_type: str # 'frontend' or 'backend'
    port: int
    install_command: str
    build_command: str | None
    start_command: str
    dockerfile_content: str
    shimmer_env: dict[str, str]
    was_shimmered: bool

class BuildpackCompiler:
    """
    Universal 3-Tier Polyglot Detection & Buildpack Compiler (EPIC-05).
    Inspects source repository, detects tech stack heuristics, generates optimized
    multi-stage Dockerfile, and applies loopback host-binding shimmers.
    """

    DETECTOR_PIPELINE = [
        FrameworkDetectors.check_dockerfile,     # Tier 3
        FrameworkDetectors.check_nextjs,         # Tier 1
        FrameworkDetectors.check_vite_react,     # Tier 1
        FrameworkDetectors.check_fastapi,        # Tier 1
        FrameworkDetectors.check_django,         # Tier 1
        FrameworkDetectors.check_golang,         # Tier 1
        FrameworkDetectors.check_rust,           # Tier 1
        FrameworkDetectors.check_java,           # Tier 1
        FrameworkDetectors.check_php_laravel,    # Tier 1
        FrameworkDetectors.check_dotnet          # Tier 1
    ]

    @classmethod
    def compile(cls, project_root: Path, user_overrides: dict | None = None) -> BuildPlan:
        user_overrides = user_overrides or {}
        root = Path(project_root)

        match: DetectorMatch | None = None
        for detector in cls.DETECTOR_PIPELINE:
            match = detector(root)
            if match:
                break

        # Fallback if no specific detector matched
        if not match:
            if (root / "package.json").exists():
                fallback_template = """FROM node:20-alpine AS runner
WORKDIR /app
COPY package*.json ./
RUN npm install --production || true
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""
                match = DetectorMatch(
                    framework="generic_node",
                    runtime_type="frontend",
                    default_port=3000,
                    install_command="npm install",
                    build_command=None,
                    start_command="npm start",
                    dockerfile_template=fallback_template
                )
            else:
                # Blank / Starter template fallback: Serve a clean status page using lightweight python server
                welcome_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sovereign Universal Cloud Platform</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #111827; border: 1px solid #1f2937; padding: 40px; border-radius: 16px; text-align: center; max-width: 500px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
    h1 { color: #38bdf8; margin: 0 0 12px; font-size: 26px; }
    p { color: #94a3b8; margin: 0 0 24px; font-size: 15px; line-height: 1.6; }
    .badge { display: inline-flex; align-items: center; gap: 8px; background: #064e3b; color: #34d399; padding: 6px 16px; border-radius: 9999px; font-weight: 600; font-size: 13px; letter-spacing: 0.5px; }
    .dot { width: 8px; height: 8px; background: #34d399; border-radius: 50%; box-shadow: 0 0 10px #34d399; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🚀 Sovereign Cloud Service</h1>
    <p>Your web service is live and running across private container replicas with zero-downtime routing!</p>
    <div class="badge"><span class="dot"></span> STATUS: 100% HEALTHY & ONLINE</div>
  </div>
</body>
</html>"""
                index_path = root / "index.html"
                if not index_path.exists():
                    index_path.write_text(welcome_html, encoding="utf-8")

                fallback_template = """FROM python:3.11-alpine
WORKDIR /app
COPY index.html ./
EXPOSE 3000
CMD ["python3", "-m", "http.server", "3000"]
"""
                match = DetectorMatch(
                    framework="starter_web",
                    runtime_type="frontend",
                    default_port=3000,
                    install_command="echo 'Starter app ready'",
                    build_command=None,
                    start_command="python3 -m http.server 3000",
                    dockerfile_template=fallback_template
                )

        # Apply user overrides if specified
        port = user_overrides.get("port") or match.default_port
        install_cmd = user_overrides.get("install_command") or match.install_command
        build_cmd = user_overrides.get("build_command") or match.build_command
        raw_start_cmd = user_overrides.get("start_command") or match.start_command

        # Apply Automated Shimmer to start command
        final_start_cmd, was_shimmered = HostShimmer.rewrite_start_command(raw_start_cmd)
        shimmer_env = HostShimmer.get_shimmer_env(port)

        return BuildPlan(
            framework=match.framework,
            runtime_type=match.runtime_type,
            port=port,
            install_command=install_cmd,
            build_command=build_cmd,
            start_command=final_start_cmd or raw_start_cmd,
            dockerfile_content=match.dockerfile_template,
            shimmer_env=shimmer_env,
            was_shimmered=was_shimmered
        )
