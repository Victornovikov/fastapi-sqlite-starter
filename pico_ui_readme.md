# Pico CSS v2 - Complete LLM Development Guide

## Overview
Pico CSS is a minimal CSS framework for semantic HTML. It styles HTML elements without requiring classes, making it ideal for rapid prototyping and clean, maintainable code.

## Installation

### CDN (Recommended for Web Apps)
```html
<!-- Standard version -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">

<!-- Classless version (no .container needed) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css">

<!-- Conditional version (styles only apply inside .pico) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.conditional.min.css">
```

### NPM/Yarn
```bash
npm install @picocss/pico
# or
yarn add @picocss/pico
```

### Import in CSS/SCSS
```css
@import "@picocss/pico";
```

## Base HTML Template
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="light dark">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <title>App Title</title>
  </head>
  <body>
    <main class="container">
      <!-- Content here -->
    </main>
  </body>
</html>
```

## Layout System

### Container
```html
<!-- Standard container with responsive padding -->
<main class="container">
  <h1>Page Title</h1>
</main>

<!-- Fluid container (full width) -->
<div class="container-fluid">
  <!-- Full width content -->
</div>
```

### Grid System
```html
<!-- Auto-responsive grid -->
<div class="grid">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>

<!-- Explicit columns (collapses on mobile) -->
<div class="grid">
  <div style="grid-column: span 2">Wide column</div>
  <div>Normal column</div>
</div>
```

### Sections & Semantic Structure
```html
<body>
  <header class="container">
    <nav>
      <ul>
        <li><strong>Brand</strong></li>
      </ul>
      <ul>
        <li><a href="#">Home</a></li>
        <li><a href="#">About</a></li>
      </ul>
    </nav>
  </header>

  <main class="container">
    <section>
      <h1>Main Content</h1>
    </section>
  </main>

  <footer class="container">
    <p>© 2024 Company</p>
  </footer>
</body>
```

## Typography

### Headings
```html
<h1>Heading 1</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>
<h4>Heading 4</h4>
<h5>Heading 5</h5>
<h6>Heading 6</h6>

<!-- With secondary text -->
<h1>Main Title <small>Subtitle</small></h1>
```

### Text Elements
```html
<p>Regular paragraph text.</p>
<p><strong>Bold text</strong> and <em>italic text</em></p>
<p><mark>Highlighted text</mark></p>
<p><del>Deleted text</del> and <ins>inserted text</ins></p>
<p><code>inline code</code></p>
<blockquote>
  "This is a blockquote"
  <footer><cite>— Author Name</cite></footer>
</blockquote>
```

### Code Blocks
```html
<pre><code>// Code block with syntax
function hello() {
  return "World";
}</code></pre>
```

### Links
```html
<a href="#">Regular link</a>
<a href="#" class="secondary">Secondary link</a>
<a href="#" class="contrast">High contrast link</a>
<a href="#" role="button">Link as button</a>
```

## Forms

### Basic Form Structure
```html
<form>
  <fieldset>
    <legend>Form Section</legend>

    <!-- Text input -->
    <label>
      Email
      <input type="email" name="email" placeholder="user@example.com" required>
      <small>We'll never share your email</small>
    </label>

    <!-- Password -->
    <label>
      Password
      <input type="password" name="password" required>
    </label>

    <!-- Textarea -->
    <label>
      Message
      <textarea name="message" rows="4"></textarea>
    </label>

    <!-- Select -->
    <label>
      Country
      <select name="country" required>
        <option value="" selected>Select a country</option>
        <option value="us">United States</option>
        <option value="uk">United Kingdom</option>
      </select>
    </label>

    <!-- Checkbox -->
    <label>
      <input type="checkbox" name="terms" required>
      I agree to the terms
    </label>

    <!-- Radio buttons -->
    <fieldset>
      <legend>Choose one:</legend>
      <label>
        <input type="radio" name="choice" value="1" checked>
        Option 1
      </label>
      <label>
        <input type="radio" name="choice" value="2">
        Option 2
      </label>
    </fieldset>

    <!-- Submit button -->
    <button type="submit">Submit</button>
  </fieldset>
</form>
```

### Form States
```html
<!-- Disabled input -->
<input type="text" disabled>

<!-- Invalid input -->
<input type="email" aria-invalid="true">
<small>Please provide a valid email</small>

<!-- Valid input -->
<input type="email" aria-invalid="false">

<!-- Loading/busy -->
<button aria-busy="true">Processing...</button>
```

### Input Groups (New in v2)
```html
<!-- Horizontal group of inputs -->
<fieldset role="group">
  <input type="text" placeholder="First name">
  <input type="text" placeholder="Last name">
  <button>Submit</button>
</fieldset>

<!-- Search with button -->
<fieldset role="group">
  <input type="search" placeholder="Search...">
  <button>Go</button>
</fieldset>
```

## Buttons

### Button Types
```html
<!-- Standard buttons -->
<button>Primary Button</button>
<button class="secondary">Secondary Button</button>
<button class="contrast">Contrast Button</button>
<button class="outline">Outline Button</button>

<!-- Button states -->
<button disabled>Disabled</button>
<button aria-busy="true">Loading...</button>

<!-- Button as link -->
<a href="#" role="button">Link Button</a>

<!-- Button group -->
<div role="group">
  <button>Left</button>
  <button>Middle</button>
  <button>Right</button>
</div>
```

### Button Sizes
```html
<!-- Full width button -->
<button style="width: 100%">Full Width</button>

<!-- Inline buttons -->
<button style="width: auto">Auto Width</button>
```

## Navigation

### Basic Navigation
```html
<nav>
  <ul>
    <li><strong>Brand</strong></li>
  </ul>
  <ul>
    <li><a href="#">Home</a></li>
    <li><a href="#">Features</a></li>
    <li><a href="#" class="secondary">Pricing</a></li>
    <li><a href="#" role="button">Sign up</a></li>
  </ul>
</nav>
```

### Breadcrumb
```html
<nav aria-label="breadcrumb">
  <ul>
    <li><a href="#">Home</a></li>
    <li><a href="#">Category</a></li>
    <li>Current Page</li>
  </ul>
</nav>
```

### Tabs (using radio buttons)
```html
<div role="tablist">
  <input type="radio" id="tab1" name="tabs" checked>
  <label for="tab1">Tab 1</label>

  <input type="radio" id="tab2" name="tabs">
  <label for="tab2">Tab 2</label>

  <input type="radio" id="tab3" name="tabs">
  <label for="tab3">Tab 3</label>
</div>
```

## Cards

### Basic Card
```html
<article>
  <header>
    <h3>Card Title</h3>
  </header>
  <p>Card content goes here.</p>
  <footer>
    <button>Action</button>
  </footer>
</article>
```

### Card Variations
```html
<!-- Card with image -->
<article>
  <img src="image.jpg" alt="Description">
  <h3>Title</h3>
  <p>Content</p>
</article>

<!-- Horizontal card -->
<article class="grid">
  <div>
    <img src="image.jpg" alt="Description">
  </div>
  <div>
    <h3>Title</h3>
    <p>Content</p>
  </div>
</article>
```

## Modal/Dialog

### Basic Modal
```html
<!-- Trigger -->
<button onclick="document.getElementById('modal').showModal()">
  Open Modal
</button>

<!-- Modal -->
<dialog id="modal">
  <article>
    <header>
      <button aria-label="Close" rel="prev" onclick="this.closest('dialog').close()"></button>
      <h3>Modal Title</h3>
    </header>
    <p>Modal content</p>
    <footer>
      <button class="secondary" onclick="this.closest('dialog').close()">
        Cancel
      </button>
      <button>Confirm</button>
    </footer>
  </article>
</dialog>
```

## Accordion

### Basic Accordion
```html
<details>
  <summary>Accordion Title</summary>
  <p>Accordion content that appears when expanded.</p>
