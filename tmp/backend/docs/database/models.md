# Database Models Documentation

## Overview
The database models define the core data structures for the children's book generation system using SQLAlchemy ORM. The models include users, characters, stories, and images, with robust relationships and constraints.

## Components

### Base Models and Mixins

#### TimestampMixin
Provides automatic timestamp tracking:
```python
class TimestampMixin:
    created_at = Column(UTCDateTime, ...)
    updated_at = Column(UTCDateTime, ...)
```

#### UTCDateTime
Custom datetime type for UTC handling:
```python
class UTCDateTime(TypeDecorator):
    # Automatically converts to/from UTC
```

### Core Models

#### User Model
```python
class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    # Fields
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean)
    
    # Relationships
    characters = relationship('Character')
    stories = relationship('Story')
    images = relationship('Image')
```

#### Character Model
```python
class Character(Base, TimestampMixin):
    __tablename__ = 'characters'
    
    # Fields
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    traits = Column(JSON)
    image_prompt = Column(String)
    generated_images = Column(JSON)
    
    # Relationships
    user = relationship('User')
    stories = relationship('Story')
    images = relationship('Image')
```

#### Story Model
```python
class Story(Base, TimestampMixin):
    __tablename__ = 'stories'
    
    # Fields
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    character_id = Column(Integer, ForeignKey('characters.id'))
    title = Column(String)
    content = Column(JSON)
    age_group = Column(String)
    page_count = Column(Integer)
    status = Column(String)
    generation_cost = Column(Float)
    moral_lesson = Column(String)
    story_tone = Column(String)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("age_group IN ('1-2', '3-5', '6-8', '9-12')"),
        CheckConstraint("moral_lesson IN (...)"),
        CheckConstraint("story_tone IN (...)"),
        CheckConstraint("status IN (...)")
    )
```

#### Image Model
```python
class Image(Base):
    __tablename__ = "images"
    
    # Fields
    id = Column(Integer, primary_key=True)
    data = Column(LargeBinary)
    format = Column(String)
    story_id = Column(Integer, ForeignKey("stories.id"))
    character_id = Column(Integer, ForeignKey("characters.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    dalle_version = Column(String)
    generation_cost = Column(Float)
    grid_position = Column(Integer)
    regeneration_count = Column(Integer)
```

## Error Handling

### Error Classes
- `ModelValidationError`: Data validation errors
- `RelationshipError`: Relationship integrity errors
- `ConstraintError`: Constraint violation errors

### Error Patterns
```python
try:
    # Create new story
    story = Story(...)
    session.add(story)
    session.commit()
except ConstraintError as e:
    # Handle constraint violation
    session.rollback()
except RelationshipError as e:
    # Handle relationship error
    session.rollback()
```

## Best Practices

1. **Model Design**
   - Use appropriate column types
   - Implement constraints
   - Define relationships
   - Add indexes for performance

2. **Data Validation**
   - Use SQLAlchemy validators
   - Implement check constraints
   - Validate relationships
   - Handle nullable fields

3. **Relationship Management**
   - Use appropriate cascades
   - Define backref relationships
   - Handle circular dependencies
   - Manage lazy loading

## Integration Points
- SQLAlchemy Session
- Migration System
- Data Validation
- Error Handling

## Testing Requirements

1. **Model Testing**
   - Test field constraints
   - Verify relationships
   - Check default values
   - Validate timestamps

2. **Validation Testing**
   - Test data constraints
   - Check error handling
   - Verify cascades
   - Test unique constraints

3. **Integration Testing**
   - Test with services
   - Verify transactions
   - Check relationships

## Future Improvements

1. **Short-term**
   - Enhanced validation
   - Better error messages
   - Additional indexes
   - Improved constraints

2. **Long-term**
   - Model versioning
   - Advanced relationships
   - Performance optimization
   - Audit logging 