"""
Platform management service
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from crypto_db.models import Platform


class PlatformService:
    """Service for managing trading platforms"""

    @staticmethod
    def create_platform(db: Session, name: str, description: Optional[str] = None) -> Platform:
        """
        Create a new platform
        """
        platform = Platform(name=name, description=description)

        db.add(platform)
        db.commit()
        db.refresh(platform)

        return platform

    @staticmethod
    def get_platform(db: Session, platform_id: int) -> Optional[Platform]:
        """
        Get platform by ID
        """
        return db.query(Platform).filter(Platform.id == platform_id).first()

    @staticmethod
    def get_platform_by_name(db: Session, name: str) -> Optional[Platform]:
        """
        Get platform by name
        """
        return db.query(Platform).filter(Platform.name == name).first()

    @staticmethod
    def get_all_platforms(db: Session) -> List[Platform]:
        """
        Get all platforms
        """
        return db.query(Platform).order_by(Platform.name).all()

    @staticmethod
    def update_platform(
        db: Session, platform_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Platform]:
        """
        Update platform details
        """
        platform = db.query(Platform).filter(Platform.id == platform_id).first()

        if platform:
            if name:
                platform.name = name
            if description is not None:
                platform.description = description

            db.commit()
            db.refresh(platform)

        return platform

    @staticmethod
    def delete_platform(db: Session, platform_id: int) -> bool:
        """
        Delete a platform (only if no transactions exist)
        """
        platform = db.query(Platform).filter(Platform.id == platform_id).first()

        if platform:
            # Check if platform has transactions
            if platform.crypto_transactions or platform.fiat_deposits:
                return False

            db.delete(platform)
            db.commit()
            return True

        return False
