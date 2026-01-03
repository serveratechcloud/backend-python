from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class RadiusUser(BaseModel):
    __tablename__ = "radius_users"
    
    # RADIUS authentication
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    
    # Service configuration
    profile = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Session limits
    session_timeout = Column(Integer, nullable=True)  # in seconds
    idle_timeout = Column(Integer, nullable=True)     # in seconds
    
    # Bandwidth limits (in Kbps)
    upload_limit = Column(Integer, nullable=True)
    download_limit = Column(Integer, nullable=True)
    
    # Foreign keys
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="radius_user")
    sessions = relationship("RadiusSession", back_populates="radius_user")
    
    def __repr__(self):
        return f"<RadiusUser(username={self.username}, profile={self.profile})>"

class RadiusSession(BaseModel):
    __tablename__ = "radius_sessions"
    
    # Session identification
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(100), index=True, nullable=False)
    
    # NAS information
    nas_ip_address = Column(String(45), nullable=False)
    nas_port_id = Column(String(50), nullable=False)
    nas_port_type = Column(String(50), nullable=True)
    
    # Session timing
    session_time = Column(Integer, nullable=False)  # in seconds
    start_time = Column(DateTime(timezone=True), nullable=False)
    stop_time = Column(DateTime(timezone=True), nullable=True)
    
    # Traffic accounting
    input_octets = Column(BigInteger, default=0, nullable=False)  # Bytes received
    output_octets = Column(BigInteger, default=0, nullable=False)  # Bytes sent
    input_packets = Column(BigInteger, default=0, nullable=False)
    output_packets = Column(BigInteger, default=0, nullable=False)
    
    # Session termination
    terminate_cause = Column(String(50), nullable=True)
    
    # Foreign keys
    radius_user_id = Column(Integer, ForeignKey("radius_users.id"), nullable=True)
    
    # Relationships
    radius_user = relationship("RadiusUser", back_populates="sessions")
    
    def __repr__(self):
        return f"<RadiusSession(session_id={self.session_id}, username={self.username})>"
    
    @property
    def duration(self) -> int:
        """Calculate session duration in seconds."""
        if self.stop_time:
            return int((self.stop_time - self.start_time).total_seconds())
        return self.session_time
    
    @property
    def total_octets(self) -> int:
        """Calculate total data transfer in bytes."""
        return self.input_octets + self.output_octets
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.stop_time is None
