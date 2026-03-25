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
SONG_TITLE = 'bamchikicha'
ARTIST_NAME = 'lifah'
STREAMS_TARGET = 1
STREAM_SECONDS = 35
LOG_FILE = 'spotify_log.txt'
UI_WAIT_SECONDS = 10
UI_POLL_SECONDS = 0.8
DEBUG_UI = False

# ===== SCREEN RESOLUTION HANDLING =====
_screen_width = None
_screen_height = None

def get_screen_dimensions():
    global _screen_width, _screen_height
    try:
        result = adb(['shell', 'wm', 'size'], capture_output=True, timeout=10)
        match = re.search(r'(\d+)x(\d+)', result.stdout)
        if match:
            _screen_width, _screen_height = int(match.group(1)), int(match.group(2))
            log(f'📐 Detected screen resolution: {_screen_width}x{_screen_height}')
            return _screen_width, _screen_height
    except Exception as e:
        log(f'⚠️ Could not detect screen resolution: {e}')
    _screen_width, _screen_height = 1080, 2400
    log(f'⚠️ Using fallback resolution: {_screen_width}x{_screen_height}')
    return _screen_width, _screen_height

def scale_coords(rel_coords):
    if _screen_width is None or _screen_height is None:
        get_screen_dimensions()
    x_rel, y_rel = rel_coords
    return int(x_rel * _screen_width), int(y_rel * _screen_height)

def scale_coords_list(rel_coords_list):
    return [scale_coords(c) for c in rel_coords_list]

# ===== RELATIVE COORDINATES =====
REL_COORDS = {
    'home_tab': (0.09, 0.97),
    'search_tab': (0.30, 0.97),
    'library_tab': (0.50, 0.97),
    'search_field': (0.32, 0.05),
    'song_row': (0.21, 0.27),
    'mini_player': (0.50, 0.92),
}

REL_FALLBACK_COORDS = {
    'home_tab': [(0.09, 0.95), (0.13, 0.95), (0.11, 0.93)],
    'search_tab': [(0.30, 0.97), (0.28, 0.95), (0.33, 0.95), (0.30, 0.93)],
    'search_field': [(0.50, 0.08), (0.32, 0.075), (0.32, 0.05)],
    'mini_player': [(0.50, 0.92), (0.50, 0.93), (0.30, 0.93), (0.70, 0.93)],
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

def tap_rel(rel_coords, label=''):
    x, y = scale_coords(rel_coords)
    return tap(x, y, label)

def type_char_by_char(text):
    log(f'   ⌨️ Typing (char by char): "{text}"')
    for char in text:
        if char == ' ':
            adb(['shell', 'input', 'keyevent', 'KEYCODE_SPACE'])
        else:
            adb(['shell', 'input', 'text', char])
        time.sleep(0.08)
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
    swipe_start = scale_coords((0.50, 0.75))
    swipe_end = scale_coords((0.50, 0.20))
    adb(['shell', 'input', 'swipe', str(swipe_start[0]), str(swipe_start[1]), 
         str(swipe_end[0]), str(swipe_end[1]), '250'])
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

def launch_spotify():
    log('📱 Launching Spotify...')
    adb(['shell', 'am', 'start', '-n', SPOTIFY_ACTIVITY])
    time.sleep(3)

def bring_spotify_to_foreground():
    package_name = get_foreground_package()
    if package_name != SPOTIFY_PACKAGE:
        log(f'   📱 Bringing Spotify to foreground (was: {package_name or "unknown"})')
        adb(['shell', 'am', 'start', '-n', SPOTIFY_ACTIVITY])
        time.sleep(2)
    else:
        log('   ✅ Spotify already in foreground')

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
                if x is not None and y is not None:
                    if _screen_height and y > _screen_height * 0.90:
                        return True
    return False

def is_search_results_screen():
    if has_resource_id('com.spotify.music:id/search_content_recyclerview'):
        return True
    if screen_contains_text('songs', 'artists', 'playlists', 'albums', 'top result', 'Song •'):
        return True
    if is_search_screen():
        return False
    return True

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
    """Check if playback is active by verifying position advances"""
    first = get_spotify_playback_snapshot()
    log(f'   📊 First check - Playing: {first["playing"]}, Position: {first["position"]}')
    if not first['playing']:
        return False
    
    time.sleep(3)
    
    second = get_spotify_playback_snapshot()
    log(f'   📊 Second check - Playing: {second["playing"]}, Position: {second["position"]}')
    if not second['playing']:
        return False
    
    if first['position'] is not None and second['position'] is not None:
        if second['position'] > first['position']:
            log(f'   ✅ Position advanced: {first["position"]} → {second["position"]}')
            return True
    
    log(f'   ⚠️ Position did not advance, but playback state is active')
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
                    node_center(item)[1] is not None and
                    _screen_height and node_center(item)[1] > _screen_height * 0.90
                )
            ),
        )
        if node is not None:
            x, y = node_center(node)
            if x is not None and y is not None:
                return x, y
    return scale_coords(REL_COORDS['search_tab'])

