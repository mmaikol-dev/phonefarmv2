import datetime
import random
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import os

# ===== CONFIGURATION =====
SPOTIFY_PACKAGE = 'com.spotify.music'
SPOTIFY_ACTIVITY = 'com.spotify.music/.MainActivity'
SONG_TITLE = 'dumpsite'          # <-- SET YOUR SONG HERE
ARTIST_NAME = 'toxic lyrikali'      # optional, for better matching
STREAMS_TARGET = 1                   # number of times to play the song
STREAM_SECONDS = 35                  # seconds to stream each time
LOG_FILE = 'spotify_log.txt'
UI_WAIT_SECONDS = 10
UI_POLL_SECONDS = 0.8
DEBUG_UI = False  # Set to False to reduce debug output

# Coordinates for 1080x2400 resolution (used as fallback)
COORDS = {
    'home_tab': (100, 2328),
    'search_tab': (324, 2288),
    'search_field': (350, 124),
    'song_row': (228, 655),
    'mini_player': (540, 2200),
}

FALLBACK_COORDS = {
    'home_tab': [(100, 2288), (140, 2288), (120, 2235)],
    'search_tab': [(324, 2328), (300, 2288), (360, 2288), (324, 2235)],
    'search_field': [(540, 200), (350, 180), (350, 124)],
}

# ===== UTILITIES =====
def log(message):
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    full_message = f'[{timestamp}] {message}'
    print(full_message)
    with open(LOG_FILE, 'a') as file:
        file.write(full_message + '\n')

