#!/usr/bin/env python3
"""
Web App Launcher Script
Usage: python3 webapp.py <URL>
Example: python3 webapp.py http://127.0.0.1:5500

This script detects the operating system and launches a web URL in app mode:
- Windows: Prioritizes Microsoft Edge, then other Chromium-based browsers
- Linux & macOS: Searches for Chromium-based browsers
- Falls back to default browser if no Chromium-based browser is found
"""

import sys
import os
import platform
import subprocess
import webbrowser
import shutil


def find_browser_executable(browser_names):
    """
    Find the first available browser executable from a list of browser names.
    
    Args:
        browser_names (list): List of browser executable names to search for
        
    Returns:
        str or None: Path to the browser executable if found, None otherwise
    """
    for browser_name in browser_names:
        browser_path = shutil.which(browser_name)
        if browser_path:
            return browser_path
    return None


def get_windows_browsers():
    """
    Get list of Chromium-based browser executables for Windows.
    Prioritizes Microsoft Edge first.
    
    Returns:
        list: List of browser executable names
    """
    return [
        'msedge.exe',
        'chrome.exe',
        'chromium.exe',
        'brave.exe',
        'opera.exe',
        'vivaldi.exe'
    ]


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
        
        print(f"Launching app mode with: {browser_path}")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Error launching {browser_path}: {e}")
        return False


def launch_webapp(url):
    """
    Main function to launch web app based on operating system.
    
    Args:
        url (str): URL to open
    """
    system = platform.system().lower()
    print(f"Detected operating system: {system}")
    
    browser_path = None
    
    if system == 'windows':
        print("Searching for Chromium-based browsers (prioritizing Microsoft Edge)...")
        browser_names = get_windows_browsers()
        browser_path = find_browser_executable(browser_names)
        
    elif system == 'darwin':  # macOS
        print("Searching for Chromium-based browsers on macOS...")
        # First try command-line executables
        browser_names = get_unix_browsers()
        browser_path = find_browser_executable(browser_names)
        
        # If not found, try macOS application bundles (including Homebrew)
        if not browser_path:
            macos_browsers = get_macos_browsers()
            for browser in macos_browsers:
                if os.path.exists(browser):
                    browser_path = browser
                    break
                    
    elif system == 'linux':
        print("Searching for Chromium-based browsers on Linux...")
        # First try standard package installations
        browser_names = get_unix_browsers()
        browser_path = find_browser_executable(browser_names)
        
        # If not found, try Flatpak installations
        if not browser_path:
            print("Checking Flatpak installations...")
            flatpak_browsers = get_flatpak_browsers()
            if flatpak_browsers:
                browser_path = flatpak_browsers[0]  # Use the first available Flatpak browser
        
    else:
        print(f"Unsupported operating system: {system}")
    
    # Try to launch with Chromium-based browser in app mode
    if browser_path:
        print(f"Found browser: {browser_path}")
        if launch_chromium_app(browser_path, url):
            print("Successfully launched web app!")
            return
        else:
            print("Failed to launch with Chromium-based browser.")
    else:
        print("No Chromium-based browser found.")
    
    # Fallback to default browser
    print("Falling back to default browser...")
    try:
        webbrowser.open(url)
        print("Opened with default browser.")
    except Exception as e:
        print(f"Error opening with default browser: {e}")
        sys.exit(1)


def main():
    """
    Main entry point of the script.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 webapp.py <URL>")
        print("Example: python3 webapp.py http://127.0.0.1:5500")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    print(f"Launching web app: {url}")
    launch_webapp(url)


if __name__ == "__main__":
    main()
