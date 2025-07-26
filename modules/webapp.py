#!/usr/bin/env python3
"""
Web App Launcher Script
Usage: python3 webapp.py [OPTIONS] <URL>

Options:
  --help         Show this help message and exit
  --pywebview    Prioritize PyWebView, fallback to Chromium app mode, then default browser
  --browser      Prioritize Chromium app mode, fallback to PyWebView, then default browser
  --auto         Auto mode (default): Prioritize PyWebView, fallback to Chromium, then default browser

Examples:
  python3 webapp.py http://127.0.0.1:5500
  python3 webapp.py --pywebview http://127.0.0.1:5500
  python3 webapp.py --browser http://127.0.0.1:5500
  python3 webapp.py --auto http://127.0.0.1:5500

This script detects the operating system and launches a web URL using different methods:
- PyWebView: Creates a native desktop app window
- Chromium App Mode: Launches in Chromium-based browsers with --app flag
- Default Browser: Falls back to system default browser
"""

import sys
import os
import platform
import subprocess
import webbrowser
import shutil
import argparse


def check_pywebview():
    """
    Check if PyWebView is available.
    
    Returns:
        bool: True if PyWebView is available, False otherwise
    """
    try:
        import webview
        return True
    except ImportError:
        return False


def launch_pywebview(url, title="Web App"):
    """
    Launch URL using PyWebView.
    
    Args:
        url (str): URL to open
        title (str): Window title
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import webview
        print(f"Launching with PyWebView: {url}")
        
        # Configure window properties
        webview.create_window(
            title=title,
            url=url,
            width=1200,
            height=800,
            min_size=(800, 600),
            resizable=True,
            fullscreen=False,
            minimized=False,
            on_top=False
        )
        
        # Start the webview (this will block until window is closed)
        webview.start(debug=False)
        return True
        
    except ImportError:
        print("PyWebView not available. Install with: pip install pywebview")
        return False
    except Exception as e:
        print(f"Error launching PyWebView: {e}")
        return False


def find_browser_executable(browser_names):
    """
    Find the first available browser executable from a list of browser names/paths.
    
    Args:
        browser_names (list): List of browser executable names or full paths to search for
        
    Returns:
        str or None: Path to the browser executable if found, None otherwise
    """
    for browser_name in browser_names:
        # If it's a full path, check if it exists directly
        if os.path.isabs(browser_name) and os.path.exists(browser_name):
            return browser_name
        # Otherwise, use shutil.which to find it in PATH
        else:
            browser_path = shutil.which(browser_name)
            if browser_path:
                return browser_path
    return None


def get_windows_browsers():
    """
    Get list of Chromium-based browser executables for Windows.
    Prioritizes Google Chrome first, then Microsoft Edge, then others.
    
    Returns:
        list: List of browser executable paths and names
    """
    browsers = []
    
    # Google Chrome paths (prioritize first due to market share)
    chrome_paths = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')
    ]
    
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            browsers.append(chrome_path)
            break  # Only add the first found Chrome installation
    
    # Microsoft Edge paths
    edge_paths = [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe')
    ]
    
    for edge_path in edge_paths:
        if os.path.exists(edge_path):
            browsers.append(edge_path)
            break  # Only add the first found Edge installation
    
    # Brave Browser paths
    brave_paths = [
        r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe')
    ]
    
    for brave_path in brave_paths:
        if os.path.exists(brave_path):
            browsers.append(brave_path)
            break  # Only add the first found Brave installation
    
    # Vivaldi paths
    vivaldi_paths = [
        r'C:\Program Files\Vivaldi\Application\vivaldi.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe')
    ]
    
    for vivaldi_path in vivaldi_paths:
        if os.path.exists(vivaldi_path):
            browsers.append(vivaldi_path)
            break  # Only add the first found Vivaldi installation
    
    # Opera paths (uses launcher.exe)
    opera_paths = [
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Opera\launcher.exe')
    ]
    
    for opera_path in opera_paths:
        if os.path.exists(opera_path):
            browsers.append(opera_path)
            break  # Only add the first found Opera installation
    
    # Ungoogled Chromium paths (manual installation)
    chromium_paths = [
        r'C:\Program Files\Chromium\Application\chrome.exe',
        r'C:\Program Files (x86)\Chromium\Application\chrome.exe'
    ]
    
    for chromium_path in chromium_paths:
        if os.path.exists(chromium_path):
            browsers.append(chromium_path)
            break  # Only add the first found Chromium installation
    
    # Fallback to PATH-based detection for any browsers we might have missed
    browsers.extend([
        'chrome.exe',
        'msedge.exe',
        'brave.exe',
        'vivaldi.exe',
        'launcher.exe',  # Opera
        'chromium.exe'
    ])
    
    return browsers


def get_unix_browsers():
    """
    Get list of Chromium-based browser executables for Linux and macOS.
    
    Returns:
        list: List of browser executable names
    """
    return [
        'chromium-browser',
        'chromium',
        'google-chrome',
        'google-chrome-stable',
        'chrome',
        'brave-browser',
        'brave',
        'opera',
        'vivaldi'
    ]


def get_flatpak_browsers():
    """
    Get list of Chromium-based browsers installed via Flatpak on Linux.
    
    Returns:
        list: List of Flatpak browser commands
    """
    flatpak_browsers = [
        'org.chromium.Chromium',
        'com.google.Chrome',
        'com.brave.Browser',
        'com.opera.Opera',
        'com.vivaldi.Vivaldi'
    ]
    
    available_browsers = []
    
    # Check if flatpak is available
    if not shutil.which('flatpak'):
        return available_browsers
    
    try:
        # Get list of installed flatpak applications
        result = subprocess.run(['flatpak', 'list', '--app'], 
                              capture_output=True, text=True, timeout=5)
        installed_apps = result.stdout
        
        for browser in flatpak_browsers:
            if browser in installed_apps:
                available_browsers.append(f'flatpak run {browser}')
                
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return available_browsers


def get_macos_browsers():
    """
    Get list of Chromium-based browser applications for macOS.
    Includes both standard installations and Homebrew installations.
    
    Returns:
        list: List of browser application paths
    """
    browsers = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
        '/Applications/Opera.app/Contents/MacOS/Opera',
        '/Applications/Vivaldi.app/Contents/MacOS/Vivaldi',
        # Homebrew installations
        '/opt/homebrew/bin/chromium',
        '/opt/homebrew/bin/google-chrome',
        '/opt/homebrew/bin/brave-browser',
        '/usr/local/bin/chromium',
        '/usr/local/bin/google-chrome',
        '/usr/local/bin/brave-browser'
    ]
    
    # Filter only existing applications
    return [browser for browser in browsers if os.path.exists(browser)]


def find_chromium_browser():
    """
    Find the best available Chromium-based browser based on operating system.
    
    Returns:
        str or None: Path to the browser executable if found, None otherwise
    """
    system = platform.system().lower()
    
    if system == 'windows':
        browser_names = get_windows_browsers()
        return find_browser_executable(browser_names)
        
    elif system == 'darwin':  # macOS
        # First try command-line executables
        browser_names = get_unix_browsers()
        browser_path = find_browser_executable(browser_names)
        
        # If not found, try macOS application bundles (including Homebrew)
        if not browser_path:
            macos_browsers = get_macos_browsers()
            for browser in macos_browsers:
                if os.path.exists(browser):
                    return browser
                    
    elif system == 'linux':
        # First try standard package installations
        browser_names = get_unix_browsers()
        browser_path = find_browser_executable(browser_names)
        
        # If not found, try Flatpak installations
        if not browser_path:
            flatpak_browsers = get_flatpak_browsers()
            if flatpak_browsers:
                return flatpak_browsers[0]  # Use the first available Flatpak browser
        
        return browser_path
    
    return None


def launch_chromium_app(browser_path, url):
    """
    Launch a Chromium-based browser in app mode.
    
    Args:
        browser_path (str): Path to the browser executable or command
        url (str): URL to open in app mode
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Handle Flatpak commands (they contain spaces)
        if browser_path.startswith('flatpak run'):
            cmd = browser_path.split() + [f'--app={url}']
        else:
            cmd = [browser_path, f'--app={url}']
        
        # Additional flags for better app experience
        cmd.extend([
            '--no-first-run',
            '--disable-default-apps',
            '--disable-features=TranslateUI',
            '--disable-extensions'
        ])
        
        print(f"Launching Chromium app mode with: {browser_path}")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Error launching {browser_path}: {e}")
        return False


def launch_default_browser(url):
    """
    Launch URL using default system browser.
    
    Args:
        url (str): URL to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("Launching with default browser...")
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"Error opening with default browser: {e}")
        return False


def launch_webapp(url, mode='auto'):
    """
    Main function to launch web app based on mode and operating system.
    
    Args:
        url (str): URL to open
        mode (str): Launch mode ('auto', 'pywebview', 'browser')
    """
    system = platform.system().lower()
    print(f"Detected operating system: {system}")
    print(f"Launch mode: {mode}")
    
    success = False
    
    if mode == 'pywebview':
        # Priority: PyWebView -> Chromium -> Default Browser
        if check_pywebview():
            success = launch_pywebview(url)
        
        if not success:
            print("PyWebView failed or not available, trying Chromium app mode...")
            browser_path = find_chromium_browser()
            if browser_path:
                success = launch_chromium_app(browser_path, url)
        
        if not success:
            print("Chromium app mode failed, falling back to default browser...")
            success = launch_default_browser(url)
            
    elif mode == 'browser':
        # Priority: Chromium -> PyWebView -> Default Browser
        browser_path = find_chromium_browser()
        if browser_path:
            success = launch_chromium_app(browser_path, url)
        
        if not success:
            print("Chromium app mode failed, trying PyWebView...")
            if check_pywebview():
                success = launch_pywebview(url)
        
        if not success:
            print("PyWebView failed or not available, falling back to default browser...")
            success = launch_default_browser(url)
            
    else:  # mode == 'auto' or default
        # Priority: PyWebView -> Chromium -> Default Browser
        if check_pywebview():
            success = launch_pywebview(url)
        
        if not success:
            print("PyWebView failed or not available, trying Chromium app mode...")
            browser_path = find_chromium_browser()
            if browser_path:
                success = launch_chromium_app(browser_path, url)
        
        if not success:
            print("Chromium app mode failed, falling back to default browser...")
            success = launch_default_browser(url)
    
    if success:
        print("Successfully launched web app!")
    else:
        print("Failed to launch web app with all methods.")
        sys.exit(1)


def show_help():
    """
    Display help information.
    """
    help_text = """
Web App Launcher Script

Usage: python3 webapp.py [OPTIONS] <URL>

Options:
  --help         Show this help message and exit
  --pywebview    Prioritize PyWebView, fallback to Chromium app mode, then default browser
  --browser      Prioritize Chromium app mode, fallback to PyWebView, then default browser
  --auto         Auto mode (default): Prioritize PyWebView, fallback to Chromium, then default browser

Examples:
  python3 webapp.py http://127.0.0.1:5500
  python3 webapp.py --pywebview http://127.0.0.1:5500
  python3 webapp.py --browser http://127.0.0.1:5500
  python3 webapp.py --auto http://127.0.0.1:5500

Launch Methods:
  1. PyWebView: Creates a native desktop app window using Python's webview library
     - Requires: pip install pywebview
     - Best for: Desktop app-like experience with native window controls
     
  2. Chromium App Mode: Launches in Chromium-based browsers with --app flag
     - Supports: Chrome, Edge, Brave, Vivaldi, Opera, Chromium
     - Best for: Web app experience without browser UI
     
  3. Default Browser: Falls back to system default browser
     - Always available as final fallback
     - Opens in regular browser tab/window

Notes:
  - The script automatically detects your operating system (Windows, macOS, Linux)
  - On Linux, it also checks for Flatpak browser installations
  - URLs must start with http:// or https://
  - PyWebView installation is optional but recommended for best experience
"""
    print(help_text)


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        tuple: (url, mode) where mode is 'auto', 'pywebview', or 'browser'
    """
    if len(sys.argv) < 2:
        print("Error: No arguments provided.")
        show_help()
        sys.exit(1)
    
    # Check for help flag
    if '--help' in sys.argv:
        show_help()
        sys.exit(0)
    
    # Parse arguments
    mode = 'auto'  # default mode
    url = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--pywebview':
            mode = 'pywebview'
        elif arg == '--browser':
            mode = 'browser'
        elif arg == '--auto':
            mode = 'auto'
        elif arg.startswith('--'):
            print(f"Error: Unknown option '{arg}'")
            show_help()
            sys.exit(1)
        else:
            # This should be the URL
            if url is None:
                url = arg
            else:
                print("Error: Multiple URLs provided. Only one URL is allowed.")
                sys.exit(1)
    
    if url is None:
        print("Error: No URL provided.")
        show_help()
        sys.exit(1)
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    return url, mode


def main():
    """
    Main entry point of the script.
    """
    url, mode = parse_arguments()
    
    print(f"Launching web app: {url}")
    launch_webapp(url, mode)


if __name__ == "__main__":
    main()
