"""
Garbage Time & Top Paylaşımı Analiz Modülü
Favori takımlarda yıldız oyuncuların risk analizini yapar
"""

from nba_api.stats.endpoints import teamgamelog
import pandas as pd
import time

def takim_son_5_mac_skorlari(takim_id, sezon='2025-26'):
    """
    Takımın son 5 maçındaki oyuncu skorlarını analiz eder
    
    Returns:
        dict: {
            'top_scorers': [(oyuncu_adi, ortalama_pts), ...],
            'count_20plus': int,
            'team_avg_pts': float
        }
    """
    try:
        time.sleep(0.6)  # Rate limiting
        
        # Takım maç loglarını çek
        gamelog = teamgamelog.TeamGameLog(team_id=takim_id, season=sezon)
        df = gamelog.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Son 5 maç
        son_5 = df.head(5)
        
        # Takım ortalama skoru
        team_avg_pts = son_5['PTS'].mean()
        
        # Not: NBA API'den oyuncu bazlı skor almak için başka endpoint gerekli
        # Şimdilik takım toplam skorunu kullanıyoruz
        
        return {
            'team_avg_pts': team_avg_pts,
            'total_games': len(son_5),
            'avg_margin': son_5['PLUS_MINUS'].mean() if 'PLUS_MINUS' in son_5.columns else 0
        }
        
    except Exception as e:
        print(f"⚠️ Takım skor analizi hatası: {e}")
        return None

def takim_oyuncu_skorlari_analiz(takim_id, sezon='2025-26'):
    """
    Takımın son 5 maçında 20+ puan atan oyuncu sayısını hesaplar
    
    Not: Bu fonksiyon için playergamelogs endpoint'i gerekli
    Şu an basitleştirilmiş versiyon
    """
    # TODO: Takım roster'ını çek ve her oyuncunun son 5 maç ortalamasını hesapla
    # Şimdilik placeholder
    return {
        'count_20plus': 0,  # Hesaplanacak
        'top_scorers': []
    }

def garbage_time_risk_analizi(
    oran, 
    takim_id=None,
    sezon='2025-26',
    favorite_threshold=1.25,  # Daha sıkı favori eşiği
    min_scorer_pts=20,
    base_penalty=0.08,  # %25 → %8 (çok daha yumuşak)
    max_penalty=0.15    # %45 → %15 (maksimum da düşük)
):
    """
    Garbage Time ve Top Paylaşımı Risk Analizi
    
    Args:
        oran: Maç oranı (float, örn: 1.22)
        takim_id: Takım ID
        sezon: NBA sezonu
        favorite_threshold: Favori eşiği (default: 1.30)
        min_scorer_pts: Minimum skor eşiği (default: 20)
        base_penalty: Temel ceza oranı (default: 0.25)
        max_penalty: Maksimum ceza oranı (default: 0.45)
    
    Returns:
        dict: {
            'is_risky': bool,
            'penalty_factor': float,
            'reason': str,
            'recommendation': str
        }
    """
    
    result = {
        'is_risky': False,
        'penalty_factor': 0.0,
        'reason': '',
        'recommendation': '',
        'details': {}
    }
    
    # 1. Favori kontrolü
    if oran > favorite_threshold:
        result['reason'] = f"Takım favori değil (oran: {oran:.2f} > {favorite_threshold})"
        result['recommendation'] = "Normal analiz uygula"
        return result
    
    result['details']['is_favorite'] = True
    result['details']['odds'] = oran
    
    # 2. Takım skor analizi (opsiyonel - API varsa)
    if takim_id:
        takim_stats = takim_son_5_mac_skorlari(takim_id, sezon)
        if takim_stats:
            result['details']['team_avg_pts'] = takim_stats['team_avg_pts']
            result['details']['avg_margin'] = takim_stats['avg_margin']
            
            # Eğer takım son 5 maçta ortalama 10+ farkla kazanıyorsa
            if takim_stats['avg_margin'] > 10:
                result['details']['blowout_tendency'] = True
                base_penalty += 0.05  # Ekstra %5 ceza
    
    # 3. Basitleştirilmiş skor analizi
    # TODO: Gerçek oyuncu skorlarını çek
    # Şimdilik kullanıcı girişine göre çalışacak
    
    # Manuel mod: Kullanıcı "2+ oyuncu 20+ skor" bilgisini verecek
    # Şimdilik varsayılan: Favori takımda genelde 2+ skorer var
    count_20plus = 2  # Placeholder
    
    if count_20plus >= 2:
        result['is_risky'] = True
        
        # Penalty hesapla (daha yumuşak)
        penalty_pct = min(
            base_penalty + 0.03 * (count_20plus - 2),  # %10 → %3 (çok daha az)
            max_penalty
        )
        
        result['penalty_factor'] = penalty_pct
        result['reason'] = (
            f"⚠️ RİSKLİ: Takım favori (oran: {oran:.2f}) ve "
            f"muhtemelen {count_20plus}+ oyuncu 20+ skor yapıyor"
        )
        result['recommendation'] = (
            f"Garbage time riski! Tahmin ve güven %{int(penalty_pct*100)} azaltılmalı"
        )
        result['details']['count_20plus'] = count_20plus
    else:
        result['reason'] = "Takım favori ama tek skorer var, risk düşük"
        result['recommendation'] = "Normal analiz uygula"
    
    return result

