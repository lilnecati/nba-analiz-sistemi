"""
NBA OYUNCU BARAJ ANALİZ SİSTEMİ
Oyuncu prop bet (bahis) analizi için gelişmiş algoritma
"""

try:
    # Önce optimize edilmiş versiyonu dene
    from nba_data_optimized import oyuncu_bul, sezon_istatistikleri_cek, son_maclar, oyuncu_detay_bilgi
    print("✅ Optimize edilmiş NBA API kullanılıyor (Cache + Retry + Rate Limit)")
except ImportError:
    # Yoksa eski versiyonu kullan
    from test_nba_data import oyuncu_bul, sezon_istatistikleri_cek, son_maclar, oyuncu_detay_bilgi
    print("⚠️ Standart NBA API kullanılıyor")

from takim_analiz import takim_bul, takim_istatistikleri_cek, takim_advanced_stats_cek, son_5_mac_analiz
from garbage_time_analyzer import uygula_garbage_time_penalty
import pandas as pd
import numpy as np

class BarajAnaliz:
    """Oyuncu bahis barajı analiz sınıfı"""
    
    def __init__(self, oyuncu_isim, baraj_limit, analiz_tipi='SAR', ev_deplasman='Bilinmiyor', mac_orani=None):
        """
        Args:
            oyuncu_isim: Oyuncu adı
            baraj_limit: Baraj limiti (örn: 40, 45)
            analiz_tipi: 'SAR' (Sayı+Asist+Ribaund), 'PTS' (Sadece Sayı), 
                        'AST' (Sadece Asist), 'REB' (Sadece Ribaund)
            ev_deplasman: 'Ev', 'Deplasman', veya 'Bilinmiyor'
            mac_orani: Maç oranı (float, örn: 1.22) - Garbage time analizi için
        """
        self.oyuncu_isim = oyuncu_isim
        self.baraj_limit = baraj_limit
        self.analiz_tipi = analiz_tipi
        self.ev_deplasman = ev_deplasman
        self.mac_orani = mac_orani
        self.oyuncu_data = None
        self.sezon_stats = None
        self.mac_loglar = None
        
    def veri_cek(self):
        """Oyuncu verilerini çeker"""
        print(f"\n{'='*70}")
        print(f"🎯 BARAJ ANALİZ SİSTEMİ")
        print(f"{'='*70}")
        print(f"Oyuncu: {self.oyuncu_isim}")
        print(f"Baraj: {self.baraj_limit}+")
        print(f"Analiz Tipi: {self.analiz_tipi}")
        print(f"{'='*70}\n")
        
        # Oyuncuyu bul
        oyuncular = oyuncu_bul(self.oyuncu_isim)
        if not oyuncular:
            return False
        
        self.oyuncu_data = oyuncular[0]
        oyuncu_id = self.oyuncu_data['id']
        
        # Oyuncu detay bilgilerini çek (takım için)
        self.oyuncu_detay = oyuncu_detay_bilgi(oyuncu_id)
        
        # Sezon istatistikleri
        self.sezon_stats, self.gercek_sezon = sezon_istatistikleri_cek(oyuncu_id)
        if self.sezon_stats is None or self.sezon_stats.empty:
            print("❌ Sezon istatistikleri bulunamadı!")
            return False
        
        # Maç logları
        self.mac_loglar = son_maclar(oyuncu_id, sezon=self.gercek_sezon)
        if self.mac_loglar is None or self.mac_loglar.empty:
            print("❌ Maç logları bulunamadı!")
            return False
        
        return True
    
    def hesapla_ortalama(self):
        """Sezon ortalamasını hesaplar"""
        stats = self.sezon_stats.iloc[0]
        mac_sayisi = stats['GP']
        
        if mac_sayisi == 0:
            return 0
        
        if self.analiz_tipi == 'SAR':
            # Sayı + Asist + Ribaund
            pts = stats['PTS'] / mac_sayisi
            ast = stats['AST'] / mac_sayisi
            reb = stats['REB'] / mac_sayisi
            return pts + ast + reb
        elif self.analiz_tipi == 'PTS':
            return stats['PTS'] / mac_sayisi
        elif self.analiz_tipi == 'AST':
            return stats['AST'] / mac_sayisi
        elif self.analiz_tipi == 'REB':
            return stats['REB'] / mac_sayisi
        else:
            return 0
    
    def hesapla_mac_basari_orani(self):
        """Her maçta barajı geçme oranını hesaplar (TÜM SEZON)"""
        basarili_maclar = 0
        toplam_maclar = len(self.mac_loglar)
        
        for idx, mac in self.mac_loglar.iterrows():
            if self.analiz_tipi == 'SAR':
                deger = mac['PTS'] + mac['AST'] + mac['REB']
            elif self.analiz_tipi == 'PTS':
                deger = mac['PTS']
            elif self.analiz_tipi == 'AST':
                deger = mac['AST']
            elif self.analiz_tipi == 'REB':
                deger = mac['REB']
            else:
                deger = 0
            
            if deger >= self.baraj_limit:
                basarili_maclar += 1
        
        basari_orani = (basarili_maclar / toplam_maclar * 100) if toplam_maclar > 0 else 0
        return basari_orani, basarili_maclar, toplam_maclar
    
    def hesapla_son_5_mac_basari_orani(self):
        """Son 5 maçta barajı geçme oranını hesaplar"""
        son_5 = self.mac_loglar.head(5)
        basarili_maclar = 0
        toplam_maclar = len(son_5)
        
        for idx, mac in son_5.iterrows():
            if self.analiz_tipi == 'SAR':
                deger = mac['PTS'] + mac['AST'] + mac['REB']
            elif self.analiz_tipi == 'PTS':
                deger = mac['PTS']
            elif self.analiz_tipi == 'AST':
                deger = mac['AST']
            elif self.analiz_tipi == 'REB':
                deger = mac['REB']
            else:
                deger = 0
            
            if deger >= self.baraj_limit:
                basarili_maclar += 1
        
        basari_orani = (basarili_maclar / toplam_maclar * 100) if toplam_maclar > 0 else 0
        return basari_orani, basarili_maclar, toplam_maclar
    
    def hesapla_son_5_mac_ortalama(self):
        """Son 5 maçın ortalamasını hesaplar"""
        son_5 = self.mac_loglar.head(5)
        
        if self.analiz_tipi == 'SAR':
            degerler = son_5['PTS'] + son_5['AST'] + son_5['REB']
        elif self.analiz_tipi == 'PTS':
            degerler = son_5['PTS']
        elif self.analiz_tipi == 'AST':
            degerler = son_5['AST']
        elif self.analiz_tipi == 'REB':
            degerler = son_5['REB']
        else:
            degerler = pd.Series([0])
        
        return degerler.mean()
    
    def hesapla_ev_deplasman_fark(self):
        """Ev ve deplasman performans farkını hesaplar"""
        ev_maclar = self.mac_loglar[self.mac_loglar['MATCHUP'].str.contains('vs.', na=False)]
        dep_maclar = self.mac_loglar[self.mac_loglar['MATCHUP'].str.contains('@', na=False)]
        
        if self.analiz_tipi == 'SAR':
            ev_ort = (ev_maclar['PTS'] + ev_maclar['AST'] + ev_maclar['REB']).mean() if len(ev_maclar) > 0 else 0
            dep_ort = (dep_maclar['PTS'] + dep_maclar['AST'] + dep_maclar['REB']).mean() if len(dep_maclar) > 0 else 0
        elif self.analiz_tipi == 'PTS':
            ev_ort = ev_maclar['PTS'].mean() if len(ev_maclar) > 0 else 0
            dep_ort = dep_maclar['PTS'].mean() if len(dep_maclar) > 0 else 0
        elif self.analiz_tipi == 'AST':
            ev_ort = ev_maclar['AST'].mean() if len(ev_maclar) > 0 else 0
            dep_ort = dep_maclar['AST'].mean() if len(dep_maclar) > 0 else 0
        elif self.analiz_tipi == 'REB':
            ev_ort = ev_maclar['REB'].mean() if len(ev_maclar) > 0 else 0
            dep_ort = dep_maclar['REB'].mean() if len(dep_maclar) > 0 else 0
        else:
            ev_ort = dep_ort = 0
        
        return ev_ort, dep_ort, ev_ort - dep_ort
    
    def hesapla_takim_tempo_etkisi(self, takim_adi):
        """Takımın tempo etkisini hesaplar"""
        try:
            takim = takim_bul(takim_adi)
            if not takim:
                print(f"⚠️ Takım bulunamadı: {takim_adi}")
                return None, None
            
            takim_id = takim['id']
            
            # Takım advanced stats (Pace için)
            advanced_stats = takim_advanced_stats_cek(takim_id)
            if advanced_stats is not None and not advanced_stats.empty:
                pace = advanced_stats['PACE'] if 'PACE' in advanced_stats else None
                off_rating = advanced_stats['OFF_RATING'] if 'OFF_RATING' in advanced_stats else None
                return pace, off_rating
            
            print(f"⚠️ Advanced stats bulunamadı: {takim_adi}")
            return None, None
        except Exception as e:
            print(f"⚠️ Takım tempo bilgisi alınamadı: {e}")
            return None, None
    
    def hesapla_standart_sapma(self):
        """Performans tutarlılığını ölçer (standart sapma)"""
        if self.analiz_tipi == 'SAR':
            degerler = self.mac_loglar['PTS'] + self.mac_loglar['AST'] + self.mac_loglar['REB']
        elif self.analiz_tipi == 'PTS':
            degerler = self.mac_loglar['PTS']
        elif self.analiz_tipi == 'AST':
            degerler = self.mac_loglar['AST']
        elif self.analiz_tipi == 'REB':
            degerler = self.mac_loglar['REB']
        else:
            degerler = pd.Series([0])
        
        return degerler.std()
    
    def hesapla_dakika_faktoru(self):
        """Oyuncunun sahada kalma süresini değerlendirir"""
        stats = self.sezon_stats.iloc[0]
        mac_sayisi = stats['GP']
        ortalama_dakika = stats['MIN'] / mac_sayisi if mac_sayisi > 0 else 0
        
        # Dakika faktörü: 30+ dakika ideal
        if ortalama_dakika >= 32:
            return "Yüksek", ortalama_dakika
        elif ortalama_dakika >= 25:
            return "Orta", ortalama_dakika
        else:
            return "Düşük", ortalama_dakika
    
    def risk_degerlendirmesi(self, final_tahmin, basari_orani, son_5_basari, std_sapma, ev_dep_fark=0):
        """
        GELİŞMİŞ RİSK DEĞERLENDİRMESİ (Sıkılaştırılmış)
        - Final tahmin + tutarlılık + son form + ev/deplasman faktörü
        """
        fark = final_tahmin - self.baraj_limit
        
        # 1. TUTARLILIK FAKTÖRÜ (Std Sapma)
        tutarlilik_katsayi = 1.0
        tutarlilik_uyari = ""
        if std_sapma > 10:
            tutarlilik_katsayi = 0.6  # Çok değişken → Daha katı
            tutarlilik_uyari = " (Çok Değişken!)"
        elif std_sapma > 7:
            tutarlilik_katsayi = 0.75  # Orta değişkenlik
            tutarlilik_uyari = " (Değişken)"
        elif std_sapma > 5:
            tutarlilik_katsayi = 0.9  # Az değişken
        elif std_sapma < 4:
            tutarlilik_katsayi = 1.15  # Çok tutarlı → Bonus
            tutarlilik_uyari = " (Tutarlı)"
        
        # 2. FORM FAKTÖRÜ (Son 5 maç daha önemli)
        form_katsayi = (son_5_basari * 0.7 + basari_orani * 0.3) / 100
        
        # 3. EV/DEPLASMAN FAKTÖRÜ (Artık kullanıcı seçiyor, ceza kaldırıldı)
        # Ev/deplasman bilgisi varsa zaten doğru ortalama kullanılıyor
        
        # 4. BAŞARI ORANI CEZASI
        # %60'ın altı başarı = ceza
        if son_5_basari < 60:
            basari_cezasi = (60 - son_5_basari) * 0.1
            fark -= basari_cezasi
        
        # 5. FINAL GÜVEN SKORU
        guven_skoru = int((fark / self.baraj_limit * 100) * tutarlilik_katsayi * form_katsayi)
        guven_skoru = max(0, min(100, guven_skoru))
        
        # 6. RİSK KATEGORİSİ (SIKIŞTIRILMIŞ)
        
        # ÇOK GÜVENLİ: Fark ≥5, Son 5 ≥80%, Std <6
        if fark >= 5 and son_5_basari >= 80 and std_sapma < 6:
            return "✅ ÇOK GÜVENLİ - GİR!" + tutarlilik_uyari, "Yeşil", max(85, guven_skoru)
        
        # GÜVENLİ: Fark ≥4, Son 5 ≥70%, Std <7
        elif fark >= 4 and son_5_basari >= 70 and std_sapma < 7:
            return "✅ GÜVENLİ - GİR!" + tutarlilik_uyari, "Yeşil", max(75, guven_skoru)
        
        # ORTA RİSK: Fark ≥3, Son 5 ≥60%
        elif fark >= 3 and son_5_basari >= 60:
            if std_sapma > 7:
                return "⚠️ ORTA RİSK" + tutarlilik_uyari, "Sarı", max(60, guven_skoru)
            return "⚠️ ORTA RİSK - DİKKATLİ" + tutarlilik_uyari, "Sarı", max(65, guven_skoru)
        
        # YÜKSEK RİSK: Fark ≥1.5, Son 5 ≥50%
        elif fark >= 1.5 and son_5_basari >= 50:
            return "⚠️ YÜKSEK RİSK" + tutarlilik_uyari, "Turuncu", max(50, guven_skoru)
        
        # RİSKLİ: Fark ≥0, Son 5 ≥40%
        elif fark >= 0 and son_5_basari >= 40:
            return "❌ RİSKLİ - DİKKATLİ" + tutarlilik_uyari, "Turuncu", max(40, guven_skoru)
        
        # UZAK DUR: Diğer durumlar
        else:
            return "❌ UZAK DUR!" + tutarlilik_uyari, "Kırmızı", min(30, guven_skoru)
    
    def onerilen_baraj_hesapla(self, ortalama, std_sapma):
        """Güvenli baraj limiti önerir"""
        # Standart sapmayı dikkate alarak güvenli limit
        guvenli_limit = ortalama - (std_sapma * 0.5)
        return max(0, guvenli_limit)
    
    def analiz_yap(self):
        """Tam analiz yapar ve sonuç üretir"""
        # Veri çek
        if not self.veri_cek():
            return None
        
        # Temel hesaplamalar
        sezon_ortalama = self.hesapla_ortalama()
        basari_orani, basarili, toplam = self.hesapla_mac_basari_orani()
        son_5_basari_orani, son_5_basarili, son_5_toplam = self.hesapla_son_5_mac_basari_orani()
        son_5_ortalama = self.hesapla_son_5_mac_ortalama()
        std_sapma = self.hesapla_standart_sapma()
        dakika_seviye, ortalama_dakika = self.hesapla_dakika_faktoru()
        
        # YENİ: Ev/Deplasman analizi
        ev_ort, dep_ort, ev_dep_fark = self.hesapla_ev_deplasman_fark()
        
        # YENİ: Takım tempo etkisi
        takim_adi = None
        if self.oyuncu_detay is not None and not self.oyuncu_detay.empty:
            if 'TEAM_NAME' in self.oyuncu_detay.columns:
                takim_adi = str(self.oyuncu_detay['TEAM_NAME'].values[0])
            elif 'TEAM_ABBREVIATION' in self.oyuncu_detay.columns:
                takim_adi = str(self.oyuncu_detay['TEAM_ABBREVIATION'].values[0])
        
        takim_pace, takim_off_rating = None, None
        if takim_adi and takim_adi != 'nan':
            takim_pace, takim_off_rating = self.hesapla_takim_tempo_etkisi(takim_adi)
        
        # YENİ: Ev/Deplasman Bazlı Tahmin
        if self.ev_deplasman == 'Ev':
            # Ev maçı → Ev ortalamasını kullan
            agirlikli_ortalama = (ev_ort * 0.7) + (sezon_ortalama * 0.3)
            print(f"🏠 EV MAÇI TESPİT EDİLDİ → Ev ortalaması ağırlıklı kullanılıyor")
        elif self.ev_deplasman == 'Deplasman':
            # Deplasman maçı → Deplasman ortalamasını kullan
            agirlikli_ortalama = (dep_ort * 0.7) + (sezon_ortalama * 0.3)
            print(f"✈️ DEPLASMAN MAÇI TESPİT EDİLDİ → Deplasman ortalaması ağırlıklı kullanılıyor")
        else:
            # Bilinmiyor → Sezon + Son 5 maç
            agirlikli_ortalama = (sezon_ortalama * 0.6) + (son_5_ortalama * 0.4)
        
        # Tempo bonusu
        tempo_bonus = 0
        if takim_pace and takim_pace > 100:
            tempo_bonus = (takim_pace - 100) * 0.3  # Hızlı tempo = daha fazla istatistik
        
        # Final tahmin (ağırlıklı + tempo bonusu)
        final_tahmin = agirlikli_ortalama + tempo_bonus
        
        # YENİ: Gelişmiş risk değerlendirmesi (final tahmin + son 5 maç + tutarlılık + ev/dep)
        risk, renk, guven_skoru = self.risk_degerlendirmesi(
            final_tahmin, 
            basari_orani, 
            son_5_basari_orani, 
            std_sapma,
            ev_dep_fark
        )
        
        onerilen_baraj = self.onerilen_baraj_hesapla(final_tahmin, std_sapma)
        
        # YENİ: Garbage Time Analizi
        garbage_time_uyari = None
        if self.mac_orani:
            print(f"\n{'─'*70}")
            print(f"🚨 GARBAGE TIME ANALİZİ")
            print(f"{'─'*70}")
            print(f"Maç Oranı: {self.mac_orani:.2f}")
            
            garbage_result = uygula_garbage_time_penalty(
                final_tahmin=final_tahmin,
                guven_skoru=guven_skoru,
                oran=self.mac_orani
            )
            
            if garbage_result['penalty_applied']:
                print(f"⚠️ GARBAGE TIME RİSKİ TESPİT EDİLDİ!")
                print(f"Penalty: %{int(garbage_result['penalty_factor']*100)}")
                print(f"Orijinal Tahmin: {garbage_result['original_tahmin']:.1f}")
                print(f"Düzeltilmiş Tahmin: {garbage_result['adjusted_tahmin']:.1f}")
                print(f"Orijinal Güven: %{garbage_result['original_guven']}")
                print(f"Düzeltilmiş Güven: %{garbage_result['adjusted_guven']}")
                print(f"Sebep: {garbage_result['penalty_info']['reason']}")
                
                # Değerleri güncelle
                final_tahmin = garbage_result['adjusted_tahmin']
                guven_skoru = garbage_result['adjusted_guven']
                garbage_time_uyari = garbage_result['penalty_info']['recommendation']
                
                # Risk'i yeniden değerlendir
                risk, renk, guven_skoru = self.risk_degerlendirmesi(
                    final_tahmin, 
                    basari_orani, 
                    son_5_basari_orani, 
                    std_sapma,
                    ev_dep_fark
                )
            else:
                print(f"✅ Garbage time riski düşük")
                print(f"Sebep: {garbage_result['penalty_info']['reason']}")
        
        # Sonuçları yazdır
        print(f"\n{'='*70}")
        print(f"📊 GELİŞMİŞ ANALİZ SONUÇLARI")
        print(f"{'='*70}\n")
        
        print(f"🎯 Oyuncu: {self.oyuncu_data['full_name']}")
        print(f"📅 Sezon: {self.gercek_sezon}")
        print(f"🎮 Toplam Maç: {toplam}")
        print(f"⏱️ Ortalama Dakika: {ortalama_dakika:.1f} ({dakika_seviye})")
        
        print(f"\n{'─'*70}")
        print(f"📈 PERFORMANS İSTATİSTİKLERİ")
        print(f"{'─'*70}")
        print(f"Sezon Ortalaması: {sezon_ortalama:.1f}")
        print(f"Son 5 Maç Ortalaması: {son_5_ortalama:.1f}")
        print(f"Ağırlıklı Ortalama (60% Sezon + 40% Son 5): {agirlikli_ortalama:.1f}")
        print(f"Standart Sapma (Tutarlılık): {std_sapma:.1f}")
        
        print(f"\n{'─'*70}")
        print(f"🏠 EV/DEPLASMAN ANALİZİ")
        print(f"{'─'*70}")
        print(f"Ev Ortalaması: {ev_ort:.1f}")
        print(f"Deplasman Ortalaması: {dep_ort:.1f}")
        print(f"Fark: {ev_dep_fark:+.1f} ({'Evde daha iyi' if ev_dep_fark > 0 else 'Deplasanda daha iyi' if ev_dep_fark < 0 else 'Dengeli'})")
        
        if takim_pace:
            print(f"\n{'─'*70}")
            print(f"⚡ TAKIM TEMPO ETKİSİ")
            print(f"{'─'*70}")
            print(f"Takım Pace: {takim_pace:.1f} ({'Hızlı' if takim_pace > 100 else 'Yavaş' if takim_pace < 98 else 'Normal'})")
            if takim_off_rating:
                print(f"Offensive Rating: {takim_off_rating:.1f}")
            print(f"Tempo Bonusu: +{tempo_bonus:.1f}")
            print(f"Final Tahmin: {final_tahmin:.1f}")
        
        print(f"\n{'─'*70}")
        print(f"🎯 BARAJ ANALİZİ")
        print(f"{'─'*70}")
        print(f"Kullanıcı Barajı: {self.baraj_limit}+")
        print(f"Sezon Başarı Oranı: %{basari_orani:.1f} ({basarili}/{toplam} maç)")
        print(f"Son 5 Maç Başarı: %{son_5_basari_orani:.1f} ({son_5_basarili}/{son_5_toplam} maç)")
        print(f"Final Tahmin - Baraj Farkı: {final_tahmin - self.baraj_limit:+.1f}")
        
        print(f"\n{'='*70}")
        print(f"🎲 SONUÇ: {risk}")
        print(f"{'='*70}")
        print(f"Güven Skoru: %{guven_skoru}")
        print(f"Risk Seviyesi: {renk}")
        print(f"Önerilen Güvenli Baraj: {onerilen_baraj:.1f}+")
        
        # Detaylı açıklama
        print(f"\n{'─'*70}")
        print(f"💡 AÇIKLAMA")
        print(f"{'─'*70}")
        
        if guven_skoru >= 80:
            print(f"✅ Bu oyuncu için {self.baraj_limit}+ barajı çok güvenli görünüyor.")
            print(f"   Sezon ortalaması {sezon_ortalama:.1f} ve maçların %{basari_orani:.0f}'inde")
            print(f"   barajı geçiyor. Yüksek kazanma olasılığı var.")
        elif guven_skoru >= 60:
            print(f"⚠️ Bu baraj orta riskli. Oyuncu ortalaması {sezon_ortalama:.1f} ve")
            print(f"   maçların %{basari_orani:.0f}'inde barajı geçiyor.")
            print(f"   Daha güvenli bir seçenek için {onerilen_baraj:.0f}+ barajını düşünebilirsiniz.")
        else:
            print(f"❌ Bu baraj riskli! Oyuncu ortalaması {sezon_ortalama:.1f} ve")
            print(f"   sadece maçların %{basari_orani:.0f}'inde barajı geçiyor.")
            print(f"   Bu bahisten uzak durmanız önerilir.")
        
        if std_sapma > 8:
            print(f"\n⚠️ DİKKAT: Oyuncunun performansı tutarsız (yüksek standart sapma).")
            print(f"   Bazı maçlarda çok iyi, bazılarında düşük performans gösteriyor.")
        
        if dakika_seviye == "Düşük":
            print(f"\n⚠️ DİKKAT: Oyuncu az dakika alıyor ({ortalama_dakika:.1f} dk).")
            print(f"   Bu durum performansı olumsuz etkileyebilir.")
        
        print(f"\n{'='*70}\n")
        
        # Ek bilgiler
        stats = self.sezon_stats.iloc[0]
        mac_sayisi = stats['GP']
        ortalama_dakika = stats['MIN'] / mac_sayisi if mac_sayisi > 0 else 0
        
        # Takım bilgisi - Takım kısa adlarını tam adlara çevir
        takim_map = {
            'PHI': 'Philadelphia 76ers', '76ers': 'Philadelphia 76ers',
            'LAL': 'Los Angeles Lakers', 'Lakers': 'Los Angeles Lakers',
            'BOS': 'Boston Celtics', 'Celtics': 'Boston Celtics',
            'GSW': 'Golden State Warriors', 'Warriors': 'Golden State Warriors',
            'MIL': 'Milwaukee Bucks', 'Bucks': 'Milwaukee Bucks',
            'DEN': 'Denver Nuggets', 'Nuggets': 'Denver Nuggets',
            'PHX': 'Phoenix Suns', 'Suns': 'Phoenix Suns',
            'MIA': 'Miami Heat', 'Heat': 'Miami Heat',
            'DAL': 'Dallas Mavericks', 'Mavericks': 'Dallas Mavericks',
            'MEM': 'Memphis Grizzlies', 'Grizzlies': 'Memphis Grizzlies',
            'CLE': 'Cleveland Cavaliers', 'Cavaliers': 'Cleveland Cavaliers',
            'SAC': 'Sacramento Kings', 'Kings': 'Sacramento Kings',
            'NYK': 'New York Knicks', 'Knicks': 'New York Knicks',
            'BKN': 'Brooklyn Nets', 'Nets': 'Brooklyn Nets',
            'ATL': 'Atlanta Hawks', 'Hawks': 'Atlanta Hawks',
            'CHI': 'Chicago Bulls', 'Bulls': 'Chicago Bulls',
            'TOR': 'Toronto Raptors', 'Raptors': 'Toronto Raptors',
            'MIN': 'Minnesota Timberwolves', 'Timberwolves': 'Minnesota Timberwolves',
            'NOP': 'New Orleans Pelicans', 'Pelicans': 'New Orleans Pelicans',
            'LAC': 'LA Clippers', 'Clippers': 'LA Clippers',
            'OKC': 'Oklahoma City Thunder', 'Thunder': 'Oklahoma City Thunder',
            'POR': 'Portland Trail Blazers', 'Trail Blazers': 'Portland Trail Blazers',
            'UTA': 'Utah Jazz', 'Jazz': 'Utah Jazz',
            'SAS': 'San Antonio Spurs', 'Spurs': 'San Antonio Spurs',
            'ORL': 'Orlando Magic', 'Magic': 'Orlando Magic',
            'IND': 'Indiana Pacers', 'Pacers': 'Indiana Pacers',
            'WAS': 'Washington Wizards', 'Wizards': 'Washington Wizards',
            'DET': 'Detroit Pistons', 'Pistons': 'Detroit Pistons',
            'CHA': 'Charlotte Hornets', 'Hornets': 'Charlotte Hornets',
            'HOU': 'Houston Rockets', 'Rockets': 'Houston Rockets'
        }
        
        takim = "N/A"
        pozisyon = "N/A"
        if self.oyuncu_detay is not None and not self.oyuncu_detay.empty:
            # Tüm olası takım kolonlarını kontrol et
            takim_raw = None
            if 'TEAM_NAME' in self.oyuncu_detay.columns:
                takim_raw = str(self.oyuncu_detay['TEAM_NAME'].values[0])
            elif 'TEAM_ABBREVIATION' in self.oyuncu_detay.columns:
                takim_raw = str(self.oyuncu_detay['TEAM_ABBREVIATION'].values[0])
            
            # Takım adını map'ten al, yoksa olduğu gibi kullan
            if takim_raw and takim_raw != 'nan':
                takim = takim_map.get(takim_raw, takim_raw)
            
            pozisyon = self.oyuncu_detay['POSITION'].values[0] if 'POSITION' in self.oyuncu_detay.columns else "N/A"
        
        return {
            'oyuncu': self.oyuncu_data['full_name'],
            'takim': takim,
            'pozisyon': pozisyon,
            'sezon_ortalama': sezon_ortalama,
            'son_5_ortalama': son_5_ortalama,
            'agirlikli_ortalama': agirlikli_ortalama,
            'final_tahmin': final_tahmin,
            'baraj': self.baraj_limit,
            'basari_orani': basari_orani,
            'son_5_basari_orani': son_5_basari_orani,
            'son_5_basarili': son_5_basarili,
            'son_5_toplam': son_5_toplam,
            'risk': risk,
            'guven_skoru': guven_skoru,
            'onerilen_baraj': onerilen_baraj,
            'toplam_mac': toplam,
            'basarili_mac': basarili,
            'ortalama_dakika': ortalama_dakika,
            'sezon': self.gercek_sezon,
            'ev_ortalama': ev_ort,
            'deplasman_ortalama': dep_ort,
            'ev_dep_fark': ev_dep_fark,
            'takim_pace': takim_pace,
            'takim_off_rating': takim_off_rating,
            'tempo_bonus': tempo_bonus,
            'std_sapma': std_sapma,
            'garbage_time_uyari': garbage_time_uyari,
            'mac_orani': self.mac_orani
        }


# Test için
if __name__ == "__main__":
    print("🚀 NBA BARAJ ANALİZ SİSTEMİ TEST\n")
    
    # Örnek 1: LeBron James - 40+ S+A+R
    analiz1 = BarajAnaliz("LeBron James", 40, 'SAR')
    sonuc1 = analiz1.analiz_yap()
    
    print("\n" + "="*70)
    print("Başka bir oyuncu test etmek için:")
    print("analiz = BarajAnaliz('Oyuncu İsmi', baraj_limiti, 'SAR')")
    print("analiz.analiz_yap()")
    print("="*70)

