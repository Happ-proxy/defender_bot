from cachetools import TTLCache

admin_replies = TTLCache(maxsize=1000, ttl=360)