</details>

<!-- Open by default -->
<details open>
  <summary>Open Section</summary>
  <p>This section is open by default.</p>
</details>

<!-- Nested accordions -->
<details>
  <summary>Parent Section</summary>
  <details>
    <summary>Child Section</summary>
    <p>Nested content</p>
  </details>
</details>
```

## Tables

### Basic Table
```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Email</th>
      <th>Role</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>John Doe</td>
      <td>john@example.com</td>
      <td>Admin</td>
    </tr>
    <tr>
      <td>Jane Smith</td>
      <td>jane@example.com</td>
      <td>User</td>
    </tr>
  </tbody>
</table>
```

### Responsive Table
```html
<figure>
  <table>
    <thead>
      <tr>
        <th scope="col">Header 1</th>
        <th scope="col">Header 2</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th scope="row">Row Header</th>
        <td>Data</td>
      </tr>
    </tbody>
  </table>
  <figcaption>Table caption</figcaption>
</figure>
```

## Progress Indicators

### Progress Bar
```html
<!-- Determinate progress -->
<progress value="75" max="100">75%</progress>

<!-- Indeterminate progress (loading) -->
<progress></progress>

<!-- With label -->
<label>
  Upload progress: 75%
  <progress value="75" max="100"></progress>
</label>
```

### Loading States
```html
<!-- Loading button -->
<button aria-busy="true">Loading...</button>

<!-- Loading section -->
<article aria-busy="true">
  Loading content...
</article>

<!-- Custom spinner -->
<div aria-busy="true"></div>
```

## Tooltips

### Basic Tooltip
```html
<!-- Using data-tooltip attribute -->
<button data-tooltip="This is a tooltip">Hover me</button>

<!-- Tooltip positions -->
<button data-tooltip="Top tooltip" data-placement="top">Top</button>
<button data-tooltip="Bottom tooltip" data-placement="bottom">Bottom</button>
<button data-tooltip="Left tooltip" data-placement="left">Left</button>
<button data-tooltip="Right tooltip" data-placement="right">Right</button>
```

## Dropdown

### Basic Dropdown
```html
<details class="dropdown">
  <summary>Dropdown</summary>
  <ul>
    <li><a href="#">Option 1</a></li>
    <li><a href="#">Option 2</a></li>
    <li><a href="#">Option 3</a></li>
  </ul>
</details>

<!-- Dropdown with button -->
<details class="dropdown">
  <summary role="button">Options</summary>
  <ul>
    <li><a href="#">Edit</a></li>
    <li><a href="#">Delete</a></li>
  </ul>
</details>
```

## Utilities

### Helper Classes
```html
<!-- Text alignment -->
<p class="text-center">Centered text</p>
<p class="text-right">Right aligned</p>
<p class="text-left">Left aligned</p>

<!-- Margins and padding -->
<div class="margin">Default margin</div>
<div class="padding">Default padding</div>

<!-- Visibility -->
<div class="hidden">Hidden element</div>
<div class="visible">Visible element</div>

<!-- Colors -->
<p class="primary">Primary color text</p>
<p class="secondary">Secondary color text</p>
<p class="success">Success color text</p>
<p class="danger">Danger color text</p>
<p class="warning">Warning color text</p>
<p class="info">Info color text</p>
<p class="light">Light color text</p>
<p class="dark">Dark color text</p>
```

### Responsive Utilities
```html
<!-- Hide on mobile -->
<div class="hide-mobile">Hidden on mobile</div>

<!-- Hide on tablet -->
<div class="hide-tablet">Hidden on tablet</div>

<!-- Hide on desktop -->
<div class="hide-desktop">Hidden on desktop</div>

<!-- Show only on mobile -->
<div class="show-mobile">Visible only on mobile</div>
```

## Color Schemes

### Dark/Light Mode
```html
<!-- Auto color scheme (follows system) -->
<meta name="color-scheme" content="light dark">

