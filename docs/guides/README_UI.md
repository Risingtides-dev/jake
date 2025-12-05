# UI Development Setup - Warner Tracker

## ✅ What's Been Set Up

### 1. Live Preview Server (`preview_server.py`)
- Local development server on port 8000
- Auto-reload functionality (checks for changes every 2 seconds)
- Automatically opens browser
- Serves files from `output/` directory

### 2. UI Development Tools (`ui_dev_tools.py`)
- List HTML files
- Open files in browser
- Create test HTML files
- Start preview server

### 3. Documentation
- `UI_OPTIMIZATION_GUIDE.md` - Comprehensive optimization guide
- `QUICK_START_UI.md` - Quick reference for UI development

## 🎯 How to Use

### Start Preview Server
```bash
python3 preview_server.py
```

### Generate and View Reports
```bash
# Generate a report
python3 generate_glass_html.py

# The preview server will automatically show it
# Or manually open:
python3 ui_dev_tools.py open output/sound_usage_complete_report.html
```

## 🌐 Browser MCP Integration

You have access to browser MCP tools through Cursor! These allow you to:

1. **Take Screenshots**: Capture design iterations
2. **Navigate Pages**: Open and interact with your HTML
3. **Inspect Elements**: Analyze CSS and layout
4. **Test Interactions**: Verify hover states, clicks, etc.
5. **Check Responsiveness**: Test different viewport sizes

### Using Browser MCP Tools

When you have the preview server running, you can ask Claude to:
- "Take a screenshot of the current design"
- "Navigate to http://localhost:8000 and show me the page"
- "Test the hover effects on the stat cards"
- "Check how it looks on mobile viewport"

## 🎨 Current UI Themes

### Glassmorphism Theme
- Modern, clean design
- Backdrop blur effects
- Purple/violet gradients
- Smooth animations

### Cyberpunk Theme
- Futuristic aesthetic
- Animated backgrounds
- Neon-style borders
- Bold typography

## 📊 Optimization Opportunities

See `UI_OPTIMIZATION_GUIDE.md` for detailed recommendations including:
- Performance improvements
- Accessibility enhancements
- Responsive design
- User experience features
- Visual design improvements

## 🚀 Quick Test

1. Create a test HTML file:
   ```bash
   python3 ui_dev_tools.py test
   ```

2. Start the preview server:
   ```bash
   python3 preview_server.py
   ```

3. The browser should open automatically showing your test page!

## 💡 Tips

- The preview server auto-reloads when files change
- Edit the Python generator scripts to change the HTML/CSS
- Use browser dev tools (F12) for quick CSS experiments
- Both themes can be customized in their respective Python files

