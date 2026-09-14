import os
import sys
import time
import socket
import threading
import urllib.request
import uvicorn
import webview

def find_free_port(default_port=8000) -> int:
    """寻找可用端口，如果 8000 可用直接用，否则自适应分配空闲端口"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", default_port))
        sock.close()
        return default_port
    except OSError:
        sock.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        port = s.getsockname()[1]
        s.close()
        return port

def run_api_server(host: str, port: int):
    """在后台线程运行 FastAPI 后端服务"""
    from app.main import app
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def wait_for_server(url: str, timeout: float = 12.0) -> bool:
    """等待后台服务就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/v1/jobs", timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def main():
    # 确保当前工作目录正确
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    host = "127.0.0.1"
    port = find_free_port(8000)
    base_url = f"http://{host}:{port}"

    # 1. 启动后端后台守护线程
    server_thread = threading.Thread(
        target=run_api_server,
        args=(host, port),
        daemon=True,
        name="FastAPIServerThread"
    )
    server_thread.start()

    # 2. 等待后端健康就绪
    is_ready = wait_for_server(base_url, timeout=12.0)
    target_url = f"{base_url}/dashboard" if is_ready else f"{base_url}/"

    # 3. 创建 macOS 原生 WebKit 窗口
    webview.create_window(
        title="CampusJob-Agent · 求职与招考智能协同系统",
        url=target_url,
        width=1360,
        height=840,
        min_size=(1024, 660),
        text_select=True,
        confirm_close=False
    )

    # 4. 启动桌面主循环
    webview.start(debug=False)
    sys.exit(0)

if __name__ == "__main__":
    main()
