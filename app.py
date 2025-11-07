"""
NBA Analiz Sistemi - Flask Backend
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, make_response
from flask_cors import CORS
from baraj_analiz import BarajAnaliz
from takim_analiz_v2 import mac_tahmini_v2
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nba_analiz_secret_key_2025'  # Güvenli bir key kullan
CORS(app)

# Basit kullanıcı veritabanı (gerçek uygulamada SQLite/PostgreSQL kullan)
USERS = {
    'admin': 'admin123',
}

# Kullanıcı giriş kontrolü
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
def index():
    """Ana sayfa - giriş kontrolü"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return jsonify({'success': True, 'message': 'Giriş başarılı!'})
        else:
            return jsonify({'success': False, 'message': 'Kullanıcı adı veya şifre hatalı!'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Çıkış"""
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Ana dashboard"""
    response = make_response(render_template('dashboard.html', username=session['username']))
    # Cache'i engelle
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/takimlar.json')
def takimlar_json():
    """Takım listesi JSON endpoint"""
    return send_from_directory('.', 'takimlar.json')

@app.route('/api/oyuncu-analiz', methods=['POST'])
@login_required
def oyuncu_analiz():
    """Oyuncu analizi API endpoint"""
    try:
        data = request.get_json()
        oyuncu_isim = data.get('oyuncu_isim')
        baraj = int(data.get('baraj', 40))
        analiz_tipi = data.get('analiz_tipi', 'SAR')
        ev_deplasman = data.get('ev_deplasman', 'Bilinmiyor')
        ev_orani = data.get('ev_orani')
        dep_orani = data.get('dep_orani')
        
        # Oranları float'a çevir
        try:
            ev_orani = float(ev_orani) if ev_orani else None
            dep_orani = float(dep_orani) if dep_orani else None
        except:
            ev_orani = None
            dep_orani = None
        
        # Oyuncunun takımına göre doğru oranı seç
        mac_orani = None
        if ev_orani and dep_orani and ev_deplasman != 'Bilinmiyor':
            if ev_deplasman == 'Ev':
                mac_orani = ev_orani  # Oyuncu ev sahibi → ev oranını kullan
            elif ev_deplasman == 'Deplasman':
                mac_orani = dep_orani  # Oyuncu deplasman → deplasman oranını kullan
        
        # Analiz yap
        analiz = BarajAnaliz(oyuncu_isim, baraj, analiz_tipi, ev_deplasman, mac_orani)
        sonuc = analiz.analiz_yap()
        
        if sonuc:
            return jsonify({
                'success': True,
                'data': sonuc
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Oyuncu bulunamadı veya veri çekilemedi!'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

@app.route('/api/mac-analiz', methods=['POST'])
@login_required
def mac_analiz():
    """Maç analizi API endpoint"""
    try:
        data = request.get_json()
        ev_takim = data.get('ev_takim')
        dep_takim = data.get('dep_takim')
        baraj = data.get('baraj')
        
        # Debug: Gelen verileri logla
        print(f"🔍 DEBUG - Gelen veriler:")
        print(f"  Ev Takım: '{ev_takim}'")
        print(f"  Deplasman: '{dep_takim}'")
        print(f"  Baraj: '{baraj}'")
        
        # Boş değer kontrolü
        if not ev_takim or not dep_takim:
            return jsonify({
                'success': False,
                'message': 'Takım isimleri boş olamaz!'
            })
        
        # Baraj varsa float'a çevir
        if baraj:
            baraj = float(baraj)
        
        # Analiz yap (Regresyonlu V2 algoritması)
        print(f"🔄 Analiz başlatılıyor...")
        sonuc = mac_tahmini_v2(ev_takim, dep_takim, baraj=baraj, sezon='2024-25', verbose=False)
        
        if sonuc:
            print(f"✅ Analiz başarılı!")
            return jsonify({
                'success': True,
                'data': sonuc
            })
        else:
            print(f"❌ Analiz başarısız - sonuc None")
            return jsonify({
                'success': False,
                'message': 'Takımlar bulunamadı veya veri çekilemedi!'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        })

if __name__ == '__main__':
    # Templates klasörünü oluştur
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Production için port ayarı
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    if debug:
        print("\n" + "="*70)
        print("🏀 NBA ANALİZ SİSTEMİ BAŞLATILIYOR")
        print("="*70)
        print("📍 Desktop URL: http://127.0.0.1:3000")
        print("📱 Mobil URL: http://192.168.1.43:3000")
        print("👤 Demo Kullanıcı: demo / demo123")
        print("👤 Admin: admin / admin123")
        print("="*70 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)

