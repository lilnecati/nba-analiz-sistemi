"""
NBA API Cache Manager
Veri önbellekleme ve optimizasyon sistemi
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

class CacheManager:
    """API verilerini önbelleğe alan ve yöneten sınıf"""
    
    def __init__(self, cache_dir='cache', cache_duration_hours=6):
        """
        Args:
            cache_dir: Cache klasörü
            cache_duration_hours: Cache süresi (saat)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Cache klasörünü oluştur
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key):
        """Cache dosya yolunu döndürür"""
        # Güvenli dosya adı oluştur
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key):
        """Cache'den veri al"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Cache süresini kontrol et
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.cache_duration:
                # Cache süresi dolmuş
                cache_path.unlink()  # Dosyayı sil
                return None
            
            return cache_data['data']
        
        except Exception as e:
            print(f"⚠️ Cache okuma hatası: {e}")
            return None
    
    def set(self, key, data):
        """Cache'e veri kaydet"""
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"⚠️ Cache yazma hatası: {e}")
            return False
    
    def clear(self):
        """Tüm cache'i temizle"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            print("✅ Cache temizlendi!")
            return True
        except Exception as e:
            print(f"⚠️ Cache temizleme hatası: {e}")
            return False
    
    def clear_old(self):
        """Eski cache dosyalarını temizle"""
        try:
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cached_time = datetime.fromisoformat(cache_data['timestamp'])
                    if datetime.now() - cached_time > self.cache_duration:
                        cache_file.unlink()
                        count += 1
                except:
                    pass
            
            if count > 0:
                print(f"✅ {count} eski cache dosyası temizlendi!")
            return True
        
        except Exception as e:
            print(f"⚠️ Eski cache temizleme hatası: {e}")
            return False
    
    def get_stats(self):
        """Cache istatistiklerini döndür"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_files': len(cache_files),
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': str(self.cache_dir)
            }
        except Exception as e:
            print(f"⚠️ Cache istatistik hatası: {e}")
            return None


# Global cache instance
cache = CacheManager()


if __name__ == "__main__":
    print("🧪 Cache Manager Test\n")
    
    # Test 1: Veri kaydet
    print("Test 1: Veri kaydetme")
    test_data = {'name': 'LeBron James', 'points': 30}
    cache.set('test_player', test_data)
    print("✅ Veri kaydedildi\n")
    
    # Test 2: Veri oku
    print("Test 2: Veri okuma")
    cached = cache.get('test_player')
    print(f"Cached data: {cached}\n")
    
    # Test 3: İstatistikler
    print("Test 3: Cache istatistikleri")
    stats = cache.get_stats()
    print(f"Stats: {stats}\n")
    
    # Test 4: Temizle
    print("Test 4: Cache temizleme")
    cache.clear()

