from app import models, schemas
import secrets
import bcrypt


class UserService:
    def __init__(self, db):
        self.db = db

    # ── Create ──────────────────────────────────────────────────────────────

    def create_user(self, user: schemas.UserCreate):
        """Register a new user. Raises ValueError if email/username is taken."""
        existing_user = self.db.query(models.User).filter(
            (models.User.email == user.email) | (models.User.username == user.username)
        ).first()
        if existing_user:
            raise ValueError("Email or username already exists")

        new_user = models.User(
            email=user.email,
            full_name=user.full_name,
            username=user.username,
            password_hash=self.hash_password(user.password),
            phone=user.phone,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    # ── Session ─────────────────────────────────────────────────────────────

    def create_user_session(self, userLogin: schemas.UserLogin):
        """Authenticate and create a new session. Raises ValueError on bad credentials."""
        user = self.authenticate_user(userLogin.email, userLogin.password)
        if not user:
            raise ValueError("Invalid email or password")

        session_id = self.generate_session_id()
        new_session = models.UserSession(user_id=user.id, session_id=session_id)
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)

        # Deactivate all previous sessions for this user
        self.deactivate_old_sessions(user.id, new_session.id)

        # Merge guest cart into the new authenticated session
        if userLogin.temp_session_id:
            self.cart_item_transfer(userLogin.temp_session_id, session_id)

        return schemas.UserLoginResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            username=user.username,
            session_id=session_id,
        )

    def logout_user(self, session_id: str):
        session = self.db.query(models.UserSession).filter(
            models.UserSession.session_id == session_id
        ).first()
        if session:
            session.is_active = False
            self.db.commit()

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_current_user(self, session_id: str):
        """Return the User linked to an active session. Raises ValueError if not found."""
        user = self.db.query(models.User).filter(
            models.User.UserSessions.any(session_id=session_id, is_active=True)
        ).first()
        if not user:
            raise ValueError("No active session found for the given session_id")
        return user

    def get_user_by_session(self, session_id: str):
        return self.db.query(models.User).filter(
            models.User.UserSessions.any(session_id=session_id, is_active=True)
        ).first()

    def is_session_active(self, session_id: str) -> bool:
        session = self.db.query(models.UserSession).filter(
            models.UserSession.session_id == session_id
        ).first()
        return session.is_active if session else False

    # ── Update ───────────────────────────────────────────────────────────────

    def Update_user(self, session_id: str, user_update: schemas.UserUpdate):
        """Update user profile. Raises ValueError if no active session found."""
        user = self.db.query(models.User).filter(
            models.User.UserSessions.any(session_id=session_id, is_active=True)
        ).first()
        if not user:
            raise ValueError("User session not found or session is inactive")

        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.phone is not None:
            user.phone = user_update.phone
        if user_update.password is not None:
            user.password_hash = self.hash_password(user_update.password)

        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Helpers ──────────────────────────────────────────────────────────────

    def authenticate_user(self, email: str, password: str):
        user = self.db.query(models.User).filter(models.User.email == email).first()
        if not user or not user.verify_password(password):
            return None
        return user

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def generate_session_id(self) -> str:
        return secrets.token_hex(16)

    def deactivate_old_sessions(self, user_id: int, current_session_id: int):
        old_sessions = self.db.query(models.UserSession).filter(
            models.UserSession.user_id == user_id,
            models.UserSession.id != current_session_id,
        ).all()
        for s in old_sessions:
            s.is_active = False
        self.db.commit()

    def cart_item_transfer(self, old_session_id: str, new_session_id: str):
        """Move a guest cart to the authenticated session after login."""
        cart = self.db.query(models.Cart).filter(
            models.Cart.session_id == old_session_id
        ).first()
        if cart:
            cart.session_id = new_session_id
            self.db.commit()