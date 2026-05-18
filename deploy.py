"""公网部署入口 — 启动Streamlit + ngrok隧道
使用方法: python deploy.py
需要: 先在 https://dashboard.ngrok.com/signup 注册免费账号获取token（可选，推荐）
"""
import os
import sys
import time
import subprocess
import signal
from pathlib import Path

BASE_DIR = Path(__file__).parent
NGROK_EXE = BASE_DIR / "ngrok.exe"


def get_auth_token():
    """获取ngrok authtoken"""
    token = os.getenv("3Dt3LkL2f98Mcv3cUtWpU9QjP91_tRhLPkHkywjjT47waXP7", "")
    if token:
        return token
    # 检查ngrok配置
    config_dir = Path.home() / "AppData" / "Local" / "ngrok"
    config_file = config_dir / "ngrok.yml"
    if config_file.exists():
        try:
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)
            return config.get("authtoken", "")
        except Exception:
            pass
    return ""


def main():
    print("=" * 60)
    print("ESG数据智能提取与分析系统 — 公网部署")
    print("=" * 60)

    # 1. 检查/配置ngrok authtoken
    token = get_auth_token()
    if not token:
        print("\n⚠️ 未检测到ngrok authtoken")
        print("  免费隧道限制: 2小时有效期，40连接/分钟")
        print("  注册免费账号可解除限制: https://dashboard.ngrok.com/signup")
        print("  注册后在 https://dashboard.ngrok.com/get-started/your-authtoken 获取token")
        print()
        choice = input("  输入token (直接回车跳过): ").strip()
        if choice:
            subprocess.run([str(NGROK_EXE), "config", "add-authtoken", choice],
                         capture_output=True)
            print("  ✅ Token已配置")
    else:
        print(f"\n✅ ngrok authtoken已配置")

    # 2. 启动Streamlit
    print("\n[1/2] 启动Streamlit应用...")
    app_path = BASE_DIR / "src" / "app" / "main.py"
    streamlit_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_path),
         "--server.headless", "true",
         "--server.port", "8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("  Streamlit已启动 (端口: 8501)")

    # 等待Streamlit就绪
    time.sleep(3)

    # 3. 启动ngrok
    print("[2/2] 启动ngrok公网隧道...")
    ngrok_proc = subprocess.Popen(
        [str(NGROK_EXE), "http", "8501", "--log", "stdout"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 等待并读取公网URL
    public_url = None
    try:
        for line in ngrok_proc.stdout:
            if "url=" in line.lower():
                import re
                match = re.search(r'url=([^\s]+)', line)
                if match:
                    public_url = match.group(1)
                    break
            # ngrok v3 also outputs the URL differently
            if "started tunnel" in line.lower() or "url" in line.lower():
                print(f"  ngrok: {line.strip()}")
    except Exception:
        pass

    # 备用：通过API获取
    if not public_url:
        time.sleep(2)
        try:
            import urllib.request, json
            resp = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels")
            data = json.loads(resp.read())
            for t in data.get("tunnels", []):
                if t.get("proto") == "https":
                    public_url = t["public_url"]
                    break
        except Exception:
            pass

    print("\n" + "=" * 60)
    if public_url:
        print(f"🌐 公网访问地址: {public_url}")
        print(f"🔗 AI智能助手: {public_url} (导航至 🤖 AI智能助手)")
    else:
        print("⚠️ 无法获取公网URL，请检查:")
        print("  1. ngrok是否正常启动")
        print("  2. 访问 http://127.0.0.1:4040 查看ngrok状态")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务\n")

    # 保持运行
    def cleanup(sig, frame):
        print("\n正在停止服务...")
        ngrok_proc.terminate()
        streamlit_proc.terminate()
        print("已停止")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        streamlit_proc.wait()
    except KeyboardInterrupt:
        cleanup(None, None)


if __name__ == "__main__":
    main()