def find_search_field_coords():
    root = dump_ui()
    if root is None:
        return scale_coords(REL_COORDS['search_field'])
    
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
            if x is not None and y is not None and _screen_height and y < _screen_height * 0.15:
                log(f'   Found candidate near top at ({x},{y})')
                return x, y
    
    return scale_coords(REL_COORDS['search_field'])

def focus_search_field():
    log('   🔍 Focusing search field')
    known_x, known_y = scale_coords(REL_COORDS['search_field'])
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
    for rel_alt in REL_FALLBACK_COORDS['search_field']:
        alt_x, alt_y = scale_coords(rel_alt)
        tap(alt_x, alt_y, f'Fallback ({alt_x},{alt_y})')
        time.sleep(2)
        if is_keyboard_visible():
            log('   ✅ Keyboard is now visible')
            return True
    
    log('   ❌ Could not focus search field')
    return False

def clear_search_query():
    log('   🧹 Clearing search field')
    if not is_keyboard_visible():
        log('   Keyboard not visible, cannot clear')
        return False
    
    for _ in range(60):
        adb(['shell', 'input', 'keyevent', 'KEYCODE_DEL'])
        time.sleep(0.02)
    time.sleep(0.3)
    
    current = get_search_field_text()
    if current.strip():
        log(f'   ⚠️ Field still has "{current}", trying backup clear...')
        for _ in range(40):
            adb(['shell', 'input', 'keyevent', 'KEYCODE_DEL'])
            time.sleep(0.02)
        time.sleep(0.3)
    
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
    
    for _ in range(2):
        clear_search_query()
        time.sleep(0.5)
        if not get_search_field_text().strip():
            break
    
    type_char_by_char(query)
    time.sleep(1.5)
    
    entered_text = get_search_field_text().strip()
    if entered_text.lower() == query.lower():
        log(f'   ✅ Verified exact text: "{entered_text}"')
        return True
    elif query.lower() in entered_text.lower() and len(entered_text) <= len(query) + 2:
        log(f'   ✅ Verified close match: "{entered_text}"')
        return True
    else:
        log(f'   ⚠️ Text mismatch. Expected: "{query}", Got: "{entered_text}"')
        for _ in range(3):
            adb(['shell', 'input', 'keyevent', 'KEYCODE_DEL'])
            time.sleep(0.05)
        time.sleep(0.5)
        type_char_by_char(query)
        time.sleep(1.5)
        entered_text = get_search_field_text().strip()
        if entered_text.lower() == query.lower():
            log(f'   ✅ Verified after retry: "{entered_text}"')
            return True
        else:
            log(f'   ❌ Final verification failed. Got: "{entered_text}"')
            return False

# ===== SONG DETECTION =====
class SongInfo:
    def __init__(self, title_node, artist_node, title_text, artist_text, x, y):
        self.title_node = title_node
        self.artist_node = artist_node
        self.title = title_text
        self.artist = artist_text
        self.x = x
        self.y = y
    
    def matches_exact(self, target_title, target_artist):
        title_match = target_title.lower() == self.title.lower()
        artist_match = not target_artist or target_artist.lower() == self.artist.lower()
        return title_match and artist_match
    
    def matches_partial(self, target_title, target_artist):
        title_match = target_title.lower() in self.title.lower()
        artist_match = not target_artist or target_artist.lower() in self.artist.lower()
        return title_match and artist_match
    
    def __repr__(self):
        return f"SongInfo(title='{self.title}', artist='{self.artist}', pos=({self.x},{self.y}))"

def find_songs_in_search_results():
    root = dump_ui()
    if root is None:
        return []
    
    songs = []
    if _screen_height is None:
        get_screen_dimensions()
    
    for node in iter_nodes(root):
        text = node_text(node)
        if not text:
            continue
        
        x, y = node_center(node)
        if x is None or y is None:
            continue
        
        if _screen_height and (y < _screen_height * 0.10 or y > _screen_height * 0.90):
            continue
        
        if len(text) < 50 and not any(pattern in text.lower() for pattern in ['song •', 'playlist', 'album', 'video', 'podcast']):
            artist_text = ""
            artist_y = y + (_screen_height * 0.02 if _screen_height else 50)
            
            for artist_node in iter_nodes(root):
                artist_node_text = node_text(artist_node)
                artist_node_center = node_center(artist_node)
                artist_node_y = artist_node_center[1] if artist_node_center else 0
                
                if artist_node_y and abs(artist_node_y - artist_y) < (_screen_height * 0.04 if _screen_height else 100):
                    if 'Song •' in artist_node_text or '• Song' in artist_node_text:
                        artist_text = artist_node_text
                        if 'Song • ' in artist_text:
                            artist_text = artist_text.split('Song • ')[-1]
                        elif '• Song' in artist_text:
                            artist_text = artist_text.split('• Song')[0]
                        break
            
            if text and not any(skip in text.lower() for skip in ['cancel', 'content filters', 'now playing']):
                songs.append(SongInfo(node, None, text, artist_text, x, y))
                if DEBUG_UI:
                    log(f'   Found song: "{text}" by "{artist_text}" at ({x},{y})')
    
    return songs

