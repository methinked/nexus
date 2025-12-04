"""
Pre-built Docker service templates for Nexus.

This module contains template definitions for popular homelab services.
Templates are automatically seeded into the database on Core startup.
"""

from typing import Dict, List

# Service template structure:
# - name: Unique identifier (lowercase, no spaces)
# - display_name: Human-readable name
# - description: Service description
# - version: Docker image version
# - category: Service category
# - docker_compose: Docker Compose YAML
# - default_env: Default environment variables
# - icon_url: Icon URL for UI

SERVICE_TEMPLATES: List[Dict] = [
    {
        "name": "pihole",
        "display_name": "Pi-hole",
        "description": "Network-wide ad blocking via DNS sinkhole. Blocks ads and trackers at the network level for all devices.",
        "version": "latest",
        "category": "networking",
        "docker_compose": """version: '3'
services:
  pihole:
    image: pihole/pihole:latest
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "80:80/tcp"
    environment:
      TZ: 'America/New_York'
      WEBPASSWORD: 'admin'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
""",
        "default_env": {
            "TZ": "America/New_York",
            "WEBPASSWORD": "admin",
        },
        "icon_url": "https://wp-cdn.pi-hole.net/wp-content/uploads/2016/12/Vortex-R.png",
    },
    {
        "name": "homeassistant",
        "display_name": "Home Assistant",
        "description": "Open source home automation platform. Control and automate all your smart home devices from one place.",
        "version": "latest",
        "category": "automation",
        "docker_compose": """version: '3'
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:latest
    ports:
      - "8123:8123"
    environment:
      TZ: 'America/New_York'
    volumes:
      - './config:/config'
    restart: unless-stopped
    privileged: true
    network_mode: host
""",
        "default_env": {
            "TZ": "America/New_York",
        },
        "icon_url": "https://www.home-assistant.io/images/home-assistant-logo.svg",
    },
    {
        "name": "prometheus",
        "display_name": "Prometheus",
        "description": "Monitoring system and time series database. Collect and store metrics from your infrastructure.",
        "version": "latest",
        "category": "monitoring",
        "docker_compose": """version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - './prometheus.yml:/etc/prometheus/prometheus.yml'
      - './prometheus-data:/prometheus'
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
""",
        "default_env": {},
        "icon_url": "https://prometheus.io/assets/prometheus_logo_grey.svg",
    },
    {
        "name": "grafana",
        "display_name": "Grafana",
        "description": "Analytics and visualization platform. Create beautiful dashboards for your metrics and logs.",
        "version": "latest",
        "category": "monitoring",
        "docker_compose": """version: '3'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: 'admin'
      GF_INSTALL_PLUGINS: ''
    volumes:
      - './grafana-data:/var/lib/grafana'
    restart: unless-stopped
""",
        "default_env": {
            "GF_SECURITY_ADMIN_PASSWORD": "admin",
            "GF_INSTALL_PLUGINS": "",
        },
        "icon_url": "https://grafana.com/static/img/menu/grafana2.svg",
    },
    {
        "name": "portainer",
        "display_name": "Portainer",
        "description": "Docker container management UI. Manage your Docker containers, images, networks, and volumes through a web interface.",
        "version": "latest",
        "category": "management",
        "docker_compose": """version: '3'
services:
  portainer:
    image: portainer/portainer-ce:latest
    ports:
      - "9000:9000"
      - "8000:8000"
    volumes:
      - '/var/run/docker.sock:/var/run/docker.sock'
      - './portainer-data:/data'
    restart: unless-stopped
""",
        "default_env": {},
        "icon_url": "https://www.portainer.io/hubfs/portainer-logo-black.svg",
    },
    {
        "name": "nginx-proxy-manager",
        "display_name": "Nginx Proxy Manager",
        "description": "Reverse proxy with SSL certificate management. Easily expose your services with automatic Let's Encrypt SSL.",
        "version": "latest",
        "category": "networking",
        "docker_compose": """version: '3'
services:
  nginx-proxy-manager:
    image: 'jc21/nginx-proxy-manager:latest'
    ports:
      - '80:80'
      - '81:81'
      - '443:443'
    environment:
      DB_SQLITE_FILE: '/data/database.sqlite'
    volumes:
      - './data:/data'
      - './letsencrypt:/etc/letsencrypt'
    restart: unless-stopped
""",
        "default_env": {
            "DB_SQLITE_FILE": "/data/database.sqlite",
        },
        "icon_url": "https://nginxproxymanager.com/icon.png",
    },
    {
        "name": "nextcloud",
        "display_name": "Nextcloud",
        "description": "Self-hosted cloud storage and collaboration platform. Your own private cloud for files, calendars, contacts, and more.",
        "version": "latest",
        "category": "storage",
        "docker_compose": """version: '3'
services:
  nextcloud:
    image: nextcloud:latest
    ports:
      - "8080:80"
    environment:
      NEXTCLOUD_ADMIN_USER: 'admin'
      NEXTCLOUD_ADMIN_PASSWORD: 'admin'
      NEXTCLOUD_TRUSTED_DOMAINS: 'localhost'
    volumes:
      - './nextcloud-data:/var/www/html'
    restart: unless-stopped
""",
        "default_env": {
            "NEXTCLOUD_ADMIN_USER": "admin",
            "NEXTCLOUD_ADMIN_PASSWORD": "admin",
            "NEXTCLOUD_TRUSTED_DOMAINS": "localhost",
        },
        "icon_url": "https://nextcloud.com/wp-content/themes/next/assets/img/common/nextcloud-square-logo.png",
    },
]


def get_all_templates() -> List[Dict]:
    """Get all service templates."""
    return SERVICE_TEMPLATES


def get_template_by_name(name: str) -> Dict | None:
    """Get a specific template by name."""
    for template in SERVICE_TEMPLATES:
        if template["name"] == name:
            return template
    return None


def get_templates_by_category(category: str) -> List[Dict]:
    """Get templates filtered by category."""
    return [t for t in SERVICE_TEMPLATES if t["category"] == category]


def get_categories() -> List[str]:
    """Get list of unique categories."""
    return list(set(t["category"] for t in SERVICE_TEMPLATES))
