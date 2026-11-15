"""Start temporary local servers and verify the Vite-to-FastAPI connection.

Uses free ports, no browser, and no external provider calls. Always stops its servers.
Run from the repository root using the repository's Python virtual environment.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def get(url):
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=1) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main() -> None:
    backend_port, frontend_port = free_port(), free_port()
    env = dict(os.environ, API_PROXY_TARGET=f'http://127.0.0.1:{backend_port}', GROQ_API_KEY='')
    commands = [
        ([sys.executable, '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend',
          '--port', str(backend_port)], ROOT),
        ([shutil.which('node'), 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1',
          '--port', str(frontend_port), '--strictPort'], ROOT / 'frontend'),
    ]
    processes = []
    success = False
    last_error = ''
    try:
        for command, cwd in commands:
            processes.append(subprocess.Popen(command, cwd=cwd, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))
        origin = f'http://127.0.0.1:{frontend_port}'
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if any(process.poll() is not None for process in processes):
                raise RuntimeError('A development server exited during startup')
            try:
                backend_status = get(f'http://127.0.0.1:{backend_port}/api/health')[0]
                if backend_status == 200 and get(origin + '/api/health')[0] == 200:
                    break
            except (OSError, TimeoutError) as exc:
                last_error = str(exc)
            time.sleep(0.2)
        else:
            raise RuntimeError('Local servers did not become reachable within 20 seconds: ' + last_error)
        assert get(origin)[0] == 200
        assert get(f'http://127.0.0.1:{backend_port}/docs')[0] == 200
        assert get(f'http://127.0.0.1:{backend_port}/openapi.json')[0] == 200
        request = urllib.request.Request(origin + '/api/recommendations',
            data=json.dumps({'occasion': 'Birthday', 'top_k': 3}).encode(),
            headers={'Content-Type': 'application/json'})
        status, body = get(request)
        assert status == 503 and 'GROQ_API_KEY' in body.decode(), (status, body)
        success = True
        print('PASS: React HTML, Swagger, OpenAPI, health proxy, recommendation POST proxy, missing-key error')
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                output = process.communicate(timeout=5)[0]
            except subprocess.TimeoutExpired:
                process.kill()
                output = process.communicate()[0]
            if not success:
                print(output.decode(errors='replace')[-2500:])


if __name__ == '__main__':
    main()
