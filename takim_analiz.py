"""
NBA Takım İstatistikleri ve Maç Analizi
"""

from nba_api.stats.endpoints import leaguedashteamstats, teamdashboardbygeneralsplits, teamgamelog, leaguegamefinder
from nba_api.stats.static import teams
import pandas as pd
import numpy as np
import time

def takim_bul(takim_isim):
    """Takım adına göre takım ID'sini bulur"""
    tum_takimlar = teams.get_teams()
    
    # Tam isim veya kısa isimle ara
    for takim in tum_takimlar:
        if (takim_isim.lower() in takim['full_name'].lower() or 
            takim_isim.lower() in takim['nickname'].lower() or
            takim_isim.upper() == takim['abbreviation']):
            return takim
    
    return None

def takim_istatistikleri_cek(takim_id, sezon='2025-26'):
    """Takımın sezon istatistiklerini çeker"""
    
    try:
        # Genel istatistikler
        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=sezon,
            per_mode_detailed='PerGame',
            season_type_all_star='Regular Season'
        )
        
        df = stats.get_data_frames()[0]
        takim_data = df[df['TEAM_ID'] == takim_id]
        
        if not takim_data.empty:
            return takim_data.iloc[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def takim_advanced_stats_cek(takim_id, sezon='2025-26'):
    """Takımın gelişmiş istatistiklerini çeker"""
    
    try:
        # Advanced stats
        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=sezon,
            measure_type_detailed_defense='Advanced',
            season_type_all_star='Regular Season'
        )
        
        df = stats.get_data_frames()[0]
        takim_data = df[df['TEAM_ID'] == takim_id]
        
        if not takim_data.empty:
            return takim_data.iloc[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

def son_5_mac_analiz(takim_id, sezon='2025-26'):
    """Takımın son 5 maçının detaylı analizini yapar"""
    
    try:
        # Alternatif yöntem: LeagueGameFinder kullan
        time.sleep(0.6)  # Rate limiting
        
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=takim_id,
            season_nullable=sezon,
            season_type_nullable='Regular Season'
        )
        
        games = gamefinder.get_data_frames()[0]
        
        if games.empty:
            # 2024-25 sezonu dene
            time.sleep(0.6)
            gamefinder = leaguegamefinder.LeagueGameFinder(
                team_id_nullable=takim_id,
                season_nullable='2024-25',
                season_type_nullable='Regular Season'
            )
            games = gamefinder.get_data_frames()[0]
        
        if games.empty:
            return None
        
        # Son 5 maç
        son_5 = games.head(5)
        
        # Detaylı istatistikler
        toplam_skorlar = []
        atilan_sayilar = []
        yenilen_sayilar = []
        fg_percentages = []
        fg3_percentages = []
        
        for _, mac in son_5.iterrows():
            # Takım skoru
            takim_skor = mac['PTS']
            
            # Rakip skorunu bul - MATCHUP'tan çıkar veya hesapla
            # W/L durumuna göre rakip skoru hesapla
            wl = mac['WL']
            plus_minus = mac['PLUS_MINUS'] if 'PLUS_MINUS' in mac else 0
            
            # Rakip skoru = Takım skoru - Plus/Minus
            rakip_skor = takim_skor - plus_minus
            
            toplam_skorlar.append(takim_skor + rakip_skor)
            atilan_sayilar.append(takim_skor)
            yenilen_sayilar.append(rakip_skor)
            
            # FG% ve 3P%
            if 'FG_PCT' in mac:
                fg_percentages.append(mac['FG_PCT'] * 100)
            if 'FG3_PCT' in mac:
                fg3_percentages.append(mac['FG3_PCT'] * 100)
        
        if not toplam_skorlar:
            return None
        
        return {
            'toplam_skor_ort': np.mean(toplam_skorlar),
            'atilan_sayi_ort': np.mean(atilan_sayilar),
            'yenilen_sayi_ort': np.mean(yenilen_sayilar),
            'fg_pct_ort': np.mean(fg_percentages) if fg_percentages else 45.0,
            'fg3_pct_ort': np.mean(fg3_percentages) if fg3_percentages else 35.0,
            'skorlar': toplam_skorlar,
            'mac_sayisi': len(toplam_skorlar),
            'ortalama': np.mean(toplam_skorlar)  # Geriye uyumluluk için
        }
        
    except Exception as e:
        print(f"Son 5 maç hatası: {e}")
        return None

def mac_tahmini(ev_takim, dep_takim, baraj=None, bahis_tipi=None, sezon='2025-26', verbose=False):
    """
    İki takım için maç tahmini yapar
    
    Args:
        ev_takim: Ev sahibi takım
        dep_takim: Deplasman takımı
        baraj: İddaa sitesindeki baraj (örn: 210.5)
        bahis_tipi: 'ÜST' veya 'ALT'
        sezon: NBA sezonu
        verbose: True ise terminal çıktısı verir
    """
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🏀 MAÇ TAHMİNİ")
        print(f"{'='*70}")
        print(f"🏠 Ev Sahibi: {ev_takim}")
        print(f"✈️ Deplasman: {dep_takim}")
        if baraj and bahis_tipi:
            print(f"📊 İddaa Barajı: {baraj} {bahis_tipi}")
        print(f"{'='*70}\n")
    
    # Takımları bul
    ev_takim_data = takim_bul(ev_takim)
    dep_takim_data = takim_bul(dep_takim)
    
    if not ev_takim_data or not dep_takim_data:
        if verbose:
            print("❌ Takımlardan biri bulunamadı!")
        return None
    
    if verbose:
        print(f"✅ Ev: {ev_takim_data['full_name']}")
        print(f"✅ Dep: {dep_takim_data['full_name']}\n")
    
    # İstatistikleri çek
    ev_stats = takim_istatistikleri_cek(ev_takim_data['id'], sezon)
    dep_stats = takim_istatistikleri_cek(dep_takim_data['id'], sezon)
    
    ev_advanced = takim_advanced_stats_cek(ev_takim_data['id'], sezon)
    dep_advanced = takim_advanced_stats_cek(dep_takim_data['id'], sezon)
    
    if ev_stats is None or dep_stats is None:
        if verbose:
            print("❌ İstatistikler çekilemedi!")
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # 🎯 REGRESYONLU PROFESYONEL NBA TAHMİN ALGORİTMASI
    # ═══════════════════════════════════════════════════════════════════
    
    # 1. TEMEL VERİLER
    ev_sezon_atilan = ev_stats['PTS']
    dep_sezon_atilan = dep_stats['PTS']
    
    ev_yenilen = ev_stats['OPP_PTS'] if 'OPP_PTS' in ev_stats else ev_sezon_atilan - 5
    dep_yenilen = dep_stats['OPP_PTS'] if 'OPP_PTS' in dep_stats else dep_sezon_atilan - 5
    
    if verbose:
        print(f"📊 TEMEL İSTATİSTİKLER")
        print(f"{'─'*70}")
        print(f"Ev Skor Ort: {ev_ort_skor:.1f} | Dep Skor Ort: {dep_ort_skor:.1f}")
        print(f"Ev Yenilen: {ev_yenilen:.1f} | Dep Yenilen: {dep_yenilen:.1f}")
    
    # 2. Tempo Analizi
    ev_tempo = ev_advanced['PACE'] if ev_advanced is not None and 'PACE' in ev_advanced else 100
    dep_tempo = dep_advanced['PACE'] if dep_advanced is not None and 'PACE' in dep_advanced else 100
    ortalama_tempo = (ev_tempo + dep_tempo) / 2
    
    tempo_faktoru = ortalama_tempo / 100  # 100 = normal tempo
    
    if ortalama_tempo > 102:
        tempo_yorum = "Hızlı maç bekleniyor (Yüksek skor)"
    elif ortalama_tempo < 98:
        tempo_yorum = "Yavaş maç bekleniyor (Düşük skor)"
    else:
        tempo_yorum = "Normal tempolu maç"
    
    if verbose:
        print(f"\n⚡ TEMPO ANALİZİ")
        print(f"{'─'*70}")
        print(f"Ev Tempo: {ev_tempo:.1f} | Dep Tempo: {dep_tempo:.1f}")
        print(f"Ortalama Tempo: {ortalama_tempo:.1f}")
        print(f"Yorum: {tempo_yorum}")
    
    # 3. Savunma Gücü
    ev_def_rating = ev_advanced['DEF_RATING'] if ev_advanced is not None and 'DEF_RATING' in ev_advanced else 110
    dep_def_rating = dep_advanced['DEF_RATING'] if dep_advanced is not None and 'DEF_RATING' in dep_advanced else 110
    
    ev_savunma = "Güçlü" if ev_def_rating < 108 else "Zayıf" if ev_def_rating > 112 else "Orta"
    dep_savunma = "Güçlü" if dep_def_rating < 108 else "Zayıf" if dep_def_rating > 112 else "Orta"
    
    if verbose:
        print(f"\n🛡️ SAVUNMA ANALİZİ")
        print(f"{'─'*70}")
        print(f"Ev Def Rating: {ev_def_rating:.1f} | Dep Def Rating: {dep_def_rating:.1f}")
        print(f"Ev Savunma: {ev_savunma} | Dep Savunma: {dep_savunma}")
    
    # 4. Ev Avantajı
    ev_avantaji = 3.5  # Ortalama ev avantajı
    
    # 5. SON 5 MAÇ ANALİZİ
    ev_son5 = son_5_mac_analiz(ev_takim_data['id'], sezon)
    dep_son5 = son_5_mac_analiz(dep_takim_data['id'], sezon)
    
    # 6. TAHMİN HESAPLAMA
    
    # Basit model: Her takımın skoru = Kendi ortalaması + Rakibin savunma zayıflığı
    ev_tahmin_skor = ev_ort_skor + (dep_def_rating - 110) * 0.3 + ev_avantaji
    dep_tahmin_skor = dep_ort_skor + (ev_def_rating - 110) * 0.3
    
    # Tempo faktörünü uygula
    ev_tahmin_skor *= tempo_faktoru
    dep_tahmin_skor *= tempo_faktoru
    
    toplam_tahmin_temel = ev_tahmin_skor + dep_tahmin_skor
    
    # PROFESYONEL ANALİZ ALGORİTMASI
    analiz_detay = {
        'tempo_egilim': '',
        'savunma_durumu': '',
        'form_durumu': '',
        'shooting_performans': '',
        'verimlilik_etki': 0,
        'tempo_etki': 0,
        'form_etki': 0,
        'ev_avantaj_etki': 0
    }
    
    if ev_son5 and dep_son5:
        # ═══════════════════════════════════════════════════════════
        # PROFESYONEL NBA ANALİZ ALGORİTMASI
        # ═══════════════════════════════════════════════════════════
        
        # 1. TEMEL SKOR ORTALAMALARI
        ev_atilan_ort = ev_son5['atilan_sayi_ort']
        ev_yenilen_ort = ev_son5['yenilen_sayi_ort']
        dep_atilan_ort = dep_son5['atilan_sayi_ort']
        dep_yenilen_ort = dep_son5['yenilen_sayi_ort']
        
        # Baz toplam = Her iki takımın atılan sayıları toplamı
        baz_toplam = ev_atilan_ort + dep_atilan_ort
        
        # 2. TEMPO ETKİSİ (Pace)
        # Tempo > 100 → hızlı maç → +puan
        # Tempo < 100 → yavaş maç → -puan
        tempo_etki = (ortalama_tempo - 100) * 0.5
        analiz_detay['tempo_etki'] = tempo_etki
        
        # 3. HÜCUM/SAVUNMA VERİMLİLİĞİ (OffRtg / DefRtg)
        # Advanced stats'tan OffRtg al
        ev_off_rating = ev_advanced['OFF_RATING'] if ev_advanced is not None and 'OFF_RATING' in ev_advanced else 110
        dep_off_rating = dep_advanced['OFF_RATING'] if dep_advanced is not None and 'OFF_RATING' in dep_advanced else 110
        
        hucum_ortalama = (ev_off_rating + dep_off_rating) / 2
        savunma_ortalama = (ev_def_rating + dep_def_rating) / 2
        verimlilik_etki = (hucum_ortalama - savunma_ortalama) * 0.3
        analiz_detay['verimlilik_etki'] = verimlilik_etki
        
        # 4. FORM DURUMU (Son 5 maç vs Sezon ortalaması)
        ev_sezon_ort = ev_ort_skor
        dep_sezon_ort = dep_ort_skor
        
        ev_form_degisim = ((ev_atilan_ort - ev_sezon_ort) / ev_sezon_ort) * 100
        dep_form_degisim = ((dep_atilan_ort - dep_sezon_ort) / dep_sezon_ort) * 100
        form_ortalama = (ev_form_degisim + dep_form_degisim) / 2
        
        if form_ortalama > 5:
            form_etki = 5  # Yüksek tempolu
        elif form_ortalama < -5:
            form_etki = -5  # Düşük tempolu
        else:
            form_etki = form_ortalama / 2
        
        analiz_detay['form_etki'] = form_etki
        
        # 5. EV AVANTAJI ETKİSİ
        # Ev takımı hücumda güçlüyse → +3 puan
        ev_hucum_fark = ev_atilan_ort - ev_sezon_ort
        ev_etki = ev_hucum_fark * 0.3 if ev_hucum_fark > 5 else 0
        
        # Deplasman savunması zayıfsa → +3 puan
        dep_savunma_fark = dep_yenilen_ort - dep_sezon_ort
        dep_etki = dep_savunma_fark * 0.3 if dep_savunma_fark > 5 else 0
        
        ev_avantaj_etki = ev_etki + dep_etki
        analiz_detay['ev_avantaj_etki'] = ev_avantaj_etki
        
        # 6. SHOOTING PERFORMANSI
        ev_fg_pct = ev_son5['fg_pct_ort']
        dep_fg_pct = dep_son5['fg_pct_ort']
        ev_fg3_pct = ev_son5['fg3_pct_ort']
        dep_fg3_pct = dep_son5['fg3_pct_ort']
        
        ortalama_fg = (ev_fg_pct + dep_fg_pct) / 2
        ortalama_3p = (ev_fg3_pct + dep_fg3_pct) / 2
        
        # Shooting etkisi
        if ortalama_fg > 48 and ortalama_3p > 38:
            shooting_etki = 3  # Mükemmel şut
        elif ortalama_fg < 43 or ortalama_3p < 32:
            shooting_etki = -3  # Düşük şut
        else:
            shooting_etki = 0
        
        # ═══════════════════════════════════════════════════════════
        # NİHAİ TAHMİN HESAPLAMA
        # ═══════════════════════════════════════════════════════════
        
        toplam_tahmin = baz_toplam
        toplam_tahmin += tempo_etki          # Tempo etkisi
        toplam_tahmin += verimlilik_etki     # Hücum/Savunma dengesi
        toplam_tahmin += form_etki           # Form durumu
        toplam_tahmin += ev_avantaj_etki     # Ev avantajı
        toplam_tahmin += shooting_etki       # Shooting performansı
        
        # 7. DETAYLI AÇIKLAMALAR OLUŞTUR
        son_mac_toplam_ort = (ev_son5['toplam_skor_ort'] + dep_son5['toplam_skor_ort']) / 2
        
        # Tempo eğilimi
        if ortalama_tempo > 102:
            analiz_detay['tempo_egilim'] = f"Yüksek tempo ({ortalama_tempo:.1f} pace, son 5 maç ort: {son_mac_toplam_ort:.1f})"
        elif ortalama_tempo < 98:
            analiz_detay['tempo_egilim'] = f"Düşük tempo ({ortalama_tempo:.1f} pace, son 5 maç ort: {son_mac_toplam_ort:.1f})"
        else:
            analiz_detay['tempo_egilim'] = f"Normal tempo ({ortalama_tempo:.1f} pace)"
        
        # Savunma durumu
        if ev_yenilen_ort > 115 and dep_yenilen_ort > 115:
            analiz_detay['savunma_durumu'] = "Her iki takım da zayıf savunma (çok sayı yiyorlar)"
        elif ev_yenilen_ort < 105 and dep_yenilen_ort < 105:
            analiz_detay['savunma_durumu'] = "Her iki takım da güçlü savunma"
        else:
            analiz_detay['savunma_durumu'] = f"Dengeli savunma (DefRtg: {savunma_ortalama:.1f})"
        
        # Shooting performansı
        if ortalama_fg > 48 and ortalama_3p > 38:
            analiz_detay['shooting_performans'] = f"Mükemmel şut performansı (FG: {ortalama_fg:.1f}%, 3P: {ortalama_3p:.1f}%)"
        elif ortalama_fg < 43 or ortalama_3p < 32:
            analiz_detay['shooting_performans'] = f"Düşük şut performansı (FG: {ortalama_fg:.1f}%, 3P: {ortalama_3p:.1f}%)"
        else:
            analiz_detay['shooting_performans'] = f"Normal şut performansı (FG: {ortalama_fg:.1f}%, 3P: {ortalama_3p:.1f}%)"
        
        # Form durumu
        if form_ortalama > 5:
            analiz_detay['form_durumu'] = f"Her iki takım da ofansif formda (+{form_ortalama:.1f}% form)"
        elif form_ortalama < -5:
            analiz_detay['form_durumu'] = f"Her iki takım da ofansif sıkıntıda ({form_ortalama:.1f}% form)"
        else:
            analiz_detay['form_durumu'] = f"Dengeli form durumu (OffRtg: {hucum_ortalama:.1f})"
        
        if verbose:
            print(f"\n📈 DETAYLI SON 5 MAÇ ANALİZİ")
            print(f"{'─'*70}")
            print(f"Ev Takım:")
            print(f"  Atılan Sayı Ort: {ev_atilan_ort:.1f}")
            print(f"  Yenilen Sayı Ort: {ev_yenilen_ort:.1f}")
            print(f"  FG%: {ev_fg_pct:.1f}% | 3P%: {ev_fg3_pct:.1f}%")
            print(f"\nDeplasman Takım:")
            print(f"  Atılan Sayı Ort: {dep_atilan_ort:.1f}")
            print(f"  Yenilen Sayı Ort: {dep_yenilen_ort:.1f}")
            print(f"  FG%: {dep_fg_pct:.1f}% | 3P%: {dep_fg3_pct:.1f}%")
            print(f"\nToplam Skor Ortalaması: {son_mac_toplam_ort:.1f}")
            print(f"Temel Tahmin: {toplam_tahmin_temel:.1f}")
            print(f"Final Tahmin: {toplam_tahmin:.1f}")
    else:
        toplam_tahmin = toplam_tahmin_temel
        analiz_detay['tempo_egilim'] = "Son 5 maç verisi bulunamadı"
        analiz_detay['savunma_durumu'] = "Sadece sezon ortalaması kullanıldı"
    
    # Standart sapma hesapla (basit model)
    std_sapma = 4.5  # Ortalama NBA maçı standart sapması
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🎯 TAHMİN")
        print(f"{'='*70}")
        print(f"Ev Tahmini: {ev_tahmin_skor:.1f}")
        print(f"Dep Tahmini: {dep_tahmin_skor:.1f}")
        print(f"Toplam Tahmin: {toplam_tahmin:.1f} (±{std_sapma:.1f})")
        
        # Otomatik baraj önerileri
        print(f"\n{'='*70}")
        print(f"📊 BARAJ ANALİZİ")
        print(f"{'='*70}")
    
    # Farklı barajlar için olasılık hesapla
    baraj_secenekleri = [
        toplam_tahmin - 10,
        toplam_tahmin - 5,
        toplam_tahmin - 2.5,
        toplam_tahmin,
        toplam_tahmin + 2.5,
        toplam_tahmin + 5,
        toplam_tahmin + 10
    ]
    
    def baraj_guven_hesapla(baraj_deger, tahmin, std):
        """Barajı geçme olasılığını hesaplar (basit normal dağılım)"""
        z_score = (baraj_deger - tahmin) / std
        
        # Basit olasılık tahmini
        if z_score < -2:
            return 95
        elif z_score < -1:
            return 85
        elif z_score < -0.5:
            return 75
        elif z_score < 0:
            return 65
        elif z_score < 0.5:
            return 45
        elif z_score < 1:
            return 30
        else:
            return 15
    
    # İDDAA BARAJI ANALİZİ
    sonuc_data = None
    
    # PROFESYONEL KARAR ALGORİTMASI
    if baraj and not bahis_tipi:
        fark = toplam_tahmin - baraj
        
        # Güven seviyesi hesaplama
        if abs(fark) >= 8:
            guven_seviyesi = "Çok Yüksek (%85+)"
            guven_puan = 90
        elif abs(fark) >= 5:
            guven_seviyesi = "Yüksek (%75-85)"
            guven_puan = 80
        elif abs(fark) >= 3:
            guven_seviyesi = "Orta (%65-75)"
            guven_puan = 70
        elif abs(fark) >= 2:
            guven_seviyesi = "Düşük (%55-65)"
            guven_puan = 60
        else:
            guven_seviyesi = "Çok Düşük (%50 altı)"
            guven_puan = 45
        
        # Karar: Tahmin > Baraj → ÜST, Tahmin < Baraj → ALT
        if abs(fark) < 2:
            # Çok yakın, riskli
            bahis_tipi = None
            if verbose:
                print(f"\n⚠️ UYARI: Baraj ({baraj}) tahmine çok yakın ({toplam_tahmin:.1f}). Bahis önerilmez!")
        elif fark > 0:
            bahis_tipi = "ÜST"
            if verbose:
                print(f"\n🤖 OTOMATİK KARAR: ÜST")
                print(f"Tahmin: {toplam_tahmin:.1f} | Baraj: {baraj} | Fark: +{fark:.1f}")
                print(f"Güven Seviyesi: {guven_seviyesi}")
        else:
            bahis_tipi = "ALT"
            if verbose:
                print(f"\n🤖 OTOMATİK KARAR: ALT")
                print(f"Tahmin: {toplam_tahmin:.1f} | Baraj: {baraj} | Fark: {fark:.1f}")
                print(f"Güven Seviyesi: {guven_seviyesi}")
    
    if baraj and bahis_tipi:
        fark = toplam_tahmin - baraj
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"🎯 İDDAA BARAJI ANALİZİ")
            print(f"{'='*70}")
            print(f"Tahmin: {toplam_tahmin:.1f}")
            print(f"Baraj:  {baraj} {bahis_tipi}")
            print(f"Fark:   {fark:+.1f}")
        
        # Detaylı açıklama oluştur
        aciklama_parcalar = []
        
        # Tempo bilgisi
        if analiz_detay['tempo_egilim']:
            aciklama_parcalar.append(f"🏃 {analiz_detay['tempo_egilim']}")
        
        # Savunma bilgisi
        if analiz_detay['savunma_durumu']:
            aciklama_parcalar.append(f"🛡️ {analiz_detay['savunma_durumu']}")
        
        # Shooting performansı
        if analiz_detay['shooting_performans']:
            aciklama_parcalar.append(f"🎯 {analiz_detay['shooting_performans']}")
        
        # Form durumu
        if analiz_detay['form_durumu']:
            aciklama_parcalar.append(f"📊 {analiz_detay['form_durumu']}")
        
        # ÜST bahsi için
        if bahis_tipi.upper() == 'ÜST' or bahis_tipi.upper() == 'UST':
            if fark > 10:
                sonuc = "✅ ÇOK GÜVENLİ - GİR!"
                guven = 95
                renk = "Yeşil"
                aciklama_temel = f"Tahmin {toplam_tahmin:.1f}, baraj {baraj}. Maç {toplam_tahmin:.0f} civarı biterse ÜST TUTAR."
            elif fark > 5:
                sonuc = "✅ GÜVENLİ - GİR!"
                guven = 85
                renk = "Yeşil"
                aciklama_temel = f"Tahmin barajın {fark:.1f} puan üzerinde. ÜST bahsi güvenli görünüyor."
            elif fark > 2:
                sonuc = "✅ GÜVENLİ"
                guven = 70
                renk = "Yeşil"
                aciklama_temel = f"Tahmin barajın üzerinde ama yakın. Makul risk."
            elif fark > -2:
                sonuc = "⚠️ SINIRDA - RİSKLİ"
                guven = 50
                renk = "Sarı"
                aciklama_temel = f"Tahmin baraj civarında. Çok riskli, önerilmez."
            elif fark > -5:
                sonuc = "❌ RİSKLİ - GİRME!"
                guven = 25
                renk = "Kırmızı"
                aciklama_temel = f"Tahmin barajın altında. ÜST bahsi tutmaz."
            else:
                sonuc = "❌ ÇOK RİSKLİ - UZAK DUR!"
                guven = 10
                renk = "Kırmızı"
                aciklama_temel = f"Tahmin {toplam_tahmin:.1f}, baraj {baraj}. ÜST bahsi kesinlikle tutmaz!"
        
        # ALT bahsi için
        else:  # ALT
            if fark < -10:
                sonuc = "✅ ÇOK GÜVENLİ - GİR!"
                guven = 95
                renk = "Yeşil"
                aciklama_temel = f"Tahmin {toplam_tahmin:.1f}, baraj {baraj}. Maç {toplam_tahmin:.0f} civarı biterse ALT TUTAR."
            elif fark < -5:
                sonuc = "✅ GÜVENLİ - GİR!"
                guven = 85
                renk = "Yeşil"
                aciklama_temel = f"Tahmin barajın {abs(fark):.1f} puan altında. ALT bahsi güvenli görünüyor."
            elif fark < -2:
                sonuc = "✅ GÜVENLİ"
                guven = 70
                renk = "Yeşil"
                aciklama_temel = f"Tahmin barajın altında ama yakın. Makul risk."
            elif fark < 2:
                sonuc = "⚠️ SINIRDA - RİSKLİ"
                guven = 50
                renk = "Sarı"
                aciklama_temel = f"Tahmin baraj civarında. Çok riskli, önerilmez."
            elif fark < 5:
                sonuc = "❌ RİSKLİ - GİRME!"
                guven = 25
                renk = "Kırmızı"
                aciklama_temel = f"Tahmin barajın üzerinde. ALT bahsi tutmaz."
            else:
                sonuc = "❌ ÇOK RİSKLİ - UZAK DUR!"
                guven = 10
                renk = "Kırmızı"
                aciklama_temel = f"Tahmin {toplam_tahmin:.1f}, baraj {baraj}. ALT bahsi kesinlikle tutmaz!"
        
        # Detaylı açıklama birleştir
        aciklama = aciklama_temel + "\n\n" + " | ".join(aciklama_parcalar) if aciklama_parcalar else aciklama_temel
        
        if verbose:
            print(f"\n{'─'*70}")
            print(f"📊 SONUÇ: {sonuc}")
            print(f"{'─'*70}")
            print(f"Güven Oranı: %{guven}")
            print(f"Risk Seviyesi: {renk}")
            print(f"\n💡 AÇIKLAMA:")
            print(f"{aciklama}")
        
        sonuc_data = {
            'baraj': baraj,
            'bahis_tipi': bahis_tipi,
            'tahmin': toplam_tahmin,
            'fark': fark,
            'sonuc': sonuc,
            'guven': guven,
            'renk': renk,
            'aciklama': aciklama
        }
    
    # Otomatik öneriler (baraj girilmemişse)
    if not baraj and verbose:
        print(f"\n💡 OTOMATİK BARAJ ÖNERİLERİ:")
        print(f"{'─'*70}")
        
        oneriler = [
            (toplam_tahmin - 5, "Çok Güvenli Alt"),
            (toplam_tahmin - 2.5, "Güvenli Alt"),
            (toplam_tahmin, "Sınırda"),
            (toplam_tahmin + 2.5, "Güvenli Üst"),
            (toplam_tahmin + 5, "Çok Güvenli Üst")
        ]
        
        for baraj_val, aciklama in oneriler:
            guven = baraj_guven_hesapla(baraj_val, toplam_tahmin, std_sapma)
            if guven >= 75:
                icon = "✅"
            elif guven >= 50:
                icon = "⚠️"
            else:
                icon = "❌"
            print(f"{icon} {baraj_val:.1f}+ → %{guven} ({aciklama})")
        
        # En güvenli öneri
        onerilen_baraj = toplam_tahmin - 3
        print(f"\n🎯 ÖNERİLEN GÜVENLİ BARAJ: {onerilen_baraj:.1f}+")
    
    if verbose:
        print(f"\n{'='*70}")
    
    # İlk yarı tahmini
    ilk_yari_tahmin = toplam_tahmin * 0.48  # Genelde ilk yarı %48
    
    if verbose:
        print(f"\n🕐 İLK YARI TAHMİNİ")
        print(f"{'─'*70}")
        print(f"İlk Yarı Toplam: {ilk_yari_tahmin:.1f}")
        
        print(f"\n{'='*70}\n")
    
    return {
        'ev_takim': ev_takim_data['full_name'],
        'dep_takim': dep_takim_data['full_name'],
        'ev_tahmin': ev_tahmin_skor,
        'dep_tahmin': dep_tahmin_skor,
        'toplam_tahmin': toplam_tahmin,
        'std_sapma': std_sapma,
        'sonuc': sonuc_data,
        'ilk_yari': ilk_yari_tahmin,
        'tempo': ortalama_tempo,
        'tempo_yorum': tempo_yorum,
        'onerilen_baraj': toplam_tahmin - 3
    }

