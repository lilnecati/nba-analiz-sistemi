"""
NBA Analiz Sistemi - Basit Veritabanı
Analiz geçmişini saklar (gelecek özellik için hazır)
"""

import sqlite3
import json
from datetime import datetime

class AnalizDB:
    def __init__(self, db_file='analiz.db'):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        """Veritabanı tablolarını oluştur"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Analiz geçmişi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analiz_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici TEXT NOT NULL,
                oyuncu_isim TEXT NOT NULL,
                baraj INTEGER NOT NULL,
                analiz_tipi TEXT NOT NULL,
                sezon_ortalama REAL,
                basari_orani REAL,
                risk TEXT,
                guven_skoru INTEGER,
                onerilen_baraj REAL,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analiz_kaydet(self, kullanici, oyuncu_isim, baraj, analiz_tipi, sonuc):
        """Analiz sonucunu veritabanına kaydet"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analiz_gecmisi 
            (kullanici, oyuncu_isim, baraj, analiz_tipi, sezon_ortalama, 
             basari_orani, risk, guven_skoru, onerilen_baraj)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kullanici,
            oyuncu_isim,
            baraj,
            analiz_tipi,
            sonuc.get('sezon_ortalama'),
            sonuc.get('basari_orani'),
            sonuc.get('risk'),
            sonuc.get('guven_skoru'),
            sonuc.get('onerilen_baraj')
        ))
        
        conn.commit()
        conn.close()
    
    def gecmis_getir(self, kullanici, limit=10):
        """Kullanıcının analiz geçmişini getir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analiz_gecmisi 
            WHERE kullanici = ?
            ORDER BY tarih DESC
            LIMIT ?
        ''', (kullanici, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows

# Test
if __name__ == "__main__":
    db = AnalizDB()
    print("✅ Veritabanı oluşturuldu: analiz.db")

