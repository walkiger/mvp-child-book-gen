# Validation Error Handling Documentation

## File: `app/core/validation_errors.py`

### Overview
Defines validation-specific error classes for handling data validation across different entities in the system (stories, users, characters, etc.).

### Error Classes

#### ValidationError
- **Purpose**: Base validation error class
- **Error Code**: VAL-BASE-001
- **Status Code**: 422
- **Usage**: Base class for all validation errors

#### StoryValidationError
- **Purpose**: Story-specific validation
- **Error Code**: VAL-STORY-001
- **Status Code**: 422
- **Usage**: Story content/metadata validation

#### UserValidationError
- **Purpose**: User data validation
- **Error Code**: VAL-USER-001
- **Status Code**: 422
- **Usage**: User profile/settings validation

#### CharacterValidationError
- **Purpose**: Character data validation
- **Error Code**: VAL-CHAR-001
- **Status Code**: 422
- **Usage**: Character attributes validation

#### ImageValidationError
- **Purpose**: Image data validation
- **Error Code**: VAL-IMG-001
- **Status Code**: 422
- **Usage**: Image format/size validation

### Code Structure Analysis

#### Inheritance Pattern
All validation errors inherit from ValidationError, providing:
- Common validation logic
- Consistent error formatting
- Standard validation utilities

#### Error Code Pattern
Current pattern needs standardization:
- Format: VAL-[ENTITY]-[SPECIFIC]-[NUMBER]
- Entity types: STORY, USER, CHAR, IMG
- Specific codes: REQ (Required), FMT (Format), LEN (Length)

### Improvement Opportunities

#### 1. Standardized Error Codes
```python
class ValidationErrorCodes:
    # Story Validation
    STORY_TITLE_REQ = "VAL-STORY-REQ-001"
    STORY_CONTENT_LEN = "VAL-STORY-LEN-001"
    STORY_FORMAT = "VAL-STORY-FMT-001"
    
    # User Validation
    USER_EMAIL_REQ = "VAL-USER-REQ-001"
    USER_PASSWORD_FMT = "VAL-USER-FMT-001"
    USER_NAME_LEN = "VAL-USER-LEN-001"
    
    # Character Validation
    CHAR_NAME_REQ = "VAL-CHAR-REQ-001"
    CHAR_TRAITS_FMT = "VAL-CHAR-FMT-001"
    CHAR_DESC_LEN = "VAL-CHAR-LEN-001"
    
    # Image Validation
    IMG_FORMAT = "VAL-IMG-FMT-001"
    IMG_SIZE = "VAL-IMG-SIZE-001"
    IMG_DIM = "VAL-IMG-DIM-001"
```

#### 2. Enhanced Validation Context
```python
@dataclass
class ValidationErrorContext:
    entity_type: str
    field_name: str
    received_value: Any
    expected_format: Optional[str]
    min_length: Optional[int]
    max_length: Optional[int]
    allowed_values: Optional[List[Any]]
```

#### 3. Field Validation Rules
```python
class ValidationRules:
    @staticmethod
    def get_rules(entity_type: str, field_name: str) -> Dict[str, Any]:
        rules = {
            "story": {
                "title": {
                    "required": True,
                    "min_length": 3,
                    "max_length": 100
                },
                "content": {
                    "required": True,
                    "min_length": 100,
                    "max_length": 5000
                }
            },
            "user": {
                "email": {
                    "required": True,
                    "format": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                },
                "password": {
                    "required": True,
                    "min_length": 8,
                    "format": r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"
                }
            }
        }
        return rules.get(entity_type, {}).get(field_name, {})
```

### Best Practices

#### Validation Creation
1. Use descriptive field names
2. Provide clear error messages
3. Include validation context
4. Add field requirements
5. Document validation rules

#### Validation Handling
1. Check required fields first
2. Validate format/pattern
3. Check length constraints
4. Verify value ranges
5. Validate relationships

### Integration Points

#### 1. Story Validation Service
```python
class StoryValidator:
    def validate_with_error_handling(
        self,
        story_data: Dict[str, Any]
    ) -> None:
        try:
            self._validate_story(story_data)
        except Exception as e:
            context = ValidationErrorContext(
                entity_type="story",
                field_name=e.field_name,
                received_value=story_data.get(e.field_name),
                expected_format=ValidationRules.get_rules("story", e.field_name)
            )
            raise StoryValidationError(str(e), context=context)
```

#### 2. User Validation Service
```python
class UserValidator:
    def validate_with_error_handling(
        self,
        user_data: Dict[str, Any]
    ) -> None:
        try:
            self._validate_user(user_data)
        except Exception as e:
            context = ValidationErrorContext(
                entity_type="user",
                field_name=e.field_name,
                received_value=user_data.get(e.field_name),
                expected_format=ValidationRules.get_rules("user", e.field_name)
            )
            raise UserValidationError(str(e), context=context)
```

### Validation Metrics

#### 1. Validation Statistics
```python
class ValidationMetrics:
    def __init__(self):
        self.validation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
    def record_validation(self, entity_type: str, success: bool):
        self.validation_counts[entity_type] += 1
        if not success:
            self.error_counts[entity_type] += 1
```

#### 2. Performance Monitoring
```python
class ValidationMonitor:
    def __init__(self):
        self.metrics = ValidationMetrics()
        
    def monitor_validation(self, entity_type: str) -> ContextManager:
        try:
            yield
            self.metrics.record_validation(entity_type, True)
        except ValidationError:
            self.metrics.record_validation(entity_type, False)
            raise
```

### Testing Requirements

#### Test Scenarios
1. Required field validation
2. Format validation
3. Length validation
4. Range validation
5. Relationship validation

#### Performance Tests
1. Validation speed
2. Error rate tracking
3. Field coverage
4. Rule consistency
5. Edge cases

### Future Enhancements
1. Add custom validators
2. Implement async validation
3. Add nested validation
4. Enhance error messages
5. Add validation caching 