"""
NBA Advanced Statistics Calculator
Gelişmiş istatistikleri hesaplayan yardımcı fonksiyonlar
"""

import pandas as pd
import numpy as np

def hesapla_true_shooting_pct(pts, fga, fta):
    """
    True Shooting % (Gerçek Şut Yüzdesi)
    Formula: TS% = PTS / (2 * (FGA + 0.44 * FTA))
    """
    if fga + (0.44 * fta) == 0:
        return 0
    return pts / (2 * (fga + 0.44 * fta))

def hesapla_effective_fg_pct(fgm, fg3m, fga):
    """
    Effective Field Goal % (Efektif Şut Yüzdesi)
    Formula: eFG% = (FGM + 0.5 * FG3M) / FGA
    """
    if fga == 0:
        return 0
    return (fgm + 0.5 * fg3m) / fga

def hesapla_assist_turnover_ratio(ast, tov):
    """
    Assist to Turnover Ratio (Asist/Top Kaybı Oranı)
    Formula: AST/TO = AST / TOV
    """
    if tov == 0:
        return ast if ast > 0 else 0
    return ast / tov

def kontrol_double_double(pts, reb, ast, stl, blk):
    """
    Double-Double kontrolü
    En az 2 kategoride 10+ olmalı
    """
    categories = [pts, reb, ast, stl, blk]
    double_count = sum(1 for cat in categories if cat >= 10)
    return double_count >= 2

def kontrol_triple_double(pts, reb, ast, stl, blk):
    """
    Triple-Double kontrolü
    En az 3 kategoride 10+ olmalı
    """
    categories = [pts, reb, ast, stl, blk]
    triple_count = sum(1 for cat in categories if cat >= 10)
    return triple_count >= 3

def hesapla_usage_rate_basit(fga, fta, tov, team_fga, team_fta, team_tov, minutes, team_minutes):
    """
    Basitleştirilmiş Usage Rate
    Formula: 100 * ((FGA + 0.44 * FTA + TOV) * (Team_MIN / 5)) / (MIN * (Team_FGA + 0.44 * Team_FTA + Team_TOV))
    
    Not: Gerçek Usage Rate daha karmaşık, bu basitleştirilmiş versiyon
    """
    if minutes == 0 or team_minutes == 0:
        return 0
    
    player_possessions = fga + 0.44 * fta + tov
    team_possessions = team_fga + 0.44 * team_fta + team_tov
    
    if team_possessions == 0:
        return 0
    
    return 100 * ((player_possessions * (team_minutes / 5)) / (minutes * team_possessions))

def mac_istatistikleri_zenginlestir(mac_df):
    """
    Maç DataFrame'ine advanced stats ekler
    
    Args:
        mac_df: playergamelog DataFrame
    
    Returns:
        Zenginleştirilmiş DataFrame
    """
    df = mac_df.copy()
    
    # True Shooting %
    df['TS_PCT'] = df.apply(
        lambda row: hesapla_true_shooting_pct(row['PTS'], row['FGA'], row['FTA']),
        axis=1
    )
    
    # Effective FG %
    df['EFG_PCT'] = df.apply(
        lambda row: hesapla_effective_fg_pct(row['FGM'], row['FG3M'], row['FGA']),
        axis=1
    )
    
    # Assist/Turnover Ratio
    df['AST_TOV_RATIO'] = df.apply(
        lambda row: hesapla_assist_turnover_ratio(row['AST'], row['TOV']),
        axis=1
    )
    
    # Double-Double
    df['DOUBLE_DOUBLE'] = df.apply(
        lambda row: kontrol_double_double(row['PTS'], row['REB'], row['AST'], row['STL'], row['BLK']),
        axis=1
    )
    
    # Triple-Double
    df['TRIPLE_DOUBLE'] = df.apply(
        lambda row: kontrol_triple_double(row['PTS'], row['REB'], row['AST'], row['STL'], row['BLK']),
        axis=1
    )
    
    return df

def sezon_advanced_stats_hesapla(mac_df):
    """
    Sezon ortalaması advanced stats hesaplar
    
    Args:
        mac_df: Zenginleştirilmiş maç DataFrame
    
    Returns:
        Dictionary of advanced stats
    """
    if mac_df is None or mac_df.empty:
        return None
    
    # Zenginleştir
    df = mac_istatistikleri_zenginlestir(mac_df)
    
    total_games = len(df)
    
    stats = {
        # Temel istatistikler
        'total_games': total_games,
        'avg_min': df['MIN'].mean(),
        'avg_pts': df['PTS'].mean(),
        'avg_reb': df['REB'].mean(),
        'avg_oreb': df['OREB'].mean(),
        'avg_dreb': df['DREB'].mean(),
        'avg_ast': df['AST'].mean(),
        'avg_stl': df['STL'].mean(),
        'avg_blk': df['BLK'].mean(),
        'avg_tov': df['TOV'].mean(),
        'avg_pf': df['PF'].mean(),
        'avg_plus_minus': df['PLUS_MINUS'].mean(),
        
        # Şut yüzdeleri
        'avg_fg_pct': df['FG_PCT'].mean(),
        'avg_fg3_pct': df['FG3_PCT'].mean(),
        'avg_ft_pct': df['FT_PCT'].mean(),
        
        # Advanced stats
        'avg_ts_pct': df['TS_PCT'].mean(),
        'avg_efg_pct': df['EFG_PCT'].mean(),
        'avg_ast_tov_ratio': df['AST_TOV_RATIO'].mean(),
        
        # Double/Triple doubles
        'total_double_doubles': df['DOUBLE_DOUBLE'].sum(),
        'total_triple_doubles': df['TRIPLE_DOUBLE'].sum(),
        'double_double_pct': (df['DOUBLE_DOUBLE'].sum() / total_games * 100) if total_games > 0 else 0,
        
        # Şut dağılımı
        'avg_fgm': df['FGM'].mean(),
        'avg_fga': df['FGA'].mean(),
        'avg_fg3m': df['FG3M'].mean(),
        'avg_fg3a': df['FG3A'].mean(),
        'avg_ftm': df['FTM'].mean(),
        'avg_fta': df['FTA'].mean(),
        
        # 2 sayılık şutlar (hesaplanmış)
        'avg_fg2m': (df['FGM'] - df['FG3M']).mean(),
        'avg_fg2a': (df['FGA'] - df['FG3A']).mean(),
        'avg_fg2_pct': ((df['FGM'] - df['FG3M']) / (df['FGA'] - df['FG3A'])).mean() if (df['FGA'] - df['FG3A']).sum() > 0 else 0,
    }
    
    return stats

def format_advanced_stats_output(stats):
    """
    Advanced stats'leri güzel formatlı string olarak döndürür
    """
    if not stats:
        return "İstatistik bulunamadı"
    
    output = []
    output.append("\n" + "="*70)
    output.append("📊 GELİŞMİŞ İSTATİSTİKLER")
    output.append("="*70)
    
    output.append(f"\n🎮 Maç: {stats['total_games']}")
    output.append(f"⏱️ Dakika (Ort): {stats['avg_min']:.1f}")
    
    output.append(f"\n{'─'*70}")
    output.append("🎯 PUAN DAĞILIMI")
    output.append(f"{'─'*70}")
    output.append(f"Toplam: {stats['avg_pts']:.1f} puan/maç")
    output.append(f"Serbest Atış: {stats['avg_ftm']:.1f} ({stats['avg_ft_pct']*100:.0f}%)")
    output.append(f"2 Sayılık: {stats['avg_fg2m']:.1f} ({stats['avg_fg2_pct']*100:.0f}%)")
    output.append(f"3 Sayılık: {stats['avg_fg3m']:.1f} ({stats['avg_fg3_pct']*100:.0f}%)")
    
    output.append(f"\n{'─'*70}")
    output.append("🏀 RİBAUND")
    output.append(f"{'─'*70}")
    output.append(f"Toplam: {stats['avg_reb']:.1f}")
    output.append(f"Savunma: {stats['avg_dreb']:.1f}")
    output.append(f"Hücum: {stats['avg_oreb']:.1f}")
    
    output.append(f"\n{'─'*70}")
    output.append("📈 DİĞER")
    output.append(f"{'─'*70}")
    output.append(f"Asist: {stats['avg_ast']:.1f}")
    output.append(f"Top Kaybı: {stats['avg_tov']:.1f}")
    output.append(f"Top Çalma: {stats['avg_stl']:.1f}")
    output.append(f"Asist/Top Kaybı: {stats['avg_ast_tov_ratio']:.2f}")
    output.append(f"Blok: {stats['avg_blk']:.1f}")
    output.append(f"Faul: {stats['avg_pf']:.1f}")
    output.append(f"+/-: {stats['avg_plus_minus']:+.2f}")
    
    output.append(f"\n{'─'*70}")
    output.append("⚡ ADVANCED STATS")
    output.append(f"{'─'*70}")
    output.append(f"Gerçek Şut %: {stats['avg_ts_pct']*100:.1f}%")
    output.append(f"Efektif Şut %: {stats['avg_efg_pct']*100:.1f}%")
    
    output.append(f"\n{'─'*70}")
    output.append("🏆 EKSTRA")
    output.append(f"{'─'*70}")
    output.append(f"Double-Double: {stats['total_double_doubles']} ({stats['double_double_pct']:.0f}%)")
    output.append(f"Triple-Double: {stats['total_triple_doubles']}")
    
    return "\n".join(output)


if __name__ == "__main__":
    print("🧪 Advanced Stats Calculator Test\n")
    
    # Test verisi
    test_data = {
        'PTS': [25, 30, 20],
        'FGM': [10, 12, 8],
        'FGA': [20, 22, 18],
        'FG3M': [3, 4, 2],
        'FG3A': [8, 9, 7],
        'FTM': [2, 2, 2],
        'FTA': [3, 3, 3],
        'REB': [8, 12, 6],
        'OREB': [2, 3, 1],
        'DREB': [6, 9, 5],
        'AST': [7, 10, 5],
        'STL': [2, 1, 1],
        'BLK': [1, 2, 0],
        'TOV': [3, 2, 4],
        'PF': [2, 3, 2],
        'PLUS_MINUS': [5, 10, -3],
        'MIN': [35, 38, 32],
        'FG_PCT': [0.500, 0.545, 0.444],
        'FG3_PCT': [0.375, 0.444, 0.286],
        'FT_PCT': [0.667, 0.667, 0.667]
    }
    
    df = pd.DataFrame(test_data)
    
    print("Test 1: Advanced Stats Hesaplama")
    stats = sezon_advanced_stats_hesapla(df)
    print(format_advanced_stats_output(stats))
    
    print("\n✅ Test tamamlandı!")