<!-- Force light mode -->
<html data-theme="light">

<!-- Force dark mode -->
<html data-theme="dark">

<!-- Toggle button example -->
<button onclick="toggleTheme()">Toggle Theme</button>

<script>
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', newTheme);
}
</script>
```

### Custom Color Themes
```html
<!-- Using precompiled themes from CDN -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.amber.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.blue.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.cyan.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.fuchsia.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.green.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.grey.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.indigo.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.jade.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.lime.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.orange.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.pink.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.purple.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.red.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.sand.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.slate.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.violet.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.yellow.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.zinc.min.css">
```

## CSS Variables (Customization)

### Key CSS Variables
```css
:root {
  /* Colors */
  --pico-color: #1095c1;
  --pico-background-color: #fff;
  --pico-text-color: #415462;

  /* Typography */
  --pico-font-family: system-ui, sans-serif;
  --pico-font-size: 1rem;
  --pico-line-height: 1.5;

  /* Spacing */
  --pico-spacing: 1rem;
  --pico-block-spacing-vertical: 1rem;
  --pico-block-spacing-horizontal: 1rem;

  /* Border radius */
  --pico-border-radius: 0.25rem;

  /* Container width */
  --pico-container-max-width: 1140px;

  /* Form elements */
  --pico-form-element-spacing-vertical: 0.75rem;
  --pico-form-element-spacing-horizontal: 1rem;
}
```

### Custom Theme Example
```html
<style>
  :root {
    --pico-color: #00897b;
    --pico-background-color: #f5f5f5;
    --pico-font-family: 'Roboto', sans-serif;
    --pico-border-radius: 0.5rem;
  }

  [data-theme="dark"] {
    --pico-color: #4db6ac;
    --pico-background-color: #121212;
  }
</style>
```

## Conditional Styling

### Using Conditional Version
```html
<!-- Only elements inside .pico will be styled -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.conditional.min.css">

<body>
  <!-- Unstyled content -->
  <div>
    <h1>This won't be styled by Pico</h1>
  </div>

  <!-- Styled content -->
  <div class="pico">
    <h1>This will be styled by Pico</h1>
    <button>Styled button</button>
  </div>
</body>
```

## HTMX Integration Examples

### Form with HTMX
```html
<form hx-post="/submit" hx-target="#result">
  <input type="text" name="username" required>
  <button type="submit">Submit</button>
</form>
<div id="result"></div>
```

### Dynamic Loading
```html
<article>
  <div hx-get="/content"
       hx-trigger="revealed"
       hx-indicator="#loading">
    <progress id="loading" class="htmx-indicator"></progress>
  </div>
</article>
```

### Modal with HTMX
```html
<button hx-get="/modal-content"
        hx-target="#modal-body"
        onclick="document.getElementById('modal').showModal()">
  Load Modal
</button>

<dialog id="modal">
  <article>
    <div id="modal-body">
      <!-- Content loaded here -->
    </div>
  </article>
</dialog>
```

## Best Practices for LLM Development

### 1. Start with Semantic HTML
- Use proper HTML5 semantic elements (`<header>`, `<main>`, `<footer>`, `<nav>`, `<section>`, `<article>`)
- Pico will automatically style them appropriately

### 2. Minimal Classes
- Most styling works without classes
- Use classes only for layout (`container`, `grid`) and variants (`secondary`, `outline`)

### 3. Form Structure
```html
<!-- Always wrap forms properly -->
<form>
  <fieldset>
    <legend>Form Title</legend>
    <!-- Form fields here -->
  </fieldset>
