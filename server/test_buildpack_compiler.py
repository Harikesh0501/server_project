import sys
import tempfile
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.buildpack import BuildpackCompiler, HostShimmer

def test_compiler():
    print("[*] Starting Universal Buildpack Compiler & Polyglot Detector Tests...")

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # 1. Next.js Test
        print("[*] 1. Testing Next.js Heuristic Detection...")
        next_dir = temp_dir / "nextjs_app"
        next_dir.mkdir()
        (next_dir / "package.json").write_text(json.dumps({
            "name": "my-next-app",
            "dependencies": {"next": "^14.2.0", "react": "^18.2.0"}
        }))
        plan = BuildpackCompiler.compile(next_dir)
        assert plan.framework == "nextjs"
        assert plan.runtime_type == "frontend"
        assert plan.port == 3000
        assert "standalone" in plan.dockerfile_content
        print("    [+] Next.js detected: multi-stage standalone buildpack generated.")

        # 2. Vite React Test
        print("[*] 2. Testing Vite / React Frontend Detection...")
        vite_dir = temp_dir / "vite_app"
        vite_dir.mkdir()
        (vite_dir / "package.json").write_text(json.dumps({
            "name": "my-vite-app",
            "devDependencies": {"vite": "^5.0.0"},
            "dependencies": {"react": "^18.2.0"}
        }))
        plan = BuildpackCompiler.compile(vite_dir)
        assert plan.framework == "react_vite"
        assert plan.runtime_type == "frontend"
        assert plan.port == 80
        assert "caddy:2-alpine" in plan.dockerfile_content
        print("    [+] React/Vite detected: static Caddy web server buildpack generated.")

        # 3. FastAPI Python Test
        print("[*] 3. Testing FastAPI Python Detection...")
        fastapi_dir = temp_dir / "fastapi_app"
        fastapi_dir.mkdir()
        (fastapi_dir / "requirements.txt").write_text("fastapi==0.110.0\nuvicorn==0.28.0\n")
        plan = BuildpackCompiler.compile(fastapi_dir)
        assert plan.framework == "fastapi"
        assert plan.runtime_type == "backend"
        assert plan.port == 8000
        assert "uvicorn" in plan.dockerfile_content
        print("    [+] FastAPI detected: Python 3.12 slim uvicorn buildpack generated.")

        # 4. Golang Test
        print("[*] 4. Testing Golang Detection...")
        go_dir = temp_dir / "go_app"
        go_dir.mkdir()
        (go_dir / "go.mod").write_text("module example.com/api\n\ngo 1.22\n")
        plan = BuildpackCompiler.compile(go_dir)
        assert plan.framework == "golang"
        assert plan.runtime_type == "backend"
        assert plan.port == 8080
        assert "CGO_ENABLED=0" in plan.dockerfile_content
        print("    [+] Golang detected: statically linked binary alpine buildpack generated.")

        # 5. Rust Test
        print("[*] 5. Testing Rust Detection...")
        rust_dir = temp_dir / "rust_app"
        rust_dir.mkdir()
        (rust_dir / "Cargo.toml").write_text('[package]\nname = "my_rust_service"\nversion = "0.1.0"\n')
        plan = BuildpackCompiler.compile(rust_dir)
        assert plan.framework == "rust"
        assert plan.runtime_type == "backend"
        assert plan.port == 8080
        assert "cargo build --release" in plan.dockerfile_content
        print("    [+] Rust detected: optimized release multi-stage buildpack generated.")

        # 6. Custom Dockerfile (Tier 3) Test
        print("[*] 6. Testing Tier 3 Custom Dockerfile & EXPOSE port parsing...")
        custom_dir = temp_dir / "custom_docker_app"
        custom_dir.mkdir()
        (custom_dir / "Dockerfile").write_text("FROM alpine:latest\nEXPOSE 9090\nCMD echo hello\n")
        plan = BuildpackCompiler.compile(custom_dir)
        assert plan.framework == "dockerfile"
        assert plan.port == 9090
        print(f"    [+] Custom Dockerfile parsed with EXPOSE port={plan.port}.")

        # 7. HostShimmer Loopback Rewriter Test
        print("[*] 7. Testing Host-Binding Automated Shimmer (Task 5.2)...")
        raw_cmd = "uvicorn main:app --host 127.0.0.1 --port 8000"
        rewritten, was_shimmered = HostShimmer.rewrite_start_command(raw_cmd)
        assert was_shimmered is True
        assert "--host 0.0.0.0" in rewritten
        assert "127.0.0.1" not in rewritten
        print(f"    [+] Shimmer rewrote '{raw_cmd}' -> '{rewritten}'")

        shimmer_env = HostShimmer.get_shimmer_env(8000)
        assert shimmer_env["HOST"] == "0.0.0.0"
        assert shimmer_env["PORT"] == "8000"
        print("    [+] Universal HOST=0.0.0.0 and PORT injected into runtime env.")

    print("\n[SUCCESS] ALL POLYGLOT DETECTOR & BUILDPACK COMPILER TESTS PASSED 100%!")

if __name__ == "__main__":
    test_compiler()
