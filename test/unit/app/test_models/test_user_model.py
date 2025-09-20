"""
Unit tests for user models (app/models/user.py)
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.models.user import (
    User,
    UserCreate,
    UserModify,
    UserResponse,
    UserStatus,
    UserDataUsageResetStrategy,
    UserExpireStrategy,
    UserBase
)


class TestUserBaseModel:
    """Test UserBase model validation and functionality"""
    
    def test_user_base_valid_creation(self):
        """Test valid UserBase model creation"""
        user_data = {
            "username": "testuser123",
            "expire_strategy": UserExpireStrategy.NEVER,
            "data_limit": 10737418240,  # 10GB
            "data_limit_reset_strategy": UserDataUsageResetStrategy.no_reset,
            "note": "Test user"
        }
        
        user = UserBase(**user_data)
        
        assert user.username == "testuser123"
        assert user.expire_strategy == UserExpireStrategy.NEVER
        assert user.data_limit == 10737418240
        assert user.note == "Test user"
        assert len(user.key) == 32  # Default key generation
    
    def test_user_base_username_validation(self):
        """Test username validation rules"""
        valid_usernames = [
            "user123",
            "test_user",
            "user",
            "u" * 32  # Max length
        ]
        
        for username in valid_usernames:
            user = UserBase(
                username=username,
                expire_strategy=UserExpireStrategy.NEVER
            )
            assert user.username == username.lower()
    
    def test_user_base_invalid_username(self):
        """Test invalid username validation"""
        invalid_usernames = [
            "",  # Empty
            "ab",  # Too short
            "a" * 33,  # Too long
            "user@test",  # Invalid characters
            "user space",  # Spaces
            "user-dash",  # Dashes
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValidationError):
                UserBase(
                    username=username,
                    expire_strategy=UserExpireStrategy.NEVER
                )
    
    def test_user_base_data_limit_validation(self):
        """Test data limit validation"""
        # Valid data limits
        valid_limits = [0, 1073741824, 10737418240, None]
        
        for limit in valid_limits:
            user = UserBase(
                username="testuser",
                expire_strategy=UserExpireStrategy.NEVER,
                data_limit=limit
            )
            assert user.data_limit == limit
        
        # Invalid data limits
        with pytest.raises(ValidationError):
            UserBase(
                username="testuser",
                expire_strategy=UserExpireStrategy.NEVER,
                data_limit=-1  # Negative limit
            )
    
    def test_user_base_note_length_validation(self):
        """Test note length validation"""
        # Valid note
        valid_note = "a" * 500  # Max length
        user = UserBase(
            username="testuser",
            expire_strategy=UserExpireStrategy.NEVER,
            note=valid_note
        )
        assert user.note == valid_note
        
        # Invalid note (too long)
        with pytest.raises(ValidationError):
            UserBase(
                username="testuser",
                expire_strategy=UserExpireStrategy.NEVER,
                note="a" * 501  # Over limit
            )


class TestUserExpireStrategyValidation:
    """Test user expire strategy validation"""
    
    def test_never_expire_strategy(self):
        """Test NEVER expire strategy validation"""
        user = UserBase(
            username="neveruser",
            expire_strategy=UserExpireStrategy.NEVER,
            expire_date=datetime.utcnow() + timedelta(days=30),  # Should be ignored
            usage_duration=86400,  # Should be ignored
            activation_deadline=datetime.utcnow() + timedelta(days=1)  # Should be ignored
        )
        
        # All expire-related fields should be None for NEVER strategy
        assert user.expire_date is None
        assert user.usage_duration is None
        assert user.activation_deadline is None
    
    def test_fixed_date_expire_strategy_valid(self):
        """Test valid FIXED_DATE expire strategy"""
        expire_date = datetime.utcnow() + timedelta(days=30)
        
        user = UserBase(
            username="fixeduser",
            expire_strategy=UserExpireStrategy.FIXED_DATE,
            expire_date=expire_date
        )
        
        assert user.expire_date == expire_date
        assert user.usage_duration is None
        assert user.activation_deadline is None
    
    def test_fixed_date_expire_strategy_invalid(self):
        """Test invalid FIXED_DATE expire strategy (missing expire_date)"""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(
                username="fixeduser",
                expire_strategy=UserExpireStrategy.FIXED_DATE,
                expire_date=None  # Missing required expire_date
            )
        
        assert "expire_strategy cannot be fixed_date without a valid expire date" in str(exc_info.value)
    
    def test_start_on_first_use_expire_strategy_valid(self):
        """Test valid START_ON_FIRST_USE expire strategy"""
        usage_duration = 86400 * 30  # 30 days in seconds
        activation_deadline = datetime.utcnow() + timedelta(days=1)
        
        user = UserBase(
            username="firstuseuser",
            expire_strategy=UserExpireStrategy.START_ON_FIRST_USE,
            usage_duration=usage_duration,
            activation_deadline=activation_deadline
        )
        
        assert user.usage_duration == usage_duration
        assert user.activation_deadline == activation_deadline
        assert user.expire_date is None  # Should be None for this strategy
    
    def test_start_on_first_use_expire_strategy_invalid(self):
        """Test invalid START_ON_FIRST_USE expire strategy (missing usage_duration)"""
        with pytest.raises(ValidationError) as exc_info:
            UserBase(
                username="firstuseuser",
                expire_strategy=UserExpireStrategy.START_ON_FIRST_USE,
                usage_duration=None  # Missing required usage_duration
            )
        
        assert "expire_strategy cannot be start_on_first_use without a valid usage_duration" in str(exc_info.value)
    
    def test_usage_duration_limit_validation(self):
        """Test usage duration limit validation"""
        max_duration = 9999 * 365 * 24 * 60 * 60  # 9999 years
        
        # Valid duration
        user = UserBase(
            username="durationuser",
            expire_strategy=UserExpireStrategy.START_ON_FIRST_USE,
            usage_duration=max_duration
        )
        assert user.usage_duration == max_duration
        
        # Invalid duration (too long)
        with pytest.raises(ValidationError):
            UserBase(
                username="durationuser",
                expire_strategy=UserExpireStrategy.START_ON_FIRST_USE,
                usage_duration=max_duration + 1
            )


class TestUserCreateModel:
    """Test UserCreate model"""
    
    def test_user_create_valid(self):
        """Test valid UserCreate model"""
        user_data = {
            "username": "newuser123",
            "expire_strategy": "start_on_first_use",
            "usage_duration": 86400 * 14,  # 14 days
            "activation_deadline": datetime.utcnow() + timedelta(days=1),
            "data_limit": 10737418240,
            "service_ids": [1, 2, 3]
        }
        
        user = UserCreate(**user_data)
        
        assert user.username == "newuser123"
        assert user.service_ids == [1, 2, 3]
        assert user.usage_duration == 86400 * 14
    
    def test_user_create_default_service_ids(self):
        """Test UserCreate with default empty service_ids"""
        user = UserCreate(
            username="defaultuser",
            expire_strategy=UserExpireStrategy.NEVER
        )
        
        assert user.service_ids == []
    
    def test_user_create_json_schema_example(self):
        """Test UserCreate JSON schema example is valid"""
        example_data = {
            "username": "user1234",
            "service_ids": [1, 2, 3],
            "expire_strategy": "start_on_first_use",
            "usage_duration": 86400 * 14,
            "activation_deadline": "2024-11-03T20:30:00",
            "data_limit": 0,
            "data_limit_reset_strategy": "no_reset",
            "note": "",
        }
        
        # Convert string datetime to datetime object
        example_data["activation_deadline"] = datetime.fromisoformat(example_data["activation_deadline"])
        
        user = UserCreate(**example_data)
        
        assert user.username == "user1234"
        assert user.service_ids == [1, 2, 3]


class TestUserModifyModel:
    """Test UserModify model"""
    
    def test_user_modify_partial_update(self):
        """Test UserModify allows partial updates"""
        modify_data = {
            "data_limit": 21474836480,  # 20GB
            "note": "Updated note"
        }
        
        user_modify = UserModify(**modify_data)
        
        assert user_modify.data_limit == 21474836480
        assert user_modify.note == "Updated note"
        assert user_modify.username is None
        assert user_modify.expire_strategy is None
    
    def test_user_modify_all_fields_optional(self):
        """Test that all UserModify fields are optional"""
        user_modify = UserModify()
        
        # All fields should be None by default
        assert user_modify.username is None
        assert user_modify.expire_strategy is None
        assert user_modify.expire_date is None
        assert user_modify.usage_duration is None
        assert user_modify.data_limit is None
        assert user_modify.service_ids is None
    
    def test_user_modify_username_validation(self):
        """Test UserModify username validation when provided"""
        # Valid username
        user_modify = UserModify(username="modifieduser")
        assert user_modify.username == "modifieduser"
        
        # Invalid username
        with pytest.raises(ValidationError):
            UserModify(username="invalid@user")
    
    def test_user_modify_json_schema_example(self):
        """Test UserModify JSON schema example is valid"""
        example_data = {
            "username": "mammad1234",
            "service_ids": [1, 2, 3],
            "expire_strategy": "fixed_date",
            "expire_date": "2023-11-03T20:30:00",
            "data_limit": 0,
            "data_limit_reset_strategy": "no_reset",
            "note": "",
        }
        
        # Convert string datetime to datetime object
        example_data["expire_date"] = datetime.fromisoformat(example_data["expire_date"])
        
        user_modify = UserModify(**example_data)
        
        assert user_modify.username == "mammad1234"
        assert user_modify.service_ids == [1, 2, 3]


class TestUserResponseModel:
    """Test UserResponse model"""
    
    def test_user_response_required_fields(self):
        """Test UserResponse model with required fields"""
        base_data = {
            "username": "responseuser",
            "expire_strategy": UserExpireStrategy.NEVER,
        }
        
        response_data = {
            **base_data,
            "id": 1,
            "activated": True,
            "is_active": True,
            "expired": False,
            "data_limit_reached": False,
            "enabled": True,
            "used_traffic": 1073741824,  # 1GB
            "lifetime_used_traffic": 2147483648,  # 2GB
            "sub_revoked_at": None,
            "created_at": datetime.utcnow(),
            "service_ids": [1, 2],
            "subscription_url": "https://example.com/sub/abc123",
            "owner_username": None,
            "traffic_reset_at": None
        }
        
        user_response = UserResponse(**response_data)
        
        assert user_response.id == 1
        assert user_response.activated == True
        assert user_response.used_traffic == 1073741824
        assert user_response.service_ids == [1, 2]
        assert "example.com" in user_response.subscription_url


class TestUserEnums:
    """Test user-related enums"""
    
    def test_user_status_enum(self):
        """Test UserStatus enum values"""
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
    
    def test_user_data_usage_reset_strategy_enum(self):
        """Test UserDataUsageResetStrategy enum values"""
        assert UserDataUsageResetStrategy.no_reset == "no_reset"
        assert UserDataUsageResetStrategy.day == "day"
        assert UserDataUsageResetStrategy.week == "week"
        assert UserDataUsageResetStrategy.month == "month"
        assert UserDataUsageResetStrategy.year == "year"
    
    def test_user_expire_strategy_enum(self):
        """Test UserExpireStrategy enum values"""
        assert UserExpireStrategy.NEVER == "never"
        assert UserExpireStrategy.FIXED_DATE == "fixed_date"
        assert UserExpireStrategy.START_ON_FIRST_USE == "start_on_first_use"


class TestUserModelIntegration:
    """Test user model integration scenarios"""
    
    def test_user_model_backwards_compatibility(self):
        """Test User model backwards compatibility"""
        # User should be an alias for UserBase
        user_data = {
            "username": "compatuser",
            "expire_strategy": UserExpireStrategy.NEVER
        }
        
        user_base = UserBase(**user_data)
        user_alias = User(**user_data)
        
        assert user_base.username == user_alias.username
        assert user_base.expire_strategy == user_alias.expire_strategy
    
    def test_user_key_generation_uniqueness(self):
        """Test that user key generation produces unique keys"""
        keys = set()
        
        for i in range(100):
            user = UserBase(
                username=f"user{i}",
                expire_strategy=UserExpireStrategy.NEVER
            )
            keys.add(user.key)
        
        # All keys should be unique
        assert len(keys) == 100
        
        # All keys should be 32 characters (16 bytes hex)
        for key in keys:
            assert len(key) == 32
            assert all(c in "0123456789abcdef" for c in key)
    
    def test_user_model_field_constraints(self):
        """Test various field constraints across user models"""
        # Test maximum values
        max_data_limit = 2**63 - 1  # Max BigInteger
        
        user = UserBase(
            username="maxuser",
            expire_strategy=UserExpireStrategy.NEVER,
            data_limit=max_data_limit
        )
        
        assert user.data_limit == max_data_limit


@pytest.mark.parametrize("strategy,additional_fields,should_be_valid", [
    (UserExpireStrategy.NEVER, {}, True),
    (UserExpireStrategy.FIXED_DATE, {"expire_date": datetime.utcnow() + timedelta(days=30)}, True),
    (UserExpireStrategy.FIXED_DATE, {}, False),  # Missing expire_date
    (UserExpireStrategy.START_ON_FIRST_USE, {"usage_duration": 86400}, True),
    (UserExpireStrategy.START_ON_FIRST_USE, {}, False),  # Missing usage_duration
])
def test_expire_strategy_validation_scenarios(strategy, additional_fields, should_be_valid):
    """Test various expire strategy validation scenarios"""
    user_data = {
        "username": "testuser",
        "expire_strategy": strategy,
        **additional_fields
    }
    
    if should_be_valid:
        user = UserBase(**user_data)
        assert user.expire_strategy == strategy
    else:
        with pytest.raises(ValidationError):
            UserBase(**user_data)