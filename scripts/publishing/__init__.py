from .meta import publish_facebook, publish_instagram
from .tiktok import publish as publish_tiktok
from .youtube import publish as publish_youtube

PUBLISHERS = {
    "youtube": publish_youtube,
    "tiktok": publish_tiktok,
    "instagram": publish_instagram,
    "facebook": publish_facebook,
}

__all__ = ["PUBLISHERS"]
