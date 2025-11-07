"""
NBA API Wrapper
Retry mekanizması, rate limiting ve cache ile optimize edilmiş API wrapper
"""

import time
from functools import wraps
from cache_manager import cache

class APIRateLimiter:
    """API rate limiting sınıfı"""
    
    def __init__(self, min_interval=0.3):  # 0.6'dan 0.3'e düşürüldü
        """
        Args:
            min_interval: API çağrıları arasındaki minimum süre (saniye)
        """
        self.min_interval = min_interval
        self.last_call = 0
    
    def wait(self):
        """Gerekirse bekle"""
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


# Global rate limiter
rate_limiter = APIRateLimiter()


def with_retry(max_retries=2, delay=0.5, backoff=1.5):
    """
    Retry decorator - API hatalarında otomatik yeniden deneme
    
    Args:
        max_retries: Maksimum deneme sayısı
        delay: İlk deneme arası bekleme süresi (saniye)
        backoff: Her denemede bekleme süresini artırma katsayısı
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ValueError, SyntaxError, KeyError) as e:
                    print(f"⚠️  API veri formatı hatası (deneme {attempt + 1}/{max_retries}): {str(e)}")
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    continue
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"⚠️ Deneme {attempt + 1}/{max_retries} başarısız: {e}")
                        print(f"   {current_delay:.1f} saniye sonra tekrar denenecek...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"❌ Tüm denemeler başarısız oldu: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


def with_cache(cache_key_func=None, cache_duration_hours=6):
    """
    Cache decorator - API sonuçlarını önbelleğe al
    
    Args:
        cache_key_func: Cache key oluşturma fonksiyonu
        cache_duration_hours: Cache süresi (saat)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache key oluştur
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default: fonksiyon adı + argümanlar
                cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Cache'den kontrol et
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                print(f"✅ Cache'den alındı: {cache_key[:50]}...")
                return cached_data
            
            # API'den çek
            print(f"🔄 API'den çekiliyor: {cache_key[:50]}...")
            result = func(*args, **kwargs)
            
            # Cache'e kaydet
            if result is not None:
                cache.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


def with_rate_limit(func):
    """Rate limiting decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter.wait()
        return func(*args, **kwargs)
    return wrapper


# Kombine decorator: Cache + Retry + Rate Limit
def api_call(cache_key_func=None, max_retries=3, cache_duration_hours=6):
    """
    Tüm optimizasyonları içeren decorator
    
    Kullanım:
        @api_call(cache_key_func=lambda player_id: f"player_{player_id}")
        def get_player_stats(player_id):
            # API çağrısı
            pass
    """
    def decorator(func):
        # Önce cache, sonra retry, en son rate limit
        func = with_cache(cache_key_func, cache_duration_hours)(func)
        func = with_retry(max_retries)(func)
        func = with_rate_limit(func)
        return func
    return decorator


if __name__ == "__main__":
    print("🧪 API Wrapper Test\n")
    
    # Test 1: Retry mekanizması
    @with_retry(max_retries=3, delay=0.5)
    def test_failing_api():
        """Her zaman hata veren test fonksiyonu"""
        raise Exception("API hatası!")
    
    print("Test 1: Retry mekanizması")
    try:
        test_failing_api()
    except:
        print("✅ Retry mekanizması çalışıyor\n")
    
    # Test 2: Cache mekanizması
    @with_cache(cache_key_func=lambda x: f"test_{x}")
    def test_cached_api(value):
        """Cache'lenebilir test fonksiyonu"""
        print(f"  API çağrısı yapılıyor: {value}")
        return {"value": value, "timestamp": time.time()}
    
    print("Test 2: Cache mekanizması")
    print("İlk çağrı:")
    result1 = test_cached_api("test_value")
    print(f"Sonuç: {result1}\n")
    
    print("İkinci çağrı (cache'den):")
    result2 = test_cached_api("test_value")
    print(f"Sonuç: {result2}\n")
    
    # Test 3: Rate limiting
    @with_rate_limit
    def test_rate_limited_api():
        """Rate limited test fonksiyonu"""
        print(f"  API çağrısı: {time.time():.2f}")
        return True
    
    print("Test 3: Rate limiting")
    for i in range(3):
        test_rate_limited_api()
    print("✅ Rate limiting çalışıyor\n")
    
    # Test 4: Kombine decorator
    @api_call(cache_key_func=lambda x: f"combined_{x}", max_retries=2)
    def test_combined_api(value):
        """Tüm optimizasyonları kullanan test fonksiyonu"""
        print(f"  Combined API çağrısı: {value}")
        return {"value": value, "status": "success"}
    
    print("Test 4: Kombine decorator")
    print("İlk çağrı:")
    result = test_combined_api("test")
    print(f"Sonuç: {result}\n")
    
    print("İkinci çağrı (cache'den):")
    result = test_combined_api("test")
    print(f"Sonuç: {result}\n")

