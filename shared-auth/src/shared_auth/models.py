"""
Data models for authentication and user context.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class AuthUser:
    """
    Authenticated user context containing essential user information.
    
    This model represents a user after successful authentication,
    containing all necessary information for authorization decisions.
    """
    
    user_id: str
    """UUID string representing the user in the database"""
    
    email: str
    """User's email address from Auth0 token"""
    
    organization_id: Optional[str] = None
    """Organization UUID if user belongs to an organization"""
    
    roles: List[str] = None
    """List of user roles for role-based access control"""
    
    auth0_subject: Optional[str] = None
    """Original Auth0 subject identifier for reference"""
    
    email_verified: bool = False
    """Whether the user's email has been verified"""
    
    scopes: List[str] = None
    """OAuth2 scopes granted to the user"""
    
    def __post_init__(self) -> None:
        """Initialize default values for mutable fields"""
        if self.roles is None:
            self.roles = []
        if self.scopes is None:
            self.scopes = []
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return "admin" in self.roles
    
    @property
    def is_organization_member(self) -> bool:
        """Check if user belongs to an organization"""
        return self.organization_id is not None
    
    @property
    def has_verified_email(self) -> bool:
        """Check if user's email is verified"""
        return self.email_verified
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: Role name to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles
    
    def has_scope(self, scope: str) -> bool:
        """
        Check if user has a specific OAuth2 scope.
        
        Args:
            scope: Scope name to check
            
        Returns:
            True if user has the scope, False otherwise
        """
        return scope in self.scopes
    
    def has_any_role(self, roles: List[str]) -> bool:
        """
        Check if user has any of the specified roles.
        
        Args:
            roles: List of role names to check
            
        Returns:
            True if user has at least one of the roles, False otherwise
        """
        return any(role in self.roles for role in roles)
    
    def has_all_roles(self, roles: List[str]) -> bool:
        """
        Check if user has all of the specified roles.
        
        Args:
            roles: List of role names to check
            
        Returns:
            True if user has all the roles, False otherwise
        """
        return all(role in self.roles for role in roles)
    
    def to_dict(self) -> dict:
        """
        Convert AuthUser to dictionary for serialization.
        
        Returns:
            Dictionary representation of the user
        """
        return {
            "user_id": self.user_id,
            "email": self.email,
            "organization_id": self.organization_id,
            "roles": self.roles,
            "auth0_subject": self.auth0_subject,
            "email_verified": self.email_verified,
            "scopes": self.scopes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AuthUser":
        """
        Create AuthUser from dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            AuthUser instance
        """
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            organization_id=data.get("organization_id"),
            roles=data.get("roles", []),
            auth0_subject=data.get("auth0_subject"),
            email_verified=data.get("email_verified", False),
            scopes=data.get("scopes", []),
        )
    
    def __str__(self) -> str:
        """String representation of the user"""
        org_info = f" (org: {self.organization_id})" if self.organization_id else ""
        return f"AuthUser(id={self.user_id}, email={self.email}{org_info})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging"""
        return (
            f"AuthUser("
            f"user_id='{self.user_id}', "
            f"email='{self.email}', "
            f"organization_id={self.organization_id!r}, "
            f"roles={self.roles!r}, "
            f"auth0_subject={self.auth0_subject!r}, "
            f"email_verified={self.email_verified}, "
            f"scopes={self.scopes!r}"
            f")"
        )


@dataclass
class JWTPayload:
    """
    Typed JWT payload model for better type safety.
    
    Represents the standard and custom claims in Auth0 JWT tokens.
    """
    
    # Standard JWT claims
    sub: str  # Subject (user identifier)
    email: str  # User email
    aud: str  # Audience (API identifier)
    iss: str  # Issuer (Auth0 domain)
    iat: int  # Issued at (timestamp)
    exp: int  # Expires at (timestamp)
    
    # Optional standard claims
    email_verified: bool = False
    scope: str = ""
    
    # Custom claims
    organization_id: Optional[str] = None
    roles: List[str] = None
    
    def __post_init__(self) -> None:
        """Initialize default values for mutable fields"""
        if self.roles is None:
            self.roles = []
    
    @property
    def scopes(self) -> List[str]:
        """Get scopes as a list from the scope string"""
        return self.scope.split() if self.scope else []
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired"""
        import time
        return time.time() > self.exp
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTPayload":
        """
        Create JWTPayload from JWT token dictionary.
        
        Args:
            data: JWT payload dictionary
            
        Returns:
            JWTPayload instance
        """
        # Extract roles from various possible claim locations
        roles = []
        role_claims = [
            "roles",
            "user_roles",
            "https://resumematch.com/roles",
        ]
        
        for claim in role_claims:
            if claim in data:
                roles = data[claim]
                if isinstance(roles, str):
                    roles = [roles]
                break
        
        return cls(
            sub=data["sub"],
            email=data["email"],
            aud=data["aud"],
            iss=data["iss"],
            iat=data["iat"],
            exp=data["exp"],
            email_verified=data.get("email_verified", False),
            scope=data.get("scope", ""),
            organization_id=data.get("organization_id") or data.get("org_id"),
            roles=roles or [],
        )
