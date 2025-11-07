"""
🎯 NBA MAÇI ALT/ÜST TAHMİN ANALİZİ – REGRESYONLU MODEL
Profesyonel NBA maç tahmini algoritması
"""

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguedashteamstats, teamdashboardbygeneralsplits, leaguegamefinder
import pandas as pd
import time

def takim_bul(takim_isim):
    """Takım adına göre takım ID'sini bulur"""
    tum_takimlar = teams.get_teams()
    
    for takim in tum_takimlar:
        if (takim_isim.lower() in takim['full_name'].lower() or 
            takim_isim.lower() in takim['nickname'].lower() or
            takim_isim.upper() == takim['abbreviation']):
            return takim
    
    return None

def takim_istatistikleri_cek(takim_id, sezon='2024-25'):
    """Takımın sezon istatistiklerini çeker"""
    try:
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

def takim_advanced_stats_cek(takim_id, sezon='2024-25'):
    """Takımın gelişmiş istatistiklerini çeker"""
    try:
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

def son_5_mac_analiz(takim_id, sezon='2024-25'):
    """Son 5 maç analizini yapar"""
    try:
        time.sleep(0.6)  # Rate limiting
        
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=takim_id,
            season_nullable=sezon,
            season_type_nullable='Regular Season'
        )
        
        games = gamefinder.get_data_frames()[0]
        
        if games.empty:
            return None
        
        # Son 5 maçı al
        son_5 = games.head(5)
        
        # Rakip skorunu hesapla (PLUS_MINUS kullanarak)
        son_5['OPP_PTS'] = son_5['PTS'] - son_5['PLUS_MINUS']
        
        # Ortalamalar
        atilan_sayi_ort = son_5['PTS'].mean()
        yenilen_sayi_ort = son_5['OPP_PTS'].mean()
        fg_pct_ort = son_5['FG_PCT'].mean() * 100
        fg3_pct_ort = son_5['FG3_PCT'].mean() * 100
        toplam_skor_ort = (son_5['PTS'] + son_5['OPP_PTS']).mean()
        
        return {
            'atilan_sayi_ort': atilan_sayi_ort,
            'yenilen_sayi_ort': yenilen_sayi_ort,
            'fg_pct_ort': fg_pct_ort,
            'fg3_pct_ort': fg3_pct_ort,
            'toplam_skor_ort': toplam_skor_ort,
            'mac_sayisi': len(son_5)
        }
        
    except Exception as e:
        print(f"❌ Son 5 maç hatası: {e}")
        return None


def mac_tahmini_v2(ev_takim, dep_takim, baraj=None, sezon='2024-25', verbose=False):
    """
    🎯 REGRESYONLU PROFESYONEL NBA TAHMİN ALGORİTMASI
    
    Args:
        ev_takim: Ev sahibi takım
        dep_takim: Deplasman takımı
        baraj: İddaa barajı (örn: 220.5)
        sezon: NBA sezonu
        verbose: Detaylı çıktı
    """
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"🎯 REGRESYONLU NBA TAHMİN ANALİZİ")
        print(f"{'='*80}")
        print(f"🏠 Ev Sahibi: {ev_takim}")
        print(f"✈️ Deplasman: {dep_takim}")
        if baraj:
            print(f"📊 Baraj: {baraj}")
        print(f"{'='*80}\n")
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. TAKIMLARI BUL VE VERİLERİ ÇEK
    # ═══════════════════════════════════════════════════════════════════
    
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
    
    # Son 5 maç analizi
    ev_son5 = son_5_mac_analiz(ev_takim_data['id'], sezon)
    dep_son5 = son_5_mac_analiz(dep_takim_data['id'], sezon)
    
    if not ev_son5 or not dep_son5:
        if verbose:
            print("❌ Son 5 maç verisi çekilemedi!")
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. TEMEL VERİLER
    # ═══════════════════════════════════════════════════════════════════
    
    ev_sezon_atilan = ev_stats['PTS']
    dep_sezon_atilan = dep_stats['PTS']
    
    ev_son5_atilan = ev_son5['atilan_sayi_ort']
    dep_son5_atilan = dep_son5['atilan_sayi_ort']
    
    ev_yenilen = ev_stats['OPP_PTS'] if 'OPP_PTS' in ev_stats else ev_sezon_atilan - 5
    dep_yenilen = dep_stats['OPP_PTS'] if 'OPP_PTS' in dep_stats else dep_sezon_atilan - 5
    
    # Advanced stats
    ev_off_rating = ev_advanced['OFF_RATING'] if ev_advanced is not None and 'OFF_RATING' in ev_advanced else 110
    dep_off_rating = dep_advanced['OFF_RATING'] if dep_advanced is not None and 'OFF_RATING' in dep_advanced else 110
    ev_def_rating = ev_advanced['DEF_RATING'] if ev_advanced is not None and 'DEF_RATING' in ev_advanced else 110
    dep_def_rating = dep_advanced['DEF_RATING'] if dep_advanced is not None and 'DEF_RATING' in dep_advanced else 110
    ev_pace = ev_advanced['PACE'] if ev_advanced is not None and 'PACE' in ev_advanced else 100
    dep_pace = dep_advanced['PACE'] if dep_advanced is not None and 'PACE' in dep_advanced else 100
    
    ortalama_pace = (ev_pace + dep_pace) / 2
    
    # Shooting stats
    ev_fg_pct = ev_son5['fg_pct_ort']
    dep_fg_pct = dep_son5['fg_pct_ort']
    ev_3p_pct = ev_son5['fg3_pct_ort']
    dep_3p_pct = dep_son5['fg3_pct_ort']
    
    if verbose:
        print(f"📊 TEMEL VERİLER")
        print(f"{'─'*80}")
        print(f"Ev Takım:")
        print(f"  Sezon Ort: {ev_sezon_atilan:.1f} | Son 5 Ort: {ev_son5_atilan:.1f}")
        print(f"  FG%: {ev_fg_pct:.1f}% | 3P%: {ev_3p_pct:.1f}%")
        print(f"  OffRtg: {ev_off_rating:.1f} | DefRtg: {ev_def_rating:.1f} | Pace: {ev_pace:.1f}")
        print(f"\nDeplasman Takım:")
        print(f"  Sezon Ort: {dep_sezon_atilan:.1f} | Son 5 Ort: {dep_son5_atilan:.1f}")
        print(f"  FG%: {dep_fg_pct:.1f}% | 3P%: {dep_3p_pct:.1f}%")
        print(f"  OffRtg: {dep_off_rating:.1f} | DefRtg: {dep_def_rating:.1f} | Pace: {dep_pace:.1f}")
        print(f"\nOrtalama Pace: {ortalama_pace:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. FORMÜL HESAPLAMALARI (OPTİMİZE EDİLMİŞ)
    # ═══════════════════════════════════════════════════════════════════
    
    # 🔹 BAZ TOPLAM (B) - Son 5 maç ortalaması
    B = ev_son5_atilan + dep_son5_atilan
    
    # 🔹 TEMPO ETKİSİ (T) - Katsayı 0.9'a yükseltildi (hızlı maçlar daha fazla etki)
    T = (ortalama_pace - 98) * 0.9
    
    # 🔹 VERİMLİLİK ETKİSİ (V) - Asimetrik hesaplama (kötü savunma daha fazla etki)
    # Her takımın hücumu rakibin savunmasına karşı
    V = ((ev_off_rating - dep_def_rating) + (dep_off_rating - ev_def_rating)) * 0.35
    
    # 🔹 FORM ETKİSİ (F) - Katsayı 0.5'e düşürüldü (aşırı form etkisini azalt)
    F = ((ev_son5_atilan - ev_sezon_atilan) + (dep_son5_atilan - dep_sezon_atilan)) * 0.5
    
    # 🔹 SHOOTING PERFORMANSI (S) - Katsayı 0.6'ya yükseltildi
    ortalama_shooting = (ev_fg_pct + dep_fg_pct + ev_3p_pct + dep_3p_pct) / 4
    S = (ortalama_shooting - 45) * 0.6
    
    # 🔹 SAVUNMA CEZASI (D) - Güçlü savunmalar skoru düşürür (ÇOK AGRESIF)
    # 226 = 2 takım için ideal savunma toplamı (113 + 113) - daha sıkı
    D = ((ev_def_rating + dep_def_rating) - 226) * 0.5
    
    # 🔹 EV AVANTAJI (E)
    E = 1.5 if ortalama_pace < 98 else 1.0
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. HAM TOPLAM HESAPLAMA
    # ═══════════════════════════════════════════════════════════════════
    
    H = B + T + V + F + S - D + E
    
    if verbose:
        print(f"\n📈 FORMÜL HESAPLAMALARI (OPTİMİZE EDİLMİŞ)")
        print(f"{'─'*80}")
        print(f"🔹 Baz Toplam (B):           {B:.1f}")
        print(f"🔹 Tempo Etkisi (T):         {T:+.1f}  (pace: {ortalama_pace:.1f}, katsayı: 0.9)")
        print(f"🔹 Verimlilik Etkisi (V):    {V:+.1f}  (asimetrik, katsayı: 0.35)")
        print(f"🔹 Form Etkisi (F):          {F:+.1f}  (katsayı: 0.5)")
        print(f"🔹 Shooting Performansı (S): {S:+.1f}  (ort: {ortalama_shooting:.1f}%, katsayı: 0.6)")
        print(f"🔹 Savunma Cezası (D):       {D:+.1f}  (DefRtg toplamı: {ev_def_rating + dep_def_rating:.1f}, katsayı: 0.5)")
        print(f"🔹 Ev Avantajı (E):          {E:+.1f}")
        print(f"{'─'*80}")
        print(f"📊 HAM TOPLAM (H):           {H:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. REGRESYON KATSAYISI
    # ═══════════════════════════════════════════════════════════════════
    
    R = (ev_sezon_atilan + dep_sezon_atilan) / (ev_son5_atilan + dep_son5_atilan)
    
    if R < 0.90:
        # Takımlar çok formda, çok agresif düzeltme
        regresyon_carpan = 0.90
        regresyon_aciklama = "Takımlar çok formda, çok agresif düzeltme"
    elif R < 0.94:
        # Takımlar formda, agresif düzeltme
        regresyon_carpan = 0.93
        regresyon_aciklama = "Takımlar formda, agresif düzeltme"
    elif R > 1.08:
        # Takımlar çok formsuz, agresif yukarı düzeltme
        regresyon_carpan = 1.05
        regresyon_aciklama = "Takımlar çok formsuz, agresif yukarı düzeltme"
    elif R > 1.04:
        # Takımlar formsuz, orta yukarı düzeltme
        regresyon_carpan = 1.02
        regresyon_aciklama = "Takımlar formsuz, orta yukarı düzeltme"
    else:
        # Dengeli
        regresyon_carpan = 1.00
        regresyon_aciklama = "Dengeli form, düzeltme yok"
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. NİHAİ SKOR TAHMİNİ
    # ═══════════════════════════════════════════════════════════════════
    
    Total = H * regresyon_carpan
    
    if verbose:
        print(f"\n🔄 REGRESYON ANALİZİ")
        print(f"{'─'*80}")
        print(f"Regresyon Oranı (R):    {R:.3f}")
        print(f"Regresyon Çarpanı:      {regresyon_carpan:.3f}")
        print(f"Açıklama:               {regresyon_aciklama}")
        print(f"{'─'*80}")
        print(f"🎯 NİHAİ TAHMİN:         {Total:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. EK İNCE AYARLAR
    # ═══════════════════════════════════════════════════════════════════
    
    ince_ayar_toplam = 0
    ince_ayar_aciklama = []
    
    # Savunma maçı kontrolü
    if ev_def_rating < 112 and dep_def_rating < 112:
        ince_ayar_toplam -= 4
        ince_ayar_aciklama.append("Her iki takım güçlü savunma (-4)")
    
    # Blowout riski kontrolü (aşırı form farkı)
    form_farki = abs((ev_son5_atilan - ev_sezon_atilan) - (dep_son5_atilan - dep_sezon_atilan))
    if form_farki > 15:
        ince_ayar_toplam -= 6
        ince_ayar_aciklama.append(f"Aşırı form farkı - blowout riski (-6)")
    
    # Deplasman formu (daha sıkı kriter)
    if dep_son5_atilan > 118:  # Çok yüksek eşik
        ince_ayar_toplam += 2  # Azaltıldı
        ince_ayar_aciklama.append("Deplasman takımı çok yüksek formda (+2)")
    
    Total += ince_ayar_toplam
    
    if verbose and ince_ayar_aciklama:
        print(f"\n⚙️ İNCE AYARLAR")
        print(f"{'─'*80}")
        for aciklama in ince_ayar_aciklama:
            print(f"  • {aciklama}")
        print(f"Toplam İnce Ayar: {ince_ayar_toplam:+.1f}")
        print(f"{'─'*80}")
        print(f"🎯 FİNAL TAHMİN:         {Total:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. BARAJ ANALİZİ VE KARAR
    # ═══════════════════════════════════════════════════════════════════
    
    karar = None
    guven_seviyesi = None
    risk_seviyesi = None
    aciklama = ""
    
    if baraj:
        fark = Total - baraj
        
        # Tempo + Verimlilik + Form toplamı
        egilim_skoru = T + V + F
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"📊 BARAJ ANALİZİ")
            print(f"{'='*80}")
            print(f"Tahmin:     {Total:.1f}")
            print(f"Baraj:      {baraj}")
            print(f"Fark:       {fark:+.1f}")
            print(f"Eğilim Skoru (T+V+F): {egilim_skoru:+.1f}")
        
        # Karar mantığı
        if abs(fark) >= 3:
            if fark >= 3:
                karar = "ÜST"
                guven_seviyesi = "Yüksek" if abs(fark) >= 5 else "Orta"
                risk_seviyesi = "Yeşil"
            else:
                karar = "ALT"
                guven_seviyesi = "Yüksek" if abs(fark) <= -5 else "Orta"
                risk_seviyesi = "Yeşil"
        else:
            karar = "PAS"
            guven_seviyesi = "Düşük"
            risk_seviyesi = "Kırmızı"
            aciklama = "Riskli bölge, bahis önerilmez"
        
        # Tempo açıklaması
        if ortalama_pace > 102:
            tempo_aciklama = f"Hızlı maç (pace: {ortalama_pace:.1f})"
        elif ortalama_pace < 98:
            tempo_aciklama = f"Yavaş maç, savunma ağırlıklı (pace: {ortalama_pace:.1f})"
        else:
            tempo_aciklama = f"Normal tempolu maç (pace: {ortalama_pace:.1f})"
        
        # Regresyon etkisi
        regresyon_etki_pct = (regresyon_carpan - 1) * 100
        
        # Neden yüksek/düşük çıktığı
        if R < 0.95:
            neden = f"Son 5 maç ortalaması ({B:.1f}) sezon ortalamasından ({ev_sezon_atilan + dep_sezon_atilan:.1f}) yüksek. Regresyon ile {abs(regresyon_etki_pct):.1f}% düşürüldü."
        elif R > 1.05:
            neden = f"Son 5 maç ortalaması ({B:.1f}) sezon ortalamasından ({ev_sezon_atilan + dep_sezon_atilan:.1f}) düşük. Regresyon ile {abs(regresyon_etki_pct):.1f}% artırıldı."
        else:
            neden = "Son 5 maç ve sezon ortalaması dengeli."
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"🎯 ANALİZ RAPORU")
            print(f"{'='*80}")
            print(f"1. Tahmini Toplam Skor:  {Total:.1f}")
            print(f"2. Tempo:                {tempo_aciklama}")
            print(f"3. Regresyon Etkisi:     {regresyon_etki_pct:+.1f}%")
            print(f"4. Açıklama:             {neden}")
            print(f"5. Nihai Yön:            {karar}")
            print(f"6. Güven Seviyesi:       {guven_seviyesi}")
            print(f"7. Risk Seviyesi:        {risk_seviyesi}")
            if aciklama:
                print(f"8. Not:                  {aciklama}")
            print(f"{'='*80}\n")
        
        return {
            'toplam_tahmin': Total,
            'baraj': baraj,
            'fark': fark,
            'karar': karar,
            'guven_seviyesi': guven_seviyesi,
            'risk_seviyesi': risk_seviyesi,
            'tempo_aciklama': tempo_aciklama,
            'regresyon_etki_pct': regresyon_etki_pct,
            'neden': neden,
            'aciklama': aciklama if aciklama else neden,
            'ev_takim': ev_takim_data['full_name'],
            'dep_takim': dep_takim_data['full_name'],
            # Detay bilgiler
            'baz_toplam': B,
            'tempo_etki': T,
            'verimlilik_etki': V,
            'form_etki': F,
            'shooting_etki': S,
            'savunma_cezasi': D,
            'ev_avantaj': E,
            'ham_toplam': H,
            'regresyon_carpan': regresyon_carpan,
            'ince_ayar': ince_ayar_toplam,
            'ortalama_pace': ortalama_pace,
            'ev_sezon_ort': ev_sezon_atilan,
            'dep_sezon_ort': dep_sezon_atilan,
            'ev_son5_ort': ev_son5_atilan,
            'dep_son5_ort': dep_son5_atilan,
            # Takım rating ve yüzde bilgileri
            'ev_off_rating': ev_off_rating,
            'ev_def_rating': ev_def_rating,
            'dep_off_rating': dep_off_rating,
            'dep_def_rating': dep_def_rating,
            'ev_fg_pct': ev_fg_pct,
            'ev_3p_pct': ev_3p_pct,
            'dep_fg_pct': dep_fg_pct,
            'dep_3p_pct': dep_3p_pct
        }
    else:
        return {
            'toplam_tahmin': Total,
            'ev_takim': ev_takim_data['full_name'],
            'dep_takim': dep_takim_data['full_name']
        }


if __name__ == "__main__":
    # Test
    print("🧪 TEST: Lakers vs Celtics")
    sonuc = mac_tahmini_v2('Lakers', 'Celtics', baraj=220.5, sezon='2024-25', verbose=True)