def adb(args, *, capture_output=False, check=False, timeout=30):
    try:
        return subprocess.run(
            ['adb', *args],
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        log(f'⚠️ ADB command timed out: adb {" ".join(args)}')
        raise

def tap(x, y, label=''):
    if label:
        log(f'   👆 Tap: {label} ({x},{y})')
    adb(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(random.uniform(0.8, 1.2))

def type_text(text):
    log(f'   ⌨️ Typing: "{text}"')
    safe_text = text.replace(' ', '%s').replace('&', '\\&').replace(';', '\\;')
    adb(['shell', 'input', 'text', safe_text])
    time.sleep(1.0)

def type_char_by_char(text):
    log(f'   ⌨️ Typing (char by char): "{text}"')
    for char in text:
        if char == ' ':
            adb(['shell', 'input', 'keyevent', 'KEYCODE_SPACE'])
        else:
            adb(['shell', 'input', 'text', char])
        time.sleep(0.1)
    time.sleep(0.5)

def press_enter():
    log('   ⌨️ Pressing Enter')
    adb(['shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
    time.sleep(1.5)

def press_back():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_BACK'])
    time.sleep(1.0)

def press_home():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_HOME'])
    time.sleep(1.0)

def wake_and_unlock_device():
    log('🔓 Waking and unlocking phone...')
    adb(['shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'])
    time.sleep(1.0)
    adb(['shell', 'wm', 'dismiss-keyguard'])
    time.sleep(0.8)
    adb(['shell', 'input', 'swipe', '540', '1800', '540', '500', '250'])
    time.sleep(1.2)
    adb(['shell', 'svc', 'power', 'stayon', 'usb'])
    time.sleep(0.5)

def human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def device_is_connected():
    try:
        result = adb(['devices'], capture_output=True, timeout=10)
        return any('\tdevice' in line for line in result.stdout.splitlines())
    except Exception:
        return False

def open_spotify():
    log('📱 Opening Spotify...')
    wake_and_unlock_device()
    adb(['shell', 'am', 'start', '-n', SPOTIFY_ACTIVITY])
    time.sleep(4)

def get_foreground_package():
    try:
        result = adb(['shell', 'dumpsys', 'window'], capture_output=True, timeout=10)
        if result.returncode != 0:
            return ''
        for line in result.stdout.splitlines():
            if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                match = re.search(r' ([A-Za-z0-9._]+)/', line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return ''

def ensure_spotify_foreground():
    package_name = get_foreground_package()
    if package_name != SPOTIFY_PACKAGE:
        log(f'   Spotify not foreground ({package_name or "unknown"}) — reopening')
        open_spotify()
        time.sleep(2)

def parse_bounds(bounds):
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds or '')
    if not match:
        return None
    return tuple(map(int, match.groups()))

def bounds_center(bounds):
    parsed = parse_bounds(bounds)
    if not parsed:
        return None, None
    x1, y1, x2, y2 = parsed
    return (x1 + x2) // 2, (y1 + y2) // 2

def dump_ui():
    """Dump current UI hierarchy and return root element"""
    remote_path = '/sdcard/window_dump.xml'
    for attempt in range(3):
        try:
            adb(['shell', 'rm', remote_path], capture_output=True, timeout=5)
            adb(['shell', 'uiautomator', 'dump', remote_path], capture_output=True, timeout=15)
            time.sleep(0.8)
            file_check = adb(['shell', 'test', '-f', remote_path, '&&', 'echo', 'exists'], capture_output=True, timeout=5)
            if 'exists' not in file_check.stdout:
                time.sleep(0.5)
                continue
            read_result = adb(['exec-out', 'cat', remote_path], capture_output=True, timeout=10)
            if not read_result.stdout or len(read_result.stdout) < 100:
                time.sleep(0.5)
                continue
            xml_start = read_result.stdout.find('<?xml')
            if xml_start == -1:
                time.sleep(0.5)
                continue
            return ET.fromstring(read_result.stdout[xml_start:])
        except ET.ParseError:
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return None

def iter_nodes(root):
    if root is None:
        return []
    return list(root.iter('node'))

def node_resource_id(node):
    return node.attrib.get('resource-id', '')

def node_text(node):
    return node.attrib.get('text', '').strip()

def node_desc(node):
    return node.attrib.get('content-desc', '').strip()

def node_attrib(node, attr):
    return node.attrib.get(attr, '')

def node_center(node):
    return bounds_center(node.attrib.get('bounds'))

def node_clickable(node):
    return node_attrib(node, 'clickable') == 'true'

def node_class(node):
    return node_attrib(node, 'class')

def find_first_node(root, predicate):
    if root is None:
        return None
    for node in iter_nodes(root):
        if predicate(node):
            return node
    return None

def find_all_nodes(root, predicate):
    if root is None:
        return []
    return [node for node in iter_nodes(root) if predicate(node)]

def wait_for(description, predicate, timeout=UI_WAIT_SECONDS, poll=UI_POLL_SECONDS):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if predicate():
                log(f'   ✅ {description}')
                return True
        except Exception:
            pass
        time.sleep(poll)
    log(f'   ❌ Timed out waiting for {description}')
    return False

def find_node_by_resource_id(resource_id):
    root = dump_ui()
    if root is None:
        return None
    return find_first_node(root, lambda item: node_resource_id(item) == resource_id)

def has_resource_id(resource_id):
    node = find_node_by_resource_id(resource_id)
    return node is not None

def screen_contains_text(*needles):
    root = dump_ui()
    if root is None:
        return False
    lowered_needles = [needle.lower() for needle in needles]
    return find_first_node(
        root,
        lambda item: any(
            needle in node_text(item).lower() or needle in node_desc(item).lower()
            for needle in lowered_needles
        ),
    ) is not None

# ===== SEARCH SCREEN DETECTION =====
def is_search_screen():
    """Check if current screen is Spotify search screen."""
    search_ids = [
        'com.spotify.music:id/search_root',
        'com.spotify.music:id/search_field_root',
        'com.spotify.music:id/query',
        'com.spotify.music:id/search_input'
    ]
    for rid in search_ids:
        if has_resource_id(rid):
            return True

    search_texts = [
        'what do you want to listen to?',
        'discover something new',
        'browse all',
        'search for artists, songs, or podcasts',
        'search spotify'
    ]
    if screen_contains_text(*search_texts):
        return True

    root = dump_ui()
    if root is not None:
        for node in iter_nodes(root):
            if node_text(node).strip().lower() == 'search' and node_clickable(node):
                x, y = node_center(node)
                if x is not None and y is not None and y > 2000:
                    return True
    return False

def is_search_results_screen():
    """Check if current screen shows search results."""
    if has_resource_id('com.spotify.music:id/search_content_recyclerview'):
        return True

    # Check for typical search result patterns
    if screen_contains_text('songs', 'artists', 'playlists', 'albums', 'top result', 'Song •'):
        return True

    if is_search_screen():
        return False

    return False

def is_keyboard_visible():
    result = adb(['shell', 'dumpsys', 'input_method'], capture_output=True, timeout=5)
    return 'mInputShown=true' in result.stdout

def get_spotify_playback_snapshot():
    try:
        result = adb(['shell', 'dumpsys', 'media_session'], capture_output=True, timeout=10)
        lines = result.stdout.splitlines()
        for index, line in enumerate(lines):
            if SPOTIFY_PACKAGE not in line:
                continue
            window = '\n'.join(lines[index:index + 80])
            state_match = re.search(r'state=PlaybackState \{state=(\d+)', window)
            position_match = re.search(r'position=(\d+)', window)
            title_match = re.search(r'description=([^,\n]+)', window)
            is_playing = state_match is not None and state_match.group(1) == '3'
            return {
                'playing': is_playing,
                'position': int(position_match.group(1)) if position_match else None,
                'title': title_match.group(1).strip() if title_match else None,
            }
    except Exception:
        pass
    return {'playing': False, 'position': None, 'title': None}

def confirm_playback_started():
    time.sleep(2)
    first = get_spotify_playback_snapshot()
    if not first['playing']:
        return False
    time.sleep(3)
    second = get_spotify_playback_snapshot()
    if not second['playing']:
        return False
    if first['position'] is not None and second['position'] is not None:
        return second['position'] > first['position']
    return second['playing']

def find_search_tab_coords():
    root = dump_ui()
    if root is not None:
        node = find_first_node(
            root,
            lambda item: (
                'search, tab' in node_desc(item).lower() or
                'search tab' in node_desc(item).lower() or
                (
                    node_clickable(item) and
                    node_text(item).strip().lower() == 'search' and
                    (node_center(item)[1] or 0) > 2000
                )
            ),
        )
        if node is not None:
            x, y = node_center(node)
            if x is not None and y is not None:
                return x, y
    return COORDS['search_tab']

def find_search_field_coords():
    root = dump_ui()
    if root is None:
        return COORDS['search_field']
    placeholder = "what do you want to listen to?"
    node = find_first_node(
        root,
        lambda item: (
            placeholder in node_text(item).lower() or
            placeholder in node_desc(item).lower()
        )
    )
    if node is not None:
        x, y = node_center(node)
        if x is not None and y is not None:
            log(f'   Found search field via placeholder text at ({x},{y})')
            return x, y
    for rid in ('com.spotify.music:id/query', 'com.spotify.music:id/search_field_root'):
        node = find_node_by_resource_id(rid)
        if node is not None:
            x, y = node_center(node)
            if x is not None and y is not None:
                log(f'   Found search field via resource-id {rid} at ({x},{y})')
                return x, y
    node = find_first_node(
        root,
        lambda item: (
            node_clickable(item) and
            ('search' in node_text(item).lower() or 'search' in node_desc(item).lower())
        ) and node_resource_id(item) != 'com.spotify.music:id/faceheader_title'
    )
    if node is not None:
        x, y = node_center(node)
        if x is not None and y is not None:
            log(f'   Found search field via text/desc at ({x},{y})')
            return x, y
    for node in iter_nodes(root):
        if node_clickable(node):
            x, y = node_center(node)
            if x is not None and y is not None and y < 400:
                log(f'   Found candidate near top at ({x},{y})')
                return x, y
    return COORDS['search_field']

def focus_search_field():
    log('   🔍 Focusing search field')
    known_x, known_y = COORDS['search_field']
    log(f'   Trying known coordinate ({known_x}, {known_y})')
    tap(known_x, known_y, 'Known search field')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    x, y = find_search_field_coords()
    log(f'   UI detected search field at ({x}, {y})')
    tap(x, y, 'UI-detected search field')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    log('   Trying fallback coordinates')
    for alt_x, alt_y in FALLBACK_COORDS['search_field']:
        tap(alt_x, alt_y, f'Fallback ({alt_x},{alt_y})')
        time.sleep(2)
        if is_keyboard_visible():
            log('   ✅ Keyboard is now visible')
            return True
    log('   Trying center screen tap')
    tap(540, 500, 'Center screen')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    log('   ❌ Could not focus search field')
    return False

def clear_search_query():
    log('   🧹 Clearing search field')
    if not is_keyboard_visible():
        log('   Keyboard not visible, cannot clear')
        return False
    adb(['shell', 'input', 'keyevent', 'KEYCODE_MOVE_END'])
    time.sleep(0.2)
    adb(['shell', 'input', 'keyevent', 'KEYCODE_SHIFT_LEFT', '--longpress'])
    time.sleep(0.3)
    adb(['shell', 'input', 'keyevent', 'KEYCODE_DEL'])
    time.sleep(0.5)
    return True

def get_search_field_text():
    root = dump_ui()
    if root is None:
        return ''
    focused_node = find_first_node(root, lambda item: node_attrib(item, 'focused') == 'true')
    if focused_node is not None:
        return node_text(focused_node)
    edit_text_node = find_first_node(
        root,
        lambda item: node_attrib(item, 'class') == 'android.widget.EditText'
    )
    if edit_text_node is not None:
        return node_text(edit_text_node)
    placeholder = "what do you want to listen to?"
    node = find_first_node(
        root,
        lambda item: (
            placeholder in node_text(item).lower() or
            placeholder in node_desc(item).lower() or
            node_resource_id(item) in ('com.spotify.music:id/query', 'com.spotify.music:id/search_field_root')
        )
    )
    if node is not None:
        return node_text(node)
    return ''

def ensure_search_field_ready(query):
    log(f'   🔍 Ensuring search field is ready for "{query}"')
    if not is_keyboard_visible():
        if not focus_search_field():
            return False
    else:
        log('   Keyboard already visible')
    clear_search_query()
    time.sleep(0.5)
    type_text(query)
    time.sleep(1)
    entered_text = get_search_field_text()
    if query.lower() in entered_text.lower():
        log(f'   ✅ Verified text in search field: "{entered_text}"')
        return True
    else:
        log(f'   ⚠️ Text verification failed. Found: "{entered_text}"')
        clear_search_query()
        time.sleep(0.5)
        type_char_by_char(query)
        time.sleep(1)
        entered_text = get_search_field_text()
        if query.lower() in entered_text.lower():
            log(f'   ✅ Verified text after char-by-char: "{entered_text}"')
            return True
        else:
            log(f'   ❌ Still no text. Found: "{entered_text}"')
            return False

# ===== IMPROVED SONG DETECTION BASED ON ACTUAL UI STRUCTURE =====
class SongInfo:
    """Represents a song found in search results"""
    def __init__(self, title_node, artist_node, title_text, artist_text, x, y):
        self.title_node = title_node
        self.artist_node = artist_node
        self.title = title_text
        self.artist = artist_text
        self.x = x
        self.y = y
    
    def matches_exact(self, target_title, target_artist):
        """Check for exact match (case-insensitive)"""
        title_match = target_title.lower() == self.title.lower()
        artist_match = not target_artist or target_artist.lower() == self.artist.lower()
        return title_match and artist_match
    
    def matches_partial(self, target_title, target_artist):
        """Check for partial match (title contains, artist contains)"""
        title_match = target_title.lower() in self.title.lower()
        artist_match = not target_artist or target_artist.lower() in self.artist.lower()
        return title_match and artist_match
    
    def __repr__(self):
        return f"SongInfo(title='{self.title}', artist='{self.artist}', pos=({self.x},{self.y}))"

def find_songs_in_search_results():
    """
    Parse UI to find songs based on actual Spotify search result structure.
    Based on debug output showing:
    - Title: "Billie Jean" at (512,537)
    - Artist: "Song • Michael Jackson" at (512,588)
    """
    root = dump_ui()
    if root is None:
        return []
    
    songs = []
    
    # Look for text nodes that might be song titles
    # Based on debug, song titles are at y ~537, 889, 1265, etc.
    for node in iter_nodes(root):
        text = node_text(node)
        if not text:
            continue
        
        x, y = node_center(node)
        if x is None or y is None:
            continue
        
        # Skip if in top search area (y < 200) or mini-player area (y > 2100)
        if y < 200 or y > 2100:
            continue
        
        # Check if this looks like a song title
        # Song titles are usually short, don't contain special patterns
        if len(text) < 50 and not any(pattern in text.lower() for pattern in ['song •', 'playlist', 'album', 'video', 'podcast']):
            # This might be a song title
            # Look for artist info below or near this node
            artist_text = ""
            artist_y = y + 50  # Artist is usually about 50px below title
            
            # Find artist node (should contain "Song • ArtistName")
            for artist_node in iter_nodes(root):
                artist_node_text = node_text(artist_node)
                artist_node_y = node_center(artist_node)[1] if node_center(artist_node) else 0
                
                if artist_node_y and abs(artist_node_y - artist_y) < 100:
                    if 'Song •' in artist_node_text or '• Song' in artist_node_text:
                        artist_text = artist_node_text
                        # Extract artist name after "Song • "
                        if 'Song • ' in artist_text:
                            artist_text = artist_text.split('Song • ')[-1]
                        elif '• Song' in artist_text:
                            artist_text = artist_text.split('• Song')[0]
                        break
            
            # If we found a title, add it
            if text and not any(skip in text.lower() for skip in ['cancel', 'content filters', 'now playing']):
                songs.append(SongInfo(node, None, text, artist_text, x, y))
                log(f'   Found song: "{text}" by "{artist_text}" at ({x},{y})')
    
    return songs

def find_and_click_correct_song(song_title, artist_name):
    """
    Find and click the correct song by matching exact title and artist.
    """
    log(f'   🎯 Looking for exact match: "{song_title}" by "{artist_name}"')
    
    # Get all songs
    songs = find_songs_in_search_results()
    
    if not songs:
        log('   ⚠️ No songs found in search results')
        return False
    
    log(f'   📋 Found {len(songs)} songs')
    
    # First try exact match
    for song in songs:
        if song.matches_exact(song_title, artist_name):
            log(f'   ✅ Found EXACT match: "{song.title}" by "{song.artist}" at ({song.x},{song.y})')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    # If no exact match, try partial match (but be careful)
    for song in songs:
        if song.matches_partial(song_title, artist_name):
            # Check if this is a remix/cover (contains extra words)
            title_lower = song.title.lower()
            if 'remix' in title_lower or 'cover' in title_lower or 'version' in title_lower:
                log(f'   ⚠️ Skipping remix/cover: "{song.title}"')
                continue
            
            log(f'   ⚠️ Found partial match: "{song.title}" by "{song.artist}"')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    # If still no match, try to find the first song that's not a remix
    for song in songs:
        title_lower = song.title.lower()
        if ('remix' not in title_lower and 'cover' not in title_lower and 
            'version' not in title_lower and 'trap' not in title_lower):
            log(f'   ⚠️ Using fallback: "{song.title}" by "{song.artist}"')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    return False

# ===== MINI-PLAYER HANDLING =====
def find_and_click_mini_player():
    """Find and click the mini-player that appears after selecting a song"""
    root = dump_ui()
    if root is None:
        return False
    
    # Look for mini-player container
    mini_player = find_first_node(
        root,
        lambda item: (node_resource_id(item) == 'com.spotify.music:id/miniplayer' or
                     'miniplayer' in node_resource_id(item).lower() or
                     ('mini' in node_desc(item).lower() and 'player' in node_desc(item).lower()))
    )
    
    if mini_player:
        x, y = node_center(mini_player)
        if x and y:
            log(f'   🎮 Clicking mini-player at ({x},{y})')
            tap(x, y, 'Mini-player')
            time.sleep(1)
            return True
    
    # Fallback: Look for any clickable element at bottom with play/pause
    for node in iter_nodes(root):
        desc = node_desc(node).lower()
        if ('play' in desc or 'pause' in desc) and node_clickable(node):
            x, y = node_center(node)
            if x and y and y > 2000:  # Near bottom of screen
                log(f'   🎮 Clicking bottom player bar at ({x},{y})')
                tap(x, y, 'Bottom player bar')
                time.sleep(1)
                return True
    
    return False

def wait_for_mini_player(timeout=8):
    """Wait for mini-player to appear after clicking a song"""
    log('   ⏳ Waiting for mini-player to appear...')
    deadline = time.time() + timeout
    while time.time() < deadline:
        root = dump_ui()
        if root is not None:
            # Check for mini-player
            mp = find_first_node(root, lambda item: 
                node_resource_id(item) == 'com.spotify.music:id/miniplayer' or
                'miniplayer' in node_resource_id(item).lower()
            )
            if mp:
                log('   ✅ Mini-player appeared!')
                return True
        time.sleep(0.5)
    log('   ⚠️ Mini-player did not appear')
    return False

def ensure_playback_starts(duration):
    """After mini-player is clicked, ensure playback actually starts"""
    log('   🎵 Checking if playback started...')
    
    # Give it a moment to start playing
    time.sleep(2)
    
    # Check if playback started
    if confirm_playback_started():
        log(f'   ▶️ Playback confirmed! Streaming for {duration}s...')
        time.sleep(duration + random.randint(0, 3))
        return True
    
    # Try to manually press play if needed
    log('   ⏸️ Playback not started, looking for play button...')
    
    # Check for play button in the now-playing screen
    root = dump_ui()
    if root:
        play_button = find_first_node(root, lambda item:
            node_resource_id(item) in ['com.spotify.music:id/play_pause_button', 
                                       'com.spotify.music:id/control_play_pause',
                                       'com.spotify.music:id/play_button'] or
            ('play' in node_desc(item).lower() and node_clickable(item))
        )
        
        if play_button:
            x, y = node_center(play_button)
            if x and y:
                log(f'   Found play button at ({x},{y}) - pressing')
                tap(x, y, 'Play button')
                time.sleep(2)
                
                if confirm_playback_started():
                    log(f'   ▶️ Playback started! Streaming for {duration}s...')
                    time.sleep(duration + random.randint(0, 3))
                    return True
    
    log('   ❌ Could not start playback')
    return False

# ===== MAIN PLAYBACK FLOW =====
def play_song(song_title, artist_name, duration):
    """
    Complete flow for playing a specific song:
    1. Find and click the correct song using UI detection
    2. Wait for mini-player to appear
    3. Click mini-player to expand
    4. Ensure playback starts
    5. Stream for specified duration
    """
    log(f'━━━ Playing: "{song_title}" by "{artist_name}" ━━━')
    
    # Step 1: Find and click the correct song
    if not find_and_click_correct_song(song_title, artist_name):
        log('   ❌ Could not find the correct song')
        return False
    
    # Step 2: Wait for mini-player to appear
    if not wait_for_mini_player(timeout=8):
        log('   ⚠️ Mini-player didn\'t appear, but continuing...')
    
    time.sleep(1)
    
    # Step 3: Click mini-player to expand
    if not find_and_click_mini_player():
        log('   ⚠️ Could not click mini-player, checking playback anyway...')
    
    # Step 4: Ensure playback starts and stream
    return ensure_playback_starts(duration)

# ===== MAIN STEPS =====
def step_go_home():
    log('━━━ STEP 1: Reset to Home ━━━')
    ensure_spotify_foreground()
    for coords in [COORDS['home_tab']] + FALLBACK_COORDS['home_tab']:
        tap(coords[0], coords[1], 'Home tab')
        time.sleep(2)
        if screen_contains_text('jump back in', 'fresh new music', 'liked songs'):
            return True
    return False

def step_go_to_search():
    log('━━━ STEP 2: Open Search ━━━')
    search_coords = [find_search_tab_coords()] + FALLBACK_COORDS['search_tab']
    for attempt, (x, y) in enumerate(search_coords[:5], 1):
        tap(x, y, f'Search tab (attempt {attempt})')
        if wait_for('Search screen', is_search_screen, timeout=5):
            return True
    return False

def step_search_query(query):
    log(f'━━━ STEP 3: Search for "{query}" ━━━')
    if not ensure_search_field_ready(query):
        log('   ❌ Could not prepare search field')
        return False
    press_enter()
    return wait_for('Search results', is_search_results_screen, timeout=8)

# ===== MAIN =====
def run():
    # Build search query including artist if provided
    search_query = SONG_TITLE
    if ARTIST_NAME:
        search_query += ' ' + ARTIST_NAME

    log('=' * 55)
    log('🎵 Spotify Bot — Exact Song Matching')
    log(f'🎤 Song: {SONG_TITLE}')
    if ARTIST_NAME:
        log(f'🎤 Artist: {ARTIST_NAME}')
        log(f'🔍 Search query: "{search_query}"')
    log(f'🎯 Target plays: {STREAMS_TARGET}')
    log(f'⏱️ Per play: {STREAM_SECONDS}s')
    log('=' * 55)

    if not device_is_connected():
        log('❌ No ADB device detected.')
        return

    log('✅ ADB device detected')
    log('Starting in 5 seconds...')
    time.sleep(5)

    total_plays = 0
    rounds = 0

    while total_plays < STREAMS_TARGET:
        rounds += 1
        log(f'\n🔄 ROUND {rounds} | ✅ {total_plays}/{STREAMS_TARGET}\n')

        try:
            open_spotify()
            human_pause(2, 3)

            if not step_go_home():
                log('⚠️ Could not verify home screen')

            if not step_go_to_search():
                log('❌ Could not open Search. Retrying round.')
                continue

            if not step_search_query(search_query):
                log('❌ Search results did not load. Retrying round.')
                continue

            # Play the specific song
            if play_song(SONG_TITLE, ARTIST_NAME, STREAM_SECONDS):
                total_plays += 1
                log(f'\n📊 Round {rounds}: +1 play | Total: {total_plays}/{STREAMS_TARGET}')
            else:
                log(f'❌ Failed to play song in round {rounds}')

            if total_plays < STREAMS_TARGET:
                pause_seconds = random.randint(20, 45)
                log(f'😴 Break: {pause_seconds}s...')
                time.sleep(pause_seconds)

        except KeyboardInterrupt:
            log('\n⚠️ Bot interrupted by user')
            break
        except Exception as e:
            log(f'❌ Error in round {rounds}: {e}')
            import traceback
            traceback.print_exc()
            time.sleep(15)

    log('')
    log('=' * 55)
    log(f'✅ DONE! {total_plays}/{STREAMS_TARGET} plays of "{SONG_TITLE}"')
    log('=' * 55)

if __name__ == '__main__':
    run()