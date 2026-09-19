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
