import json
import re
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DetectorMatch:
    framework: str
    runtime_type: str # 'frontend' or 'backend'
    default_port: int
    install_command: str
    build_command: str | None
    start_command: str
    dockerfile_template: str

class FrameworkDetectors:
    """
    Tier 1 Native Framework Heuristic Detectors and Multi-Stage Dockerfile Generators (Task 5.1).
    Generates ultra-efficient, multi-stage Linux-native Dockerfiles without requiring external cloud buildpacks.
    """

    @staticmethod
    def check_dockerfile(root: Path) -> DetectorMatch | None:
        dockerfile = root / "Dockerfile"
        if not dockerfile.exists():
            return None

        # Parse EXPOSE port if present
        port = 8080
        content = dockerfile.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^\s*EXPOSE\s+(\d+)", content, re.MULTILINE | re.IGNORECASE)
        if match:
            port = int(match.group(1))

        return DetectorMatch(
            framework="dockerfile",
            runtime_type="backend",
            default_port=port,
            install_command="",
            build_command=None,
            start_command="",
            dockerfile_template=content
        )

    @staticmethod
    def check_nextjs(root: Path) -> DetectorMatch | None:
        pkg_path = root / "package.json"
        if not pkg_path.exists():
            return None
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "next" in deps:
                template = """FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=base /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
"""
                return DetectorMatch(
                    framework="nextjs",
                    runtime_type="frontend",
                    default_port=3000,
                    install_command="npm ci",
                    build_command="npm run build",
                    start_command="node server.js",
                    dockerfile_template=template
                )
        except Exception:
            pass
        return None

    @staticmethod
    def check_vite_react(root: Path) -> DetectorMatch | None:
        pkg_path = root / "package.json"
        if not pkg_path.exists():
            return None
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            has_vite = "vite" in deps or (root / "vite.config.ts").exists() or (root / "vite.config.js").exists()
            has_react = "react" in deps or "vue" in deps or "svelte" in deps

            if has_vite or has_react:
                template = """FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2-alpine AS runner
WORKDIR /usr/share/caddy
COPY --from=builder /app/dist ./
COPY --from=builder /app/build ./
EXPOSE 80
CMD ["caddy", "file-server", "--root", "/usr/share/caddy", "--listen", ":80"]
"""
                return DetectorMatch(
                    framework="react_vite",
                    runtime_type="frontend",
                    default_port=80,
                    install_command="npm ci",
                    build_command="npm run build",
                    start_command="caddy file-server --listen :80",
                    dockerfile_template=template
                )
        except Exception:
            pass
        return None

    @staticmethod
    def check_fastapi(root: Path) -> DetectorMatch | None:
        req_path = root / "requirements.txt"
        pyproject = root / "pyproject.toml"

        is_fastapi = False
        if req_path.exists():
            content = req_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "fastapi" in content:
                is_fastapi = True
        elif pyproject.exists():
            content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
            if "fastapi" in content:
                is_fastapi = True

        if is_fastapi:
            template = """FROM python:3.12-slim AS runner
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
            return DetectorMatch(
                framework="fastapi",
                runtime_type="backend",
                default_port=8000,
                install_command="pip install -r requirements.txt",
                build_command=None,
                start_command="uvicorn main:app --host 0.0.0.0 --port 8000",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_django(root: Path) -> DetectorMatch | None:
        manage_py = root / "manage.py"
        if manage_py.exists():
            template = """FROM python:3.12-slim AS runner
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
RUN python manage.py collectstatic --noinput || true
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
"""
            return DetectorMatch(
                framework="django",
                runtime_type="backend",
                default_port=8000,
                install_command="pip install -r requirements.txt",
                build_command="python manage.py collectstatic --noinput",
                start_command="gunicorn --bind 0.0.0.0:8000 wsgi:application",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_golang(root: Path) -> DetectorMatch | None:
        go_mod = root / "go.mod"
        if go_mod.exists():
            template = """FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .

FROM alpine:3.19 AS runner
WORKDIR /app
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/server ./
EXPOSE 8080
CMD ["./server"]
"""
            return DetectorMatch(
                framework="golang",
                runtime_type="backend",
                default_port=8080,
                install_command="go mod download",
                build_command="go build -o server .",
                start_command="./server",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_rust(root: Path) -> DetectorMatch | None:
        cargo_toml = root / "Cargo.toml"
        if cargo_toml.exists():
            template = """FROM rust:1.77-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim AS runner
WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/* /app/server
EXPOSE 8080
CMD ["/app/server"]
"""
            return DetectorMatch(
                framework="rust",
                runtime_type="backend",
                default_port=8080,
                install_command="cargo fetch",
                build_command="cargo build --release",
                start_command="./server",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_java(root: Path) -> DetectorMatch | None:
        pom_xml = root / "pom.xml"
        gradle = root / "build.gradle"
        if pom_xml.exists() or gradle.exists():
            is_maven = pom_xml.exists()
            template = f"""FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY . .
RUN {"mvn clean package -DskipTests" if is_maven else "./gradlew build -x test"}

FROM eclipse-temurin:21-jre-alpine AS runner
WORKDIR /app
COPY --from=builder /app/target/*.jar /app/app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
"""
            return DetectorMatch(
                framework="java_spring",
                runtime_type="backend",
                default_port=8080,
                install_command="mvn dependency:go-offline" if is_maven else "./gradlew dependencies",
                build_command="mvn package" if is_maven else "./gradlew build",
                start_command="java -jar app.jar",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_php_laravel(root: Path) -> DetectorMatch | None:
        composer = root / "composer.json"
        artisan = root / "artisan"
        if composer.exists():
            template = """FROM php:8.3-cli-alpine AS runner
WORKDIR /var/www/html
RUN apk add --no-cache curl git libpng-dev libzip-dev
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
COPY . .
RUN composer install --no-dev --optimize-autoloader
EXPOSE 8000
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]
"""
            return DetectorMatch(
                framework="laravel",
                runtime_type="backend",
                default_port=8000,
                install_command="composer install",
                build_command=None,
                start_command="php artisan serve --host=0.0.0.0 --port=8000",
                dockerfile_template=template
            )
        return None

    @staticmethod
    def check_dotnet(root: Path) -> DetectorMatch | None:
        csproj = list(root.glob("*.csproj"))
        if csproj:
            template = """FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder
WORKDIR /app
COPY . .
RUN dotnet publish -c Release -o /app/out

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runner
WORKDIR /app
COPY --from=builder /app/out ./
ENV ASPNETCORE_URLS=http://+:5000
EXPOSE 5000
CMD ["dotnet", "run"]
"""
            return DetectorMatch(
                framework="dotnet",
                runtime_type="backend",
                default_port=5000,
                install_command="dotnet restore",
                build_command="dotnet publish -c Release",
                start_command="dotnet run",
                dockerfile_template=template
            )
        return None
