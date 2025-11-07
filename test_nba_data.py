"""
NBA Oyuncu Veri Çekme Test Scripti
Bu script nba_api kütüphanesini test eder ve oyuncu verilerini çeker
Cache, retry ve rate limiting ile optimize edilmiş
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, playergamelog, commonplayerinfo
import pandas as pd
import json
from datetime import datetime
from api_wrapper import api_call, with_retry, with_rate_limit
import time

def guncel_sezon_bul():
    """Mevcut NBA sezonunu otomatik tespit eder"""
    now = datetime.now()
    yil = now.year
    ay = now.month
    
    # NBA sezonu genellikle Ekim'de başlar, Haziran'da biter
    # Ekim-Aralık arası: 2024-25 gibi (başlangıç yılı-bitiş yılı)
    # Ocak-Eylül arası: Bir önceki sezon veya off-season
    
    if ay >= 10:  # Ekim veya sonrası
        sezon = f"{yil}-{str(yil + 1)[-2:]}"
    else:  # Ocak-Eylül
        sezon = f"{yil - 1}-{str(yil)[-2:]}"
    
    return sezon

def oyuncu_bul(isim):
    """Oyuncu adına göre oyuncu bilgilerini bulur"""
    print(f"\n🔍 '{isim}' aranıyor...")
    
    # Oyuncuyu bul
    oyuncu_listesi = players.find_players_by_full_name(isim)
    
    if not oyuncu_listesi:
        # Tam isim bulunamazsa, kısmi arama yap
        tum_oyuncular = players.get_players()
        oyuncu_listesi = [p for p in tum_oyuncular if isim.lower() in p['full_name'].lower()]
    
    if oyuncu_listesi:
        print(f"✅ {len(oyuncu_listesi)} oyuncu bulundu:")
        for oyuncu in oyuncu_listesi:
            print(f"   - {oyuncu['full_name']} (ID: {oyuncu['id']})")
        return oyuncu_listesi
    else:
        print("❌ Oyuncu bulunamadı!")
        return None

def sezon_istatistikleri_cek(oyuncu_id, sezon=None):
    """Oyuncunun sezon istatistiklerini çeker"""
    if sezon is None:
        sezon = guncel_sezon_bul()
    
    print(f"\n📊 {sezon} sezonu istatistikleri çekiliyor...")
    
    try:
        # Kariyer istatistikleri
        kariyer = playercareerstats.PlayerCareerStats(player_id=oyuncu_id)
        kariyer_df = kariyer.get_data_frames()[0]
        
        # Mevcut tüm sezonları göster
        mevcut_sezonlar = kariyer_df['SEASON_ID'].unique()
        print(f"📅 Mevcut sezonlar: {', '.join(mevcut_sezonlar[-3:])}")  # Son 3 sezon
        
        # İlgili sezonu filtrele
        sezon_df = kariyer_df[kariyer_df['SEASON_ID'] == sezon]
        
        if not sezon_df.empty:
            print(f"✅ {sezon} sezonu bulundu!")
            return sezon_df, sezon
        else:
            # En son sezonu al
            en_son_sezon = mevcut_sezonlar[-1]
            print(f"⚠️ {sezon} sezonu bulunamadı. En son sezon ({en_son_sezon}) gösteriliyor:")
            sezon_df = kariyer_df[kariyer_df['SEASON_ID'] == en_son_sezon]
            return sezon_df, en_son_sezon
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None, None

def oyuncu_detay_bilgi(oyuncu_id):
    """Oyuncunun detaylı bilgilerini çeker"""
    print(f"\n👤 Oyuncu detay bilgileri çekiliyor...")
    
    try:
        bilgi = commonplayerinfo.CommonPlayerInfo(player_id=oyuncu_id)
        bilgi_df = bilgi.get_data_frames()[0]
        
        if not bilgi_df.empty:
            print("✅ Detay bilgiler alındı!")
            return bilgi_df
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def son_maclar(oyuncu_id, sezon=None):
    """Oyuncunun sezon içindeki tüm maç performanslarını çeker"""
    if sezon is None:
        sezon = guncel_sezon_bul()
    
    print(f"\n🏀 {sezon} sezonu maç logları çekiliyor...")
    
    try:
        maclar = playergamelog.PlayerGameLog(player_id=oyuncu_id, season=sezon)
        maclar_df = maclar.get_data_frames()[0]
        
        if not maclar_df.empty:
            print(f"✅ {len(maclar_df)} maç bulundu!")
            return maclar_df
        else:
            print("⚠️ Maç bulunamadı!")
            return None
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def analiz_yap(oyuncu_isim):
    """Oyuncu için tam analiz yapar"""
    print("="*60)
    print(f"🎯 NBA OYUNCU ANALİZ SİSTEMİ")
    print("="*60)
    
    # 1. Oyuncuyu bul
    oyuncular = oyuncu_bul(oyuncu_isim)
    if not oyuncular:
        return
    
    oyuncu = oyuncular[0]  # İlk sonucu al
    oyuncu_id = oyuncu['id']
    
    print(f"\n{'='*60}")
    print(f"📋 Oyuncu: {oyuncu['full_name']}")
    print(f"{'='*60}")
    
    # 2. Detay bilgileri çek
    detay = oyuncu_detay_bilgi(oyuncu_id)
    if detay is not None and not detay.empty:
        print(f"\n🏀 Takım: {detay['TEAM_NAME'].values[0]}")
        print(f"📍 Pozisyon: {detay['POSITION'].values[0]}")
        print(f"🎂 Yaş: {detay['BIRTHDATE'].values[0]}")
        print(f"📏 Boy: {detay['HEIGHT'].values[0]}")
        print(f"⚖️ Kilo: {detay['WEIGHT'].values[0]}")
    
    # 3. Sezon istatistikleri
    sezon_stats, gercek_sezon = sezon_istatistikleri_cek(oyuncu_id)
    if sezon_stats is not None and not sezon_stats.empty:
        print(f"\n{'='*60}")
        print(f"📊 SEZON İSTATİSTİKLERİ ({gercek_sezon})")
        print(f"{'='*60}")
        
        stats = sezon_stats.iloc[0]
        mac_sayisi = stats['GP']
        
        # Ortalamaları hesapla
        pts_ort = stats['PTS'] / mac_sayisi if mac_sayisi > 0 else 0
        ast_ort = stats['AST'] / mac_sayisi if mac_sayisi > 0 else 0
        reb_ort = stats['REB'] / mac_sayisi if mac_sayisi > 0 else 0
        min_ort = stats['MIN'] / mac_sayisi if mac_sayisi > 0 else 0
        sar_toplam = pts_ort + ast_ort + reb_ort
        
        print(f"🎮 Maç Sayısı: {mac_sayisi}")
        print(f"⏱️ Dakika (Ort): {min_ort:.1f}")
        print(f"🎯 Sayı (PTS): {pts_ort:.1f}")
        print(f"🤝 Asist (AST): {ast_ort:.1f}")
        print(f"🏀 Ribaund (REB): {reb_ort:.1f}")
        print(f"📈 S+A+R Toplamı: {sar_toplam:.1f}")
        print(f"🎯 FG%: {stats['FG_PCT']*100:.1f}%")
        print(f"🎯 3P%: {stats['FG3_PCT']*100:.1f}%")
        print(f"🎯 FT%: {stats['FT_PCT']*100:.1f}%")
    
    # 4. Son maçlar
    maclar = son_maclar(oyuncu_id, sezon=gercek_sezon)
    if maclar is not None and not maclar.empty:
        print(f"\n{'='*60}")
        print(f"🏀 SON MAÇLAR (İlk 5)")
        print(f"{'='*60}")
        
        for idx, mac in maclar.head(5).iterrows():
            sar_toplam = mac['PTS'] + mac['AST'] + mac['REB']
            print(f"\n📅 {mac['GAME_DATE']} - {mac['MATCHUP']}")
            print(f"   Sayı: {mac['PTS']} | Asist: {mac['AST']} | Ribaund: {mac['REB']}")
            print(f"   S+A+R: {sar_toplam} | Dakika: {mac['MIN']}")
    
    print(f"\n{'='*60}")
    print("✅ ANALİZ TAMAMLANDI!")
    print(f"{'='*60}\n")

# Test için örnek oyuncular
if __name__ == "__main__":
    print("🚀 NBA API Test Başlıyor...\n")
    
    # Örnek oyuncular
    test_oyuncular = [
        "LeBron James",
        "Stephen Curry",
        "Luka Doncic"
    ]
    
    # İlk oyuncuyu test et
    analiz_yap(test_oyuncular[0])
    
    print("\n💡 Diğer oyuncuları test etmek için:")
    print("   analiz_yap('Oyuncu İsmi')")

