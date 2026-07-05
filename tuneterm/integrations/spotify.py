import urllib.request
import json
import re
import logging
from typing import List, Dict

_log = logging.getLogger("tuneterm")

def get_spotify_metadata(url: str) -> List[Dict]:
    """
    Scrapes the Spotify embed page to extract track metadata.
    Returns a list of dicts with keys: 'title', 'artist', 'cover_url'
    """
    try:
        # Convert standard URL to embed URL
        if "/embed/" not in url:
            url = url.replace("spotify.com/", "spotify.com/embed/")
            
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if not m:
            _log.warning("[Spotify] No __NEXT_DATA__ found in embed page.")
            return []
            
        data = json.loads(m.group(1))
        props = data.get('props', {}).get('pageProps', {})
        
        # Depending on whether it's a track or playlist/album, the state path differs
        if 'state' in props:
            entity = props['state']['data']['entity']
        elif 'entity' in props:
            entity = props['entity']
        else:
            _log.warning("[Spotify] Neither 'state' nor 'entity' found in props.")
            return []

        # Extract tracks
        results = []
        entity_type = entity.get('type')
        
        if entity_type == 'track':
            title = entity.get('title', entity.get('name', 'Unknown Track'))
            artists = entity.get('artists', [])
            artist_name = ", ".join(a.get('name', '') for a in artists) if artists else "Unknown Artist"
            cover_url = entity.get('coverArt', {}).get('extractedColors', {}).get('colorRaw', {}).get('hex', None) # We'll just grab the cover from visualIdentity if possible
            
            # Real cover logic
            vi = entity.get('visualIdentity', {})
            images = vi.get('image', [])
            if images:
                cover_url = images[0].get('url')
                
            results.append({
                'title': title,
                'artist': artist_name,
                'cover_url': cover_url
            })
            
        elif entity_type in ['playlist', 'album']:
            track_list = entity.get('trackList', [])
            for t in track_list:
                title = t.get('title', 'Unknown Track')
                subtitle = t.get('subtitle', 'Unknown Artist')
                
                # Cover art usually not in trackList, fallback to playlist cover
                cover_url = None
                
                results.append({
                    'title': title,
                    'artist': subtitle,
                    'cover_url': cover_url
                })
        
        return results

    except Exception as e:
        _log.error("[Spotify] Error fetching metadata: %s", e)
        return []