# Test
if __name__ == "__main__":
    print("🚀 NBA MAÇ ANALİZ SİSTEMİ TEST\n")
    
    # Test 1: ÜST bahsi - Güvenli
    print("\n" + "="*70)
    print("TEST 1: ÜST BAHSİ - GÜVENLİ SENARYO")
    print("="*70)
    sonuc1 = mac_tahmini("Lakers", "Celtics", baraj=210.5, bahis_tipi="ÜST", sezon="2024-25", verbose=True)
    
    # Test 2: ÜST bahsi - Riskli
    print("\n\n" + "="*70)
    print("TEST 2: ÜST BAHSİ - RİSKLİ SENARYO")
    print("="*70)
    sonuc2 = mac_tahmini("Lakers", "Celtics", baraj=234.5, bahis_tipi="ÜST", sezon="2024-25", verbose=True)
    
    # Test 3: ALT bahsi - Güvenli
    print("\n\n" + "="*70)
    print("TEST 3: ALT BAHSİ - GÜVENLİ SENARYO")
    print("="*70)
    sonuc3 = mac_tahmini("Warriors", "Heat", baraj=235.5, bahis_tipi="ALT", sezon="2024-25", verbose=True)
    
    # Test 4: Barajsız (otomatik öneriler)
    print("\n\n" + "="*70)
    print("TEST 4: OTOMATİK ÖNERİLER")
    print("="*70)
    sonuc4 = mac_tahmini("Warriors", "Heat", sezon="2024-25", verbose=True)

