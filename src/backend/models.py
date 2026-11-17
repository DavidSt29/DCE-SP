from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class QRCode(Base):
    """
    Relational model storing QR code metadata and raw binary image data.
    The 'qr_codes' table stores encoded payload, user descriptions, and binary PNG bytes.
    """
    __tablename__ = "qr_codes"

    # Auto-incrementing primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Unique/indexed identifier for the code (e.g. QR-0001)
    code_number = Column(String(100), nullable=False, index=True)
    
    # Optional user-defined description or title
    description = Column(Text, nullable=True)
    
    # Encoded payload (text, URL, etc.)
    content = Column(Text, nullable=False)
    
    # Binary PNG image data (stored as BYTEA in PostgreSQL)
    image_data = Column(LargeBinary, nullable=False)
    
    # Timestamps in UTC
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        """
        Serialize model instance to a JSON-compatible dictionary.
        Binary image bytes are omitted from the JSON response; an image endpoint URL is provided instead.
        """
        return {
            "id": self.id,
            "code_number": self.code_number,
            "description": self.description or "",
            "content": self.content,
            "image_url": f"/api/qrcodes/{self.id}/image",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
