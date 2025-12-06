"""
Service template seeding for Nexus Core.

Seeds pre-built service templates into the database on startup.
"""

import logging
from sqlalchemy.orm import Session

from nexus.core.db import create_service, get_service_by_name
from nexus.core.services.service_templates import get_all_templates
from nexus.shared import ServiceCreate

logger = logging.getLogger(__name__)


async def seed_service_templates(db: Session) -> dict:
    """
    Seed pre-built service templates into the database.
    
    This function is idempotent - it will not create duplicates if templates
    already exist in the database.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with seeding results (created, skipped, errors)
    """
    templates = get_all_templates()
    results = {
        "created": [],
        "skipped": [],
        "errors": [],
    }
    
    logger.info(f"Seeding {len(templates)} service templates...")
    
    for template in templates:
        try:
            # Check if template already exists
            existing = get_service_by_name(db, template["name"])
            
            if existing:
                logger.debug(f"Template '{template['name']}' already exists, skipping")
                results["skipped"].append(template["name"])
                continue
            
            # Create service template
            service_create = ServiceCreate(
                name=template["name"],
                display_name=template["display_name"],
                description=template["description"],
                version=template["version"],
                category=template["category"],
                docker_compose=template["docker_compose"],
                default_env=template["default_env"],
                icon_url=template.get("icon_url"),
            )
            
            created_service = create_service(db, service_create)
            logger.info(f"Created template '{template['name']}' (ID: {created_service.id})")
            results["created"].append(template["name"])
            
        except Exception as e:
            logger.error(f"Failed to seed template '{template['name']}': {e}")
            results["errors"].append({
                "name": template["name"],
                "error": str(e),
            })
    
    # Log summary
    logger.info(
        f"Template seeding complete: "
        f"{len(results['created'])} created, "
        f"{len(results['skipped'])} skipped, "
        f"{len(results['errors'])} errors"
    )
    
    return results