def uygula_garbage_time_penalty(
    final_tahmin,
    guven_skoru,
    oran,
    takim_id=None,
    sezon='2025-26'
):
    """
    Garbage time penalty'sini uygula
    
    Returns:
        dict: {
            'adjusted_tahmin': float,
            'adjusted_guven': int,
            'penalty_applied': bool,
            'penalty_info': dict
        }
    """
    
    # Risk analizi yap
    risk = garbage_time_risk_analizi(oran, takim_id, sezon)
    
    if not risk['is_risky']:
        return {
            'adjusted_tahmin': final_tahmin,
            'adjusted_guven': guven_skoru,
            'penalty_applied': False,
            'penalty_info': risk
        }
    
    # Penalty uygula
    penalty = risk['penalty_factor']
    
    adjusted_tahmin = final_tahmin * (1 - penalty)
    adjusted_guven = int(guven_skoru * (1 - penalty * 0.8))
    
    return {
        'adjusted_tahmin': adjusted_tahmin,
        'adjusted_guven': adjusted_guven,
        'penalty_applied': True,
        'penalty_factor': penalty,
        'penalty_info': risk,
        'original_tahmin': final_tahmin,
        'original_guven': guven_skoru
    }


if __name__ == "__main__":
    print("🧪 Garbage Time Analyzer Test\n")
    
    # Test 1: Favori takım
    print("Test 1: Favori Takım (oran: 1.22)")
    result1 = garbage_time_risk_analizi(oran=1.22)
    print(f"Riskli: {result1['is_risky']}")
    print(f"Penalty: %{int(result1['penalty_factor']*100)}")
    print(f"Sebep: {result1['reason']}")
    print(f"Öneri: {result1['recommendation']}\n")
    
    # Test 2: Favori değil
    print("Test 2: Favori Değil (oran: 1.85)")
    result2 = garbage_time_risk_analizi(oran=1.85)
    print(f"Riskli: {result2['is_risky']}")
    print(f"Sebep: {result2['reason']}\n")
    
    # Test 3: Penalty uygulama
    print("Test 3: Penalty Uygulama")
    print("Orijinal: Tahmin=35, Güven=%80")
    adjusted = uygula_garbage_time_penalty(
        final_tahmin=35,
        guven_skoru=80,
        oran=1.22
    )
    print(f"Düzeltilmiş: Tahmin={adjusted['adjusted_tahmin']:.1f}, Güven=%{adjusted['adjusted_guven']}")
    print(f"Penalty uygulandı: {adjusted['penalty_applied']}")
    
    print("\n✅ Test tamamlandı!")

