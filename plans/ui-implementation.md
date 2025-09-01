# UI Implementation with FastAPI, Jinja2 Templates and HTMX

## Goal
Implement a basic web UI served by FastAPI backend using Jinja2 templates with HTMX for dynamic interactions and Pico CSS for clean, semantic styling. The UI will include a landing page, login/signup page, user dashboard, and profile page with proper navigation and authentication integration.

## Implementation Blueprint

### Phase 1: Setup and Configuration
- [x] Install required dependencies (jinja2, jinja2-fragments)
- [x] Create templates directory structure
- [x] Configure FastAPI to serve templates with Jinja2Blocks
- [x] Add session middleware for maintaining login state
- [x] Set up cookie-based JWT storage configuration

### Phase 2: Base Template and Navigation
- [x] Create base.html template with Pico CSS CDN link and HTMX script
- [x] Set up semantic HTML structure using Pico's conventions
- [x] Implement navigation using semantic <nav> with signup link aligned right
- [x] Add data-theme support for light/dark mode toggle
- [x] Create fragments for dynamic navigation updates

### Phase 3: Landing Page
- [x] Create index.html template extending base.html
- [x] Add welcome content using Pico's semantic container structure
- [x] Ensure navigation shows "Signup" when not logged in
- [x] Create FastAPI route to serve landing page
- [x] Use Pico's hero/article patterns for content sections

### Phase 4: Login/Signup Page
- [x] Create auth.html template with both login and signup forms
- [x] Use Pico's form styling with semantic HTML (no classes needed)
- [x] Implement form switching using HTMX with Pico's tabs or details/summary
- [x] Add HTMX attributes for form submission without page reload
- [x] Create FastAPI routes for serving auth page
- [x] Integrate with existing /auth/register and /auth/token endpoints
- [x] Handle JWT token storage in httpOnly cookies
- [x] Implement success/error message display using Pico's mark/ins elements

### Phase 5: User Dashboard
- [x] Create dashboard.html template for logged-in users
- [x] Display "Hello" message centered using Pico's container
- [x] Show username in top-right navigation
- [x] Create protected FastAPI route for dashboard
- [x] Implement authentication check using JWT from cookies
- [x] Redirect to login page if not authenticated

### Phase 6: Profile Page
- [x] Create profile.html template to display user information
- [x] Show user details using Pico's article/card patterns
- [x] Display fields in semantic definition lists or tables
- [x] Make username in navigation clickable with HTMX
- [x] Create protected FastAPI route for profile page
- [x] Integrate with existing /users/me endpoint

### Phase 7: Authentication Flow Integration
- [x] Implement JWT token storage in httpOnly cookies
- [x] Create authentication dependency for template routes
- [x] Add logout functionality with HTMX
- [x] Implement automatic redirect after login
- [x] Handle expired tokens gracefully

### Phase 8: Enhancements and UX
- [x] Add Pico's loading states for HTMX requests (aria-busy attribute)
- [x] Implement theme toggle button for light/dark mode
- [x] Use Pico's grid system for responsive layouts where needed
- [x] Add custom CSS variables only if needed for brand colors
- [x] Ensure all forms use Pico's validation styling

### Phase 9: Error Handling and Validation
- [x] Implement client-side form validation
- [x] Display server-side validation errors using HTMX
- [x] Add proper error pages (404, 500)
- [x] Handle network errors gracefully

### Phase 10: Testing and Refinement
- [x] Test authentication flow end-to-end
- [x] Verify HTMX partial updates work correctly
- [x] Test session persistence across page refreshes
- [x] Ensure all navigation links work properly
- [x] Validate protected routes redirect correctly

## Technical Notes
- Use jinja2-fragments for rendering partial templates with HTMX
- Store JWT tokens in secure httpOnly cookies
- Use HTMX hx-target and hx-swap for dynamic content updates
- Implement CSRF protection for forms
- Keep templates simple and semantic - Pico CSS will handle styling
- Use Pico's semantic HTML patterns (no custom classes needed)
- Leverage Pico's built-in responsive design and theme support
- Only add custom CSS for specific brand requirements

## Implementation Complete! ✅

All phases have been successfully implemented. The FastAPI application now has:

1. **Beautiful UI** - Clean, modern interface using Pico CSS
2. **Dynamic Interactions** - HTMX for seamless page updates without full reloads
3. **Secure Authentication** - JWT tokens stored in httpOnly cookies
4. **Complete User Flow**:
   - Landing page with feature highlights
   - Login/Signup page with form validation
   - Protected dashboard for authenticated users
   - Profile page showing user details
   - Logout functionality
5. **Enhanced UX**:
   - Loading states during form submissions
   - Light/dark theme toggle with persistence
   - Client and server-side form validation
   - Custom error pages (404, 500)
   - Responsive design for all screen sizes

### Key Files Created:
- `/app/templates/base.html` - Base template with navigation and theme toggle
- `/app/templates/index.html` - Landing page
- `/app/templates/auth.html` - Login/signup forms
- `/app/templates/dashboard.html` - User dashboard
- `/app/templates/profile.html` - User profile
- `/app/templates/404.html` - 404 error page
- `/app/templates/error.html` - Generic error page
- `/app/templates/fragments/` - HTMX fragments for dynamic updates
- `/app/routers/ui.py` - UI routes and authentication handling
- `/app/templates_config.py` - Jinja2 configuration

The application is now ready for use with a complete web interface!

## Post-Implementation Improvements

### CSS Optimization (Completed)
Based on Pico CSS documentation review, we've optimized our implementation:

1. **Reduced Custom CSS** from 35 lines to just 10 lines
   - Removed unnecessary navigation alignment CSS (Pico handles this automatically)
   - Removed custom HTMX loading indicators (use Pico's aria-busy)
   - Removed center-content helper class (use semantic HTML instead)
   - Removed inline margin styles on forms

2. **Better Semantic HTML**
   - Wrapped `<nav>` in `<header>` for proper document structure
   - Used buttons directly in navigation without form wrappers
   - Removed unnecessary style attributes
   - Leveraged Pico's automatic spacing and layout

3. **Improved Navigation**
   - Removed `class="container"` from nav (not needed)
   - Added `class="outline"` to signup link for consistency
   - Simplified logout buttons by removing form wrappers
   - Let Pico handle all link and button styling

The result is cleaner, more maintainable code that fully leverages Pico CSS's capabilities!