</form>
```

### 4. Accessibility
- Always include `aria-label` for icon-only buttons
- Use `aria-invalid` for form validation
- Include `aria-busy` for loading states
- Add `role` attributes where appropriate

### 5. Responsive Design
- Use `.container` for automatic responsive padding
- Grid automatically responds to screen size
- Test with different viewport sizes

### 6. Dark Mode Support
```html
<!-- Always include in <head> -->
<meta name="color-scheme" content="light dark">
```

### 7. Loading States
```html
<!-- Consistent loading pattern -->
<button aria-busy="true" disabled>Processing...</button>
```

### 8. Error Handling
```html
<!-- Form field with error -->
<label>
  Email
  <input type="email" aria-invalid="true" aria-describedby="email-error">
  <small id="email-error">Please enter a valid email</small>
</label>
```

### 9. Navigation Structure
```html
<!-- Standard nav pattern -->
<nav>
  <ul>
    <li><strong>Brand</strong></li>
  </ul>
  <ul>
    <li><a href="#">Link 1</a></li>
    <li><a href="#">Link 2</a></li>
  </ul>
</nav>
```

### 10. Button Groups
```html
<!-- Use role="group" for related buttons -->
<div role="group">
  <button>Save</button>
  <button class="secondary">Cancel</button>
</div>
```

## Common Patterns

### Login Form
```html
<main class="container">
  <article class="grid">
    <div>
      <hgroup>
        <h1>Sign in</h1>
        <p>Welcome back!</p>
      </hgroup>
      <form>
        <label>
          Email
          <input type="email" name="email" required>
        </label>
        <label>
          Password
          <input type="password" name="password" required>
        </label>
        <label>
          <input type="checkbox" name="remember">
          Remember me
        </label>
        <button type="submit">Sign in</button>
      </form>
    </div>
  </article>
</main>
```

### Dashboard Layout
```html
<body>
  <nav class="container-fluid">
    <ul>
      <li><strong>Dashboard</strong></li>
    </ul>
    <ul>
      <li><a href="#">Profile</a></li>
      <li><a href="#">Settings</a></li>
      <li><a href="#">Logout</a></li>
    </ul>
  </nav>

  <main class="container">
    <div class="grid">
      <article>
        <h3>Statistics</h3>
        <p>Content here</p>
      </article>
      <article>
        <h3>Activity</h3>
        <p>Content here</p>
      </article>
    </div>
  </main>
</body>
```

### Settings Page
```html
<main class="container">
  <h1>Settings</h1>

  <section>
    <h2>Profile</h2>
    <form>
      <div class="grid">
        <label>
          First Name
          <input type="text" name="first_name">
        </label>
        <label>
          Last Name
          <input type="text" name="last_name">
        </label>
      </div>
      <button>Save Changes</button>
    </form>
  </section>

  <section>
    <h2>Preferences</h2>
    <label>
      <input type="checkbox" name="notifications">
      Enable notifications
    </label>
    <label>
      Theme
      <select name="theme">
        <option>Auto</option>
        <option>Light</option>
        <option>Dark</option>
      </select>
    </label>
  </section>
</main>
```

## Notes for FastAPI/HTMX Integration

When using Pico CSS with FastAPI and HTMX:

1. **Return HTML fragments** for HTMX requests, not full pages
2. **Use Pico's semantic styling** - no need for custom CSS in most cases
3. **Include CSRF tokens** in forms as hidden inputs
4. **Use aria-busy** for loading states during HTMX requests
5. **Leverage dialogs** for modals instead of custom implementations
6. **Use progress elements** for loading indicators
7. **Remember form validation** states with aria-invalid

## Version Notes

- This guide covers **Pico CSS v2.0+**
- All CSS variables use the `pico-` prefix
- Breaking changes from v1: buttons no longer 100% width by default, grid columns collapse on mobile
- 20 precompiled color themes available via CDN
- Enhanced accessibility following WCAG 2.1 AAA standards

## Resources

- Official Website: https://picocss.com
- Documentation: https://picocss.com/docs
- GitHub: https://github.com/picocss/pico
- Examples: https://picocss.com/examples
- CDN: https://cdn.jsdelivr.net/npm/@picocss/pico@2/

---

*This guide is designed for LLMs to quickly understand and implement Pico CSS features in web development projects.*