# get_ngrok_url.py
import json
import urllib.request
import os
import sys

def get_ngrok_public_url():
    try:
        with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
            data = json.loads(response.read().decode())
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
        return None
    except Exception as e:
        print(f"Ошибка подключения к ngrok API: {e}")
        return None

def update_env_file(url):
    env_path = '.env'
    if not os.path.exists(env_path):
        print(".env файл не найден")
        return

    with open(env_path, 'r') as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.startswith('WEBAPP_BASE_URL='):
            lines[i] = f'WEBAPP_BASE_URL={url}\n'
            updated = True
            break

    if not updated:
        lines.append(f'WEBAPP_BASE_URL={url}\n')

    with open(env_path, 'w') as f:
        f.writelines(lines)

    print(f"WEBAPP_BASE_URL обновлён на {url}")

if __name__ == "__main__":
    url = get_ngrok_public_url()
    if url:
        update_env_file(url)
        print("Готово! Перезапустите бота, чтобы изменения вступили в силу.")
    else:
        print("Не удалось получить URL от ngrok. Убедитесь, что ngrok запущен.")
        sys.exit(1)