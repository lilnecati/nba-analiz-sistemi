"""
NBA 2025-26 Sezonu Güncel Veri Çekme
NBA.com'dan direkt web scraping ile güncel oyuncu istatistiklerini çeker
"""

import requests
from bs4 import BeautifulSoup
import json
import time

def nba_stats_api_cek(oyuncu_isim, sezon='2025-26'):
    """
    NBA Stats API'den direkt veri çeker (resmi API endpoint)
    """
    
    print(f"\n🔍 '{oyuncu_isim}' için {sezon} sezonu verileri çekiliyor...")
    
    # NBA Stats API endpoint'leri
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com'
    }
    
    try:
        # 1. Oyuncu arama
        print("📡 Oyuncu aranıyor...")
        search_url = "https://stats.nba.com/stats/commonallplayers"
        params = {
            'LeagueID': '00',
            'Season': sezon,
            'IsOnlyCurrentSeason': '1'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            players = data['resultSets'][0]['rowSet']
            
            # Oyuncuyu bul
            oyuncu_bulundu = None
            for player in players:
                if oyuncu_isim.lower() in player[2].lower():  # player[2] = DISPLAY_NAME
                    oyuncu_bulundu = {
                        'id': player[0],
                        'name': player[2],
                        'team': player[8] if len(player) > 8 else 'N/A'
                    }
                    break
            
            if oyuncu_bulundu:
                print(f"✅ Oyuncu bulundu: {oyuncu_bulundu['name']} (ID: {oyuncu_bulundu['id']})")
                return oyuncu_bulundu
            else:
                print(f"❌ '{oyuncu_isim}' bulunamadı!")
                return None
        else:
            print(f"❌ API Hatası: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def oyuncu_sezon_stats_cek(oyuncu_id, sezon='2025-26'):
    """Oyuncunun sezon istatistiklerini çeker"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com'
    }
    
    try:
        print(f"\n📊 {sezon} sezonu istatistikleri çekiliyor...")
        
        # Player Dashboard API
        url = "https://stats.nba.com/stats/playerdashboardbyyearoveryear"
        params = {
            'PlayerID': oyuncu_id,
            'Season': sezon,
            'SeasonType': 'Regular Season',
            'PerMode': 'PerGame'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['resultSets'] and len(data['resultSets']) > 0:
                headers_list = data['resultSets'][0]['headers']
                stats = data['resultSets'][0]['rowSet']
                
                if stats and len(stats) > 0:
                    stat_dict = dict(zip(headers_list, stats[0]))
                    print(f"✅ İstatistikler alındı!")
                    return stat_dict
        
        print(f"⚠️ {sezon} sezonu bulunamadı, alternatif yöntem deneniyor...")
        return None
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def oyuncu_game_log_cek(oyuncu_id, sezon='2025-26'):
    """Oyuncunun maç maç performansını çeker"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com'
    }
    
    try:
        print(f"\n🏀 {sezon} sezonu maç logları çekiliyor...")
        
        url = "https://stats.nba.com/stats/playergamelog"
        params = {
            'PlayerID': oyuncu_id,
            'Season': sezon,
            'SeasonType': 'Regular Season'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['resultSets'] and len(data['resultSets']) > 0:
                headers_list = data['resultSets'][0]['headers']
                games = data['resultSets'][0]['rowSet']
                
                if games:
                    print(f"✅ {len(games)} maç bulundu!")
                    
                    # Her maçı dict'e çevir
                    game_logs = []
                    for game in games:
                        game_dict = dict(zip(headers_list, game))
                        game_logs.append(game_dict)
                    
                    return game_logs
        
        print(f"⚠️ Maç logları bulunamadı!")
        return None
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def tam_analiz(oyuncu_isim, sezon='2025-26'):
    """Oyuncu için tam analiz yapar"""
    
    print(f"\n{'='*70}")
    print(f"🎯 NBA GÜNCEL VERİ ANALİZ SİSTEMİ")
    print(f"{'='*70}")
    print(f"Oyuncu: {oyuncu_isim}")
    print(f"Sezon: {sezon}")
    print(f"{'='*70}\n")
    
    # 1. Oyuncuyu bul
    oyuncu = nba_stats_api_cek(oyuncu_isim, sezon)
    if not oyuncu:
        # 2024-25 sezonunu dene
        print(f"\n⚠️ {sezon} bulunamadı, 2024-25 deneniyor...")
        oyuncu = nba_stats_api_cek(oyuncu_isim, '2024-25')
        sezon = '2024-25'
        
        if not oyuncu:
            print("❌ Oyuncu hiçbir sezonda bulunamadı!")
            return None
    
    # 2. Sezon istatistikleri
    stats = oyuncu_sezon_stats_cek(oyuncu['id'], sezon)
    
    # 3. Maç logları
    game_logs = oyuncu_game_log_cek(oyuncu['id'], sezon)
    
    # 4. Sonuçları göster
    if stats:
        print(f"\n{'='*70}")
        print(f"📊 SEZON İSTATİSTİKLERİ ({sezon})")
        print(f"{'='*70}")
        print(f"Oyuncu: {oyuncu['name']}")
        print(f"Takım: {oyuncu['team']}")
        
        if 'GP' in stats:
            print(f"\n🎮 Maç Sayısı: {stats.get('GP', 'N/A')}")
            print(f"⏱️ Dakika: {stats.get('MIN', 'N/A'):.1f}")
            print(f"🎯 Sayı: {stats.get('PTS', 'N/A'):.1f}")
            print(f"🤝 Asist: {stats.get('AST', 'N/A'):.1f}")
            print(f"🏀 Ribaund: {stats.get('REB', 'N/A'):.1f}")
            
            sar = stats.get('PTS', 0) + stats.get('AST', 0) + stats.get('REB', 0)
            print(f"📈 S+A+R: {sar:.1f}")
    
    if game_logs:
        print(f"\n{'='*70}")
        print(f"🏀 SON 5 MAÇ")
        print(f"{'='*70}")
        
        for i, game in enumerate(game_logs[:5]):
            pts = game.get('PTS', 0)
            ast = game.get('AST', 0)
            reb = game.get('REB', 0)
            sar = pts + ast + reb
            
            print(f"\n📅 Maç {i+1}: {game.get('MATCHUP', 'N/A')}")
            print(f"   Sayı: {pts} | Asist: {ast} | Ribaund: {reb} | S+A+R: {sar}")
    
    print(f"\n{'='*70}\n")
    
    return {
        'oyuncu': oyuncu,
        'stats': stats,
        'game_logs': game_logs
    }

# Test
if __name__ == "__main__":
    print("🚀 NBA GÜNCEL VERİ ÇEKME TEST\n")
    
    # 2025-26 sezonunu dene
    sonuc = tam_analiz("LeBron James", "2025-26")
    
    if sonuc:
        print("\n✅ Veri çekme başarılı!")
    else:
        print("\n❌ Veri çekme başarısız!")

