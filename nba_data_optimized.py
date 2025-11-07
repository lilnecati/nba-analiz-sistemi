"""
Optimize Edilmiş NBA Veri Çekme Modülü
Cache, Retry ve Rate Limiting ile güçlendirilmiş
"""

from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, playergamelog, commonplayerinfo
import pandas as pd
from datetime import datetime
from api_wrapper import api_call
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Hızlı HTTP session oluştur
def create_fast_session():
    """Hızlı HTTP session oluşturur"""
    session = requests.Session()
    
    # Retry stratejisi
    retry_strategy = Retry(
        total=2,  # Maksimum 2 deneme
        backoff_factor=0.3,  # Hızlı backoff
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Timeout ayarları
    session.timeout = (5, 15)  # (connect, read) timeout
    
    return session

# Global fast session
fast_session = create_fast_session()

def guncel_sezon_bul():
    """Mevcut NBA sezonunu otomatik tespit eder"""
    now = datetime.now()
    yil = now.year
    ay = now.month
    
    # NBA sezonu Ekim'de başlar
    if ay >= 10:
        return f"{yil}-{str(yil+1)[2:]}"
    else:
        return f"{yil-1}-{str(yil)[2:]}"

def oyuncu_bul(isim):
    """Oyuncu adına göre arama yapar (Cache'li)"""
    print(f"\n🔍 '{isim}' aranıyor...")
    
    tum_oyuncular = players.get_players()
    bulunan = [p for p in tum_oyuncular if isim.lower() in p['full_name'].lower()]
    
    if bulunan:
        print(f"✅ {len(bulunan)} oyuncu bulundu!")
        for oyuncu in bulunan[:5]:
            print(f"   - {oyuncu['full_name']}")
        return bulunan
    else:
        print("❌ Oyuncu bulunamadı!")
        return None

def hizli_api_cagri(func, *args, **kwargs):
    """Ultra hızlı API çağrısı - 15 saniye timeout"""
    try:
        print(f"⚡ Hızlı API çağrısı başlatılıyor...")
        
        # NBA API endpoint'ini direkt çağır
        result = func(*args, **kwargs)
        
        if hasattr(result, 'get_data_frames'):
            df_list = result.get_data_frames()
            if df_list and len(df_list) > 0:
                return df_list[0]
        
        return None
        
    except Exception as e:
        print(f"⚠️ API hatası: {str(e)[:100]}...")
        return None

@api_call(
    cache_key_func=lambda oyuncu_id, sezon=None: f"season_stats_{oyuncu_id}_{sezon or 'current'}",
    max_retries=1,  # Tek deneme
    cache_duration_hours=24  # Uzun cache
)
def sezon_istatistikleri_cek_optimized(oyuncu_id, sezon=None):
    """
    Oyuncunun sezon istatistiklerini çeker
    ✅ Cache: 6 saat
    ✅ Retry: 3 deneme
    ✅ Rate Limit: 0.6 saniye
    """
    if sezon is None:
        sezon = guncel_sezon_bul()
    
    print(f"\n📊 {sezon} sezonu istatistikleri çekiliyor...")
    
    # API çağrısı
    kariyer = playercareerstats.PlayerCareerStats(player_id=oyuncu_id)
    kariyer_df = kariyer.get_data_frames()[0]
    
    # Mevcut sezonları göster
    mevcut_sezonlar = kariyer_df['SEASON_ID'].unique()
    print(f"📅 Mevcut sezonlar: {', '.join(mevcut_sezonlar[-3:])}")
    
    # İlgili sezonu filtrele
    sezon_df = kariyer_df[kariyer_df['SEASON_ID'] == sezon]
    
    if not sezon_df.empty:
        print(f"✅ {sezon} sezonu bulundu!")
        # DataFrame'i dict'e çevir (JSON serializable for cache)
        return {
            'data': sezon_df.to_dict('records'),
            'sezon': sezon,
            'timestamp': datetime.now().isoformat()
        }
    else:
        # En son sezonu al
        en_son_sezon = mevcut_sezonlar[-1]
        print(f"⚠️ {sezon} sezonu bulunamadı. En son sezon ({en_son_sezon}) gösteriliyor")
        sezon_df = kariyer_df[kariyer_df['SEASON_ID'] == en_son_sezon]
        return {
            'data': sezon_df.to_dict('records'),
            'sezon': en_son_sezon,
            'timestamp': datetime.now().isoformat()
        }

@api_call(
    cache_key_func=lambda oyuncu_id, sezon=None: f"game_log_{oyuncu_id}_{sezon or 'current'}",
    max_retries=3,
    cache_duration_hours=3  # Maç logları daha sık güncellenir
)
def son_maclar_optimized(oyuncu_id, sezon=None):
    """
    Oyuncunun sezon içindeki tüm maç performanslarını çeker
    ✅ Cache: 3 saat (daha sık güncellenir)
    ✅ Retry: 3 deneme
    ✅ Rate Limit: 0.6 saniye
    """
    if sezon is None:
        sezon = guncel_sezon_bul()
    
    print(f"\n🏀 {sezon} sezonu maç logları çekiliyor...")
    
    maclar = playergamelog.PlayerGameLog(player_id=oyuncu_id, season=sezon)
    maclar_df = maclar.get_data_frames()[0]
    
    if not maclar_df.empty:
        print(f"✅ {len(maclar_df)} maç bulundu!")
        return {
            'data': maclar_df.to_dict('records'),
            'sezon': sezon,
            'total_games': len(maclar_df),
            'timestamp': datetime.now().isoformat()
        }
    else:
        print("⚠️ Maç bulunamadı!")
        return None

@api_call(
    cache_key_func=lambda oyuncu_id: f"player_info_{oyuncu_id}",
    max_retries=3,
    cache_duration_hours=24  # Oyuncu bilgileri nadiren değişir
)
def oyuncu_detay_bilgi_optimized(oyuncu_id):
    """
    Oyuncunun detaylı bilgilerini çeker
    ✅ Cache: 24 saat (oyuncu bilgileri nadiren değişir)
    ✅ Retry: 3 deneme
    ✅ Rate Limit: 0.6 saniye
    """
    print(f"\n👤 Oyuncu detay bilgileri çekiliyor...")
    
    detay = commonplayerinfo.CommonPlayerInfo(player_id=oyuncu_id)
    detay_df = detay.get_data_frames()[0]
    
    if not detay_df.empty:
        print(f"✅ Detay bilgiler bulundu!")
        return {
            'data': detay_df.to_dict('records'),
            'timestamp': datetime.now().isoformat()
        }
    else:
        print("⚠️ Detay bilgiler bulunamadı!")
        return None


# Wrapper fonksiyonlar (eski API ile uyumluluk için)
def sezon_istatistikleri_cek(oyuncu_id, sezon=None):
    """Eski API ile uyumlu wrapper"""
    try:
        result = sezon_istatistikleri_cek_optimized(oyuncu_id, sezon)
        if result and isinstance(result, dict) and 'data' in result:
            df = pd.DataFrame(result['data'])
            return df, result['sezon']
        return None, None
    except Exception as e:
        print(f"⚠️ Sezon istatistikleri hatası: {e}")
        return None, None

def son_maclar(oyuncu_id, sezon=None):
    """Eski API ile uyumlu wrapper"""
    try:
        result = son_maclar_optimized(oyuncu_id, sezon)
        if result and isinstance(result, dict) and 'data' in result:
            df = pd.DataFrame(result['data'])
            return df
        return None
    except Exception as e:
        print(f"⚠️ Maç logları hatası: {e}")
        return None

def oyuncu_detay_bilgi(oyuncu_id):
    """Eski API ile uyumlu wrapper"""
    try:
        result = oyuncu_detay_bilgi_optimized(oyuncu_id)
        if result and isinstance(result, dict) and 'data' in result:
            df = pd.DataFrame(result['data'])
            return df
        return None
    except Exception as e:
        print(f"⚠️ Oyuncu detay bilgisi hatası: {e}")
        return None


if __name__ == "__main__":
    print("="*70)
    print("🚀 OPTİMİZE EDİLMİŞ NBA VERİ SİSTEMİ TEST")
    print("="*70)
    
    # Test: LeBron James
    print("\n📊 Test: LeBron James")
    oyuncular = oyuncu_bul("LeBron James")
    
    if oyuncular:
        oyuncu = oyuncular[0]
        oyuncu_id = oyuncu['id']
        
        print("\n1️⃣ İlk çağrı (API'den):")
        start = time.time()
        stats, sezon = sezon_istatistikleri_cek(oyuncu_id)
        print(f"⏱️ Süre: {time.time() - start:.2f} saniye")
        
        print("\n2️⃣ İkinci çağrı (Cache'den):")
        start = time.time()
        stats, sezon = sezon_istatistikleri_cek(oyuncu_id)
        print(f"⏱️ Süre: {time.time() - start:.2f} saniye")
        
        print("\n3️⃣ Maç logları:")
        start = time.time()
        maclar = son_maclar(oyuncu_id, sezon)
        print(f"⏱️ Süre: {time.time() - start:.2f} saniye")
        
        if maclar is not None:
            print(f"✅ {len(maclar)} maç bulundu")
    
    print("\n" + "="*70)
    print("✅ Test tamamlandı!")
    print("="*70)

