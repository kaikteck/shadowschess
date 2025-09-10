# Overview

"In the Shadows" is a strategic analysis web application designed as a personal laboratory for developing and documenting chess and gaming strategies. The application focuses on a specific strategic concept called "In the Shadows" - a methodology that uses partial execution of known moves to create deception, while positioning a hidden piece or movement to deliver the decisive blow. The platform serves as both a learning tool and a documentation system for strategic insights.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses a traditional server-side rendered architecture with Flask templates and Jinja2 templating engine. The frontend consists of multiple sections:
- **Base Template System**: Uses template inheritance with `base.html` as the master template containing navigation, flash messaging, and common layout elements
- **Responsive Design**: CSS Grid and Flexbox-based responsive layout with a dark theme optimized for focus and readability
- **Interactive Elements**: JavaScript-enhanced forms with auto-resizing textareas, tab functionality, and dynamic chess board visualization
- **Navigation Structure**: Fixed navigation bar with sections for Theory, Examples, Concepts, and home page

## Backend Architecture
Built on Flask web framework with the following architectural decisions:
- **MVC Pattern**: Separation of concerns with models, views (templates), and controllers (Flask routes)
- **Session-Based Storage**: Uses Flask sessions for temporary data storage (teoria content)
- **Database Integration**: SQLAlchemy ORM with Flask-SQLAlchemy extension for database operations
- **Environment-Based Configuration**: Database URLs and secret keys configured via environment variables with fallback defaults
- **Request Handling**: Form-based POST requests for data submission with flash messaging for user feedback

## Data Storage Solutions
- **Primary Database**: SQLAlchemy-based ORM with support for both SQLite (development) and PostgreSQL (production)
- **Connection Management**: Configured with connection pooling (pool_recycle: 300 seconds, pool_pre_ping enabled)
- **Session Storage**: Flask sessions for temporary user data
- **Model Structure**: Simple relational model with `Exemplo` entity containing strategy examples with timestamps

## Authentication and Authorization
Currently implements a basic session-based system without user authentication. All data is accessible to anyone with application access. The session secret is configured via environment variables for security.

## Key Design Patterns
- **Template Inheritance**: Consistent UI through base template extension
- **Environment Configuration**: Twelve-factor app compliance with environment-based settings
- **Flash Messaging**: User feedback system for form submissions and actions
- **Responsive Components**: Mobile-first CSS approach with flexible grid systems

# External Dependencies

## Frontend Dependencies
- **Font Awesome 6.0.0**: Icon library for consistent iconography throughout the interface
- **Custom CSS**: Self-contained styling system with dark theme and chess-specific components
- **Chess Board System**: Visual-only boards for analysis (Fundamentos) with proper coordinate display and responsive design
- **Favicon**: Custom chess king icon (256x256px) for enhanced branding

## Backend Dependencies
- **Flask**: Core web framework for routing and request handling
- **Flask-SQLAlchemy**: ORM integration for database operations
- **SQLAlchemy**: Database toolkit and ORM with DeclarativeBase
- **Werkzeug ProxyFix**: Middleware for handling proxy headers in production environments

## Database Support
- **SQLite**: Default development database (file-based)
- **PostgreSQL**: Production-ready database option via DATABASE_URL environment variable
- **Connection Pooling**: Built-in SQLAlchemy connection management

## Development and Deployment
- **Environment Variables**: DATABASE_URL for database configuration, SESSION_SECRET for security
- **Logging**: Python logging module configured for debugging
- **WSGI Compatibility**: ProxyFix middleware for deployment behind reverse proxies