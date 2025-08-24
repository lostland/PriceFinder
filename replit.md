# Overview

This is a Python Flask web application that scrapes price information from websites. Users can input any website URL, and the application will extract and display the top 5 prices found on that page. The app supports multiple currencies (Korean Won, USD, Euro, British Pound, Japanese Yen) and provides a clean, responsive web interface with real-time feedback.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Technology**: Pure HTML5, CSS3, and vanilla JavaScript
- **Framework**: Bootstrap 5 with dark theme for responsive UI
- **Design**: Single-page application with form-based interaction
- **User Experience**: Real-time loading states, error handling, responsive design, and multilingual support (Korean/English)
- **Language Support**: Dynamic language switching with comprehensive translation system

## Backend Architecture
- **Framework**: Flask (Python web framework)
- **Structure**: Modular design with separate scraper functionality
- **API Design**: RESTful JSON API with POST endpoint for scraping
- **Session Management**: Flask sessions with configurable secret key
- **Middleware**: ProxyFix for handling reverse proxy headers

## Web Scraping Engine
- **Library**: BeautifulSoup4 for HTML parsing
- **HTTP Client**: Requests library with browser-like headers
- **Pattern Matching**: Regular expressions for multi-currency price detection
- **Content Processing**: Automatic script/style removal and text extraction
- **Error Handling**: Comprehensive exception handling and timeout management

## Data Processing
- **Price Detection**: Multi-currency regex patterns for global price formats
- **Content Extraction**: Context-aware price extraction with surrounding text
- **Result Ranking**: Returns top 5 most relevant price matches
- **Response Format**: Structured JSON with price values and contextual information
- **Error Handling**: Invalid link detection with user-friendly modal feedback
- **UI Enhancements**: Clean card display without "price found" badges, focus on price information

# External Dependencies

## Python Libraries
- **Flask**: Web framework for HTTP handling and templating
- **BeautifulSoup4**: HTML/XML parsing and web scraping
- **Requests**: HTTP client library for web requests
- **Werkzeug**: WSGI utilities and middleware

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Replit Bootstrap Theme**: Dark theme styling

## Runtime Environment
- **Python**: Server-side runtime
- **Environment Variables**: SESSION_SECRET for Flask session management
- **WSGI**: Web server gateway interface compatibility