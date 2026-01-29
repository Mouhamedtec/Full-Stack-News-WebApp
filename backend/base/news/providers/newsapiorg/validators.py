import re
from urllib.parse import urlparse

def url_validator(url):
    """
    Validate a URL to ensure it is well-formed and not pointing to local or private resources.
    Args:
        url (str): The URL to validate.
    Returns:
        bool: True if the URL is valid and safe, False otherwise.
    """
    try:
        pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/.*)?$',
            re.IGNORECASE
        )

        if not pattern.match(url):
            return False

        # Parse URL to extract host
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # Block localhost
        if hostname.lower() == 'localhost':
            return False

        # Block private IP ranges
        if hostname.replace('.', '').isdigit():
            ip_parts = list(map(int, hostname.split('.')))

            # Validate that all octets are in valid range (0-255)
            if len(ip_parts) != 4 or any(octet < 0 or octet > 255 for octet in ip_parts):
                return False

            # Check for private IP ranges
            if (ip_parts[0] == 10) or \
            (ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31) or \
            (ip_parts[0] == 192 and ip_parts[1] == 168) or \
            (ip_parts[0] == 127):  # Localhost IP
                return False
        return True
    except Exception:
        return False