def find_and_click_correct_song(song_title, artist_name):
    log(f'   🎯 Looking for: "{song_title}" by "{artist_name}"')
    songs = find_songs_in_search_results()
    
    if not songs:
        log('   ⚠️ No songs found in search results')
        return False
    
    valid_songs = [s for s in songs if 
                   s.title.lower() not in ['artists', 'songs', 'albums', 'playlists', 'follow', 'artist'] and
                   len(s.title) > 2]
    
    if not valid_songs:
        log('   ⚠️ No valid song candidates after filtering')
        return False
    
    log(f'   📋 Found {len(valid_songs)} valid song candidates')
    
    for song in valid_songs:
        if song.matches_exact(song_title, artist_name):
            log(f'   ✅ Found EXACT match: "{song.title}" by "{song.artist}" at ({song.x},{song.y})')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    for song in valid_songs:
        if song.matches_partial(song_title, artist_name):
            title_lower = song.title.lower()
            if any(bad in title_lower for bad in ['remix', 'cover', 'version', 'live', 'acoustic']):
                continue
            log(f'   ⚠️ Using partial match: "{song.title}" by "{song.artist}"')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    for song in valid_songs:
        if song_title.lower() in song.title.lower():
            log(f'   ⚠️ Using fallback match: "{song.title}"')
            tap(song.x, song.y, f'Click: {song.title}')
            return True
    
    log('   ❌ No suitable song found')
    return False

# ===== FIXED MINI-PLAYER HANDLING =====
def check_if_already_playing():
    """Check if song is already playing after clicking (most common case)"""
    log('   🎵 Checking if song started playing automatically...')
    time.sleep(2)  # Give Spotify a moment to start playback
    
    # Quick check via media_session (fast, no UI dump)
    playback = get_spotify_playback_snapshot()
    log(f'   📊 Playback state: Playing={playback["playing"]}, Position={playback["position"]}')
    
    if playback['playing']:
        log('   ✅ Song is already playing!')
        return True
    
    return False

def click_mini_player_if_needed():
    """Only click mini-player if song isn't already playing"""
    log('   🎮 Checking if mini-player click is needed...')
    
    # Check if already playing first
    if check_if_already_playing():
        log('   ⏭️ Skipping mini-player click - already playing!')
        return True
    
    # Not playing, try clicking mini-player
    log('   ⚠️ Song not playing, clicking mini-player...')
    time.sleep(1)
    
    x, y = scale_coords(REL_COORDS['mini_player'])
    log(f'   👆 Tap: Mini-player ({x},{y})')
    tap(x, y, 'Mini-player')
    time.sleep(2)
    
    # Verify it worked
    if check_if_already_playing():
        log('   ✅ Mini-player click worked!')
        return True
    
    # Try one fallback
    log('   ⚠️ Trying fallback position...')
    x, y = scale_coords(REL_FALLBACK_COORDS['mini_player'][1])
    tap(x, y, 'Mini-player fallback')
    time.sleep(2)
    
    return True

def ensure_playback_starts(duration):
    log('   🎵 Starting playback stream...')
    
    # Final verification
    if confirm_playback_started():
        log(f'   ▶️ Playback confirmed! Streaming for {duration}s...')
        time.sleep(duration + random.randint(0, 3))
        return True
    
    # Try to find and press play button
    log('   ⏸️ Playback not confirmed, looking for play button...')
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
    log(f'━━━ Playing: "{song_title}" by "{artist_name}" ━━━')
    
    if not find_and_click_correct_song(song_title, artist_name):
        log('   ❌ Could not find the correct song')
        return False
    
    # Check if already playing, click mini-player only if needed
    click_mini_player_if_needed()
    
    return ensure_playback_starts(duration)

# ===== MAIN STEPS =====
def step_go_home():
    log('━━━ STEP 1: Reset to Home ━━━')
    bring_spotify_to_foreground()
    coords_list = [scale_coords(REL_COORDS['home_tab'])] + scale_coords_list(REL_FALLBACK_COORDS['home_tab'])
    for coords in coords_list:
        tap(coords[0], coords[1], 'Home tab')
        time.sleep(2)
        if screen_contains_text('jump back in', 'fresh new music', 'liked songs'):
            return True
    return False

def step_go_to_search():
    log('━━━ STEP 2: Open Search ━━━')
    search_coords = [find_search_tab_coords()] + scale_coords_list(REL_FALLBACK_COORDS['search_tab'])
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
    get_screen_dimensions()
    
    search_query = SONG_TITLE
    if ARTIST_NAME:
        search_query += ' ' + ARTIST_NAME

    log('=' * 55)
    log('🎵 Spotify Bot — v8 (Auto-Play Detection)')
    log(f'📐 Screen: {_screen_width}x{_screen_height}')
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
            launch_spotify()
            wake_and_unlock_device()
            human_pause(2, 3)

            if not step_go_home():
                log('⚠️ Could not verify home screen')

            if not step_go_to_search():
                log('❌ Could not open Search. Retrying round.')
                continue

            if not step_search_query(search_query):
                log('❌ Search results did not load. Retrying round.')
                continue

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