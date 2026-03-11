from flask import Flask, render_template_string, request, session, redirect, url_for
import requests
import socket
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'fima1456-game-secret-key-2026'

# Статистика
total_visits = 0
visitors = []  # Кто заходил на сайт: {'ip': '...', 'time': '...', 'user_agent': '...', 'action': '...'}
user_queries = []  # Запросы: {'id': 1, 'type': '...', 'query': '...', 'result': '...', 'full_info': {...}, 'time': '...'}

ADMIN_PASSWORD = "fima1456Game!"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def get_ip_info(ip):
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def get_site_ip(site):
    try:
        site = site.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
        ip = socket.gethostbyname(site)
        return ip
    except:
        return None

@app.before_request
def before_request():
    global total_visits, visitors
    
    # Считаем посещения главной
    if request.endpoint == 'index':
        total_visits += 1
        
        # Запоминаем посетителя
        visitor_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        visitors.append({
            'ip': visitor_ip,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_agent': user_agent,
            'action': 'ЗАШЁЛ НА САЙТ'
        })

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template_string(INDEX_HTML)

@app.route('/ipinfo', methods=['POST'])
def ipinfo():
    ip = request.form.get('ip', '').strip()
    info = get_ip_info(ip)
    
    # Сохраняем запрос
    query_id = len(user_queries) + 1
    user_queries.append({
        'id': query_id,
        'type': '🔍 Инфо по IP',
        'query': ip,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'full_info': info,
        'result': f"{info.get('city', '?')}, {info.get('country', '?')} | {info.get('org', '?')}" if info else '❌ Не найдено'
    })
    
    # Запоминаем действие посетителя
    visitors.append({
        'ip': request.remote_addr,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'action': f'ПРОВЕРИЛ IP: {ip}'
    })
    
    return render_template_string(IPINFO_HTML, ip=ip, info=info)

@app.route('/siteip', methods=['POST'])
def siteip():
    site = request.form.get('site', '').strip()
    ip = get_site_ip(site)
    
    # Сохраняем запрос
    query_id = len(user_queries) + 1
    user_queries.append({
        'id': query_id,
        'type': '🌐 IP сайта',
        'query': site,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'full_info': {'site': site, 'ip': ip} if ip else None,
        'result': f"IP: {ip}" if ip else '❌ Не найден'
    })
    
    # Запоминаем действие посетителя
    visitors.append({
        'ip': request.remote_addr,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'action': f'ПРОВЕРИЛ САЙТ: {site} → {ip if ip else "не найден"}'
    })
    
    return render_template_string(SITEIP_HTML, site=site, ip=ip)

# Админка
@app.route('/sysadminpanel', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template_string(ADMIN_LOGIN_HTML, error='❌ Неверный пароль!')
    
    return render_template_string(ADMIN_LOGIN_HTML, error=None)

@app.route('/sysadminpanel/dashboard')
@login_required
def admin_panel():
    return render_template_string(ADMIN_PANEL_HTML, 
                                 queries=user_queries[::-1],  # Последние сверху
                                 visitors=visitors[::-1],     # Последние посетители сверху
                                 total_visits=total_visits)

@app.route('/sysadminpanel/query/<int:query_id>')
@login_required
def admin_query_detail(query_id):
    # Ищем запрос по ID
    query = next((q for q in user_queries if q['id'] == query_id), None)
    if not query:
        return "Запрос не найден", 404
    
    if query['type'] == '🔍 Инфо по IP':
        return render_template_string(ADMIN_QUERY_IP_HTML, query=query)
    else:
        return render_template_string(ADMIN_QUERY_SITE_HTML, query=query)

@app.route('/sysadminpanel/visitors')
@login_required
def admin_visitors():
    return render_template_string(ADMIN_VISITORS_HTML, visitors=visitors[::-1])

@app.route('/sysadminpanel/clear')
@login_required
def admin_clear():
    user_queries.clear()
    return redirect(url_for('admin_panel'))

@app.route('/sysadminpanel/clear_visitors')
@login_required
def admin_clear_visitors():
    visitors.clear()
    return redirect(url_for('admin_visitors'))

@app.route('/sysadminpanel/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ================== HTML ШАБЛОНЫ ==================

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Местность на IP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 50px;
        }
        
        h1 {
            font-size: 4em;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(96, 165, 250, 0.3);
            letter-spacing: 2px;
        }
        
        .subtitle {
            font-size: 1.2em;
            color: #94a3b8;
            margin-top: 10px;
            letter-spacing: 1px;
        }
        
        .options {
            display: flex;
            gap: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px 30px;
            width: 350px;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-10px);
            border-color: #60a5fa;
            box-shadow: 0 20px 40px rgba(96, 165, 250, 0.2);
        }
        
        .card h2 {
            color: white;
            font-size: 2em;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .card p {
            color: #94a3b8;
            margin-bottom: 30px;
            line-height: 1.6;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            color: white;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #60a5fa;
            background: rgba(255, 255, 255, 0.15);
        }
        
        input::placeholder {
            color: #64748b;
        }
        
        button {
            width: 100%;
            padding: 15px 20px;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            border: none;
            border-radius: 50px;
            color: white;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(96, 165, 250, 0.4);
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #64748b;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 МЕСТНОСТЬ НА IP</h1>
            <div class="subtitle">Узнай, где прячется любой IP-адрес</div>
        </div>
        
        <div class="options">
            <div class="card">
                <h2>🔍 ПО IP</h2>
                <p>Введи IP-адрес и узнай где он находится, кому принадлежит и всё-всё-всё</p>
                <form action="/ipinfo" method="post">
                    <div class="form-group">
                        <input type="text" name="ip" placeholder="Например: 8.8.8.8" required>
                    </div>
                    <button type="submit">УЗНАТЬ ИНФУ</button>
                </form>
            </div>
            
            <div class="card">
                <h2>🌐 ПО САЙТУ</h2>
                <p>Введи адрес сайта и узнай его настоящий IP (без DNS-магии)</p>
                <form action="/siteip" method="post">
                    <div class="form-group">
                        <input type="text" name="site" placeholder="Например: google.com" required>
                    </div>
                    <button type="submit">УЗНАТЬ IP</button>
                </form>
            </div>
        </div>
        
        <div class="footer">
            <p>⚡ Каждый IP хранит свою историю ⚡</p>
        </div>
    </div>
</body>
</html>
"""

IPINFO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Инфо по IP | Местность на IP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .back-link {
            margin-bottom: 30px;
        }
        
        .back-link a {
            color: #60a5fa;
            text-decoration: none;
            font-size: 1.1em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        
        .back-link a:hover {
            color: #a78bfa;
            transform: translateX(-5px);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px;
        }
        
        h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .ip-address {
            color: #60a5fa;
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .info-grid {
            display: grid;
            gap: 20px;
        }
        
        .info-item {
            display: flex;
            align-items: baseline;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
        }
        
        .label {
            color: #94a3b8;
            width: 150px;
            font-size: 1.1em;
        }
        
        .value {
            color: white;
            font-size: 1.2em;
            font-weight: 500;
            flex: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="/">← На главную</a>
        </div>
        
        <div class="card">
            <h1>🔍 Информация по IP</h1>
            <div class="ip-address">{{ ip }}</div>
            
            {% if info %}
            <div class="info-grid">
                {% if info.get('ip') %}
                <div class="info-item">
                    <span class="label">IP:</span>
                    <span class="value">{{ info.ip }}</span>
                </div>
                {% endif %}
                
                {% if info.get('hostname') %}
                <div class="info-item">
                    <span class="label">Hostname:</span>
                    <span class="value">{{ info.hostname }}</span>
                </div>
                {% endif %}
                
                {% if info.get('city') %}
                <div class="info-item">
                    <span class="label">Город:</span>
                    <span class="value">{{ info.city }}</span>
                </div>
                {% endif %}
                
                {% if info.get('region') %}
                <div class="info-item">
                    <span class="label">Регион:</span>
                    <span class="value">{{ info.region }}</span>
                </div>
                {% endif %}
                
                {% if info.get('country') %}
                <div class="info-item">
                    <span class="label">Страна:</span>
                    <span class="value">{{ info.country }}</span>
                </div>
                {% endif %}
                
                {% if info.get('loc') %}
                <div class="info-item">
                    <span class="label">Координаты:</span>
                    <span class="value">{{ info.loc }}</span>
                </div>
                {% endif %}
                
                {% if info.get('org') %}
                <div class="info-item">
                    <span class="label">Провайдер:</span>
                    <span class="value">{{ info.org }}</span>
                </div>
                {% endif %}
                
                {% if info.get('postal') %}
                <div class="info-item">
                    <span class="label">Индекс:</span>
                    <span class="value">{{ info.postal }}</span>
                </div>
                {% endif %}
                
                {% if info.get('timezone') %}
                <div class="info-item">
                    <span class="label">Часовой пояс:</span>
                    <span class="value">{{ info.timezone }}</span>
                </div>
                {% endif %}
            </div>
            {% else %}
            <div style="color: #ef4444; text-align: center; padding: 40px;">
                ❌ Не удалось получить информацию по IP {{ ip }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

SITEIP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP сайта | Местность на IP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .back-link {
            margin-bottom: 30px;
        }
        
        .back-link a {
            color: #60a5fa;
            text-decoration: none;
            font-size: 1.1em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        
        .back-link a:hover {
            color: #a78bfa;
            transform: translateX(-5px);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px;
            text-align: center;
        }
        
        h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        
        .site-name {
            color: #60a5fa;
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .result {
            font-size: 2em;
            color: white;
            margin: 30px 0;
            padding: 20px;
            background: rgba(96, 165, 250, 0.1);
            border-radius: 50px;
        }
        
        .ip-value {
            font-weight: 700;
            color: #a78bfa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="/">← На главную</a>
        </div>
        
        <div class="card">
            <h1>🌐 IP адрес сайта</h1>
            <div class="site-name">{{ site }}</div>
            
            {% if ip %}
            <div class="result">
                <span class="ip-value">{{ ip }}</span>
            </div>
            {% else %}
            <div style="color: #ef4444; padding: 40px;">
                ❌ Не удалось найти IP для сайта {{ site }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в админку | Местность на IP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-box {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 50px;
            width: 400px;
            text-align: center;
        }
        
        h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            color: white;
            font-size: 1em;
        }
        
        input:focus {
            outline: none;
            border-color: #60a5fa;
        }
        
        button {
            width: 100%;
            padding: 15px 20px;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            border: none;
            border-radius: 50px;
            color: white;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
        }
        
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(96, 165, 250, 0.4);
        }
        
        .error {
            color: #ef4444;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Админка</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="post">
            <div class="form-group">
                <input type="password" name="password" placeholder="Введи пароль" required>
            </div>
            <button type="submit">ВОЙТИ</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админка | Местность на IP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        h1 {
            color: white;
            font-size: 2.5em;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stats {
            display: flex;
            gap: 20px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            min-width: 150px;
        }
        
        .stat-value {
            color: white;
            font-size: 2em;
            font-weight: 700;
        }
        
        .stat-label {
            color: #94a3b8;
            font-size: 0.9em;
        }
        
        .admin-actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 25px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(96, 165, 250, 0.4);
        }
        
        .btn-danger {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }
        
        .btn-danger:hover {
            background: #ef4444;
            color: white;
        }
        
        .btn-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
            border: 1px solid #f59e0b;
        }
        
        .btn-warning:hover {
            background: #f59e0b;
            color: white;
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .section {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 30px;
            margin-bottom: 40px;
        }
        
        .section-title {
            color: white;
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th {
            text-align: left;
            color: #94a3b8;
            font-weight: 600;
            padding: 15px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table td {
            padding: 15px 10px;
            color: white;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .table tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }
        
        .query-link {
            color: #60a5fa;
            text-decoration: none;
            font-weight: 600;
        }
        
        .query-link:hover {
            text-decoration: underline;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 50px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-ip {
            background: rgba(96, 165, 250, 0.2);
            color: #60a5fa;
        }
        
        .badge-site {
            background: rgba(167, 139, 250, 0.2);
            color: #a78bfa;
        }
        
        .user-agent {
            color: #94a3b8;
            font-size: 0.9em;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Панель управления</h1>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{{ total_visits }}</div>
                    <div class="stat-label">Всего визитов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ queries|length }}</div>
                    <div class="stat-label">Запросов</div>
                </div>
            </div>
        </div>
        
        <div class="admin-actions">
            <a href="/sysadminpanel/dashboard" class="btn btn-primary">📊 Главная админки</a>
            <a href="/sysadminpanel/visitors" class="btn btn-secondary">👥 Кто заходил</a>
            <a href="/sysadminpanel/clear" class="btn btn-warning" onclick="return confirm('Очистить все запросы?')">🗑️ Очистить запросы</a>
            <a href="/sysadminpanel/logout" class="btn btn-danger">🚪 Выйти</a>
        </div>
        
        <div class="section">
            <div class="section-title">
                <span>📋 Последние запросы</span>
            </div>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Тип</th>
                        <th>Запрос</th>
                        <th>Результат</th>
                        <th>Время</th>
                        <th>Детали</th>
                    </tr>
                </thead>
                <tbody>
                    {% for q in queries[:20] %}
                    <tr>
                        <td>#{{ q.id }}</td>
                        <td>
                            <span class="badge {% if 'IP' in q.type %}badge-ip{% else %}badge-site{% endif %}">
                                {{ q.type }}
                            </span>
                        </td>
                        <td>{{ q.query }}</td>
                        <td>{{ q.result }}</td>
                        <td>{{ q.time }}</td>
                        <td>
                            <a href="/sysadminpanel/query/{{ q.id }}" class="query-link">Подробно</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            {% if not queries %}
            <div style="color: #94a3b8; text-align: center; padding: 40px;">
                Пока нет запросов
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADMIN_VISITORS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Посетители | Админка</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        h1 {
            color: white;
            font-size: 2.5em;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .admin-actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 25px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(96, 165, 250, 0.4);
        }
        
        .btn-danger {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }
        
        .btn-danger:hover {
            background: #ef4444;
            color: white;
        }
        
        .btn-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
            border: 1px solid #f59e0b;
        }
        
        .btn-warning:hover {
            background: #f59e0b;
            color: white;
        }
        
        .section {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 30px;
        }
        
        .section-title {
            color: white;
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th {
            text-align: left;
            color: #94a3b8;
            font-weight: 600;
            padding: 15px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table td {
            padding: 15px 10px;
            color: white;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .table tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }
        
        .user-agent {
            color: #94a3b8;
            font-size: 0.9em;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .action-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 50px;
            font-size: 0.85em;
            background: rgba(96, 165, 250, 0.2);
            color: #60a5fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👥 Посетители сайта</h1>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{{ visitors|length }}</div>
                    <div class="stat-label">Всего визитов</div>
                </div>
            </div>
        </div>
        
        <div class="admin-actions">
            <a href="/sysadminpanel/dashboard" class="btn btn-primary">📊 Назад в админку</a>
            <a href="/sysadminpanel/clear_visitors" class="btn btn-warning" onclick="return confirm('Очистить историю посетителей?')">🗑️ Очистить историю</a>
            <a href="/sysadminpanel/logout" class="btn btn-danger">🚪 Выйти</a>
        </div>
        
        <div class="section">
            <div class="section-title">
                <span>📋 История посещений</span>
            </div>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>IP посетителя</th>
                        <th>Действие</th>
                        <th>Время</th>
                        <th>User Agent</th>
                    </tr>
                </thead>
                <tbody>
                    {% for v in visitors %}
                    <tr>
                        <td><strong>{{ v.ip }}</strong></td>
                        <td><span class="action-badge">{{ v.action }}</span></td>
                        <td>{{ v.time }}</td>
                        <td class="user-agent">{{ v.user_agent }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            {% if not visitors %}
            <div style="color: #94a3b8; text-align: center; padding: 40px;">
                Пока никто не заходил
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADMIN_QUERY_IP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Детали запроса | Админка</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .back-link {
            margin-bottom: 30px;
        }
        
        .back-link a {
            color: #60a5fa;
            text-decoration: none;
            font-size: 1.1em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        
        .back-link a:hover {
            color: #a78bfa;
            transform: translateX(-5px);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        h1 {
            color: white;
            font-size: 2em;
        }
        
        .badge {
            padding: 8px 15px;
            border-radius: 50px;
            font-size: 0.9em;
            font-weight: 600;
            background: rgba(96, 165, 250, 0.2);
            color: #60a5fa;
        }
        
        .info-item {
            display: flex;
            align-items: baseline;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            margin-bottom: 10px;
        }
        
        .label {
            color: #94a3b8;
            width: 150px;
            font-size: 1.1em;
        }
        
        .value {
            color: white;
            font-size: 1.2em;
            font-weight: 500;
            flex: 1;
        }
        
        .time {
            color: #94a3b8;
            font-size: 0.9em;
            margin-top: 20px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="/sysadminpanel/dashboard">← Назад в админку</a>
        </div>
        
        <div class="card">
            <div class="header">
                <h1>🔍 Запрос #{{ query.id }}</h1>
                <span class="badge">{{ query.type }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Запрос:</span>
                <span class="value">{{ query.query }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Результат:</span>
                <span class="value">{{ query.result }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Время:</span>
                <span class="value">{{ query.time }}</span>
            </div>
            
            {% if query.full_info %}
                {% if query.full_info.get('city') %}
                <div class="info-item">
                    <span class="label">Город:</span>
                    <span class="value">{{ query.full_info.city }}</span>
                </div>
                {% endif %}
                
                {% if query.full_info.get('region') %}
                <div class="info-item">
                    <span class="label">Регион:</span>
                    <span class="value">{{ query.full_info.region }}</span>
                </div>
                {% endif %}
                
                {% if query.full_info.get('country') %}
                <div class="info-item">
                    <span class="label">Страна:</span>
                    <span class="value">{{ query.full_info.country }}</span>
                </div>
                {% endif %}
                
                {% if query.full_info.get('loc') %}
                <div class="info-item">
                    <span class="label">Координаты:</span>
                    <span class="value">{{ query.full_info.loc }}</span>
                </div>
                {% endif %}
                
                {% if query.full_info.get('org') %}
                <div class="info-item">
                    <span class="label">Провайдер:</span>
                    <span class="value">{{ query.full_info.org }}</span>
                </div>
                {% endif %}
            {% endif %}
            
            <div class="time">
                ID: {{ query.id }}
            </div>
        </div>
    </div>
</body>
</html>
"""

ADMIN_QUERY_SITE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Детали запроса | Админка</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .back-link {
            margin-bottom: 30px;
        }
        
        .back-link a {
            color: #60a5fa;
            text-decoration: none;
            font-size: 1.1em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.3s;
        }
        
        .back-link a:hover {
            color: #a78bfa;
            transform: translateX(-5px);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        h1 {
            color: white;
            font-size: 2em;
        }
        
        .badge {
            padding: 8px 15px;
            border-radius: 50px;
            font-size: 0.9em;
            font-weight: 600;
            background: rgba(167, 139, 250, 0.2);
            color: #a78bfa;
        }
        
        .info-item {
            display: flex;
            align-items: baseline;
            padding: 15px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 15px;
            margin-bottom: 10px;
        }
        
        .label {
            color: #94a3b8;
            width: 150px;
            font-size: 1.1em;
        }
        
        .value {
            color: white;
            font-size: 1.2em;
            font-weight: 500;
            flex: 1;
        }
        
        .time {
            color: #94a3b8;
            font-size: 0.9em;
            margin-top: 20px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="back-link">
            <a href="/sysadminpanel/dashboard">← Назад в админку</a>
        </div>
        
        <div class="card">
            <div class="header">
                <h1>🌐 Запрос #{{ query.id }}</h1>
                <span class="badge">{{ query.type }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Сайт:</span>
                <span class="value">{{ query.query }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Результат:</span>
                <span class="value">{{ query.result }}</span>
            </div>
            
            <div class="info-item">
                <span class="label">Время:</span>
                <span class="value">{{ query.time }}</span>
            </div>
            
            <div class="time">
                ID: {{ query.id }}
            </div>
        </div>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
