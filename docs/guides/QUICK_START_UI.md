# Quick Start: UI Development & Preview

## 🚀 Quick Start

### 1. Start Live Preview Server
```bash
python3 preview_server.py
```

This will:
- Start a local server on `http://localhost:8000`
- Automatically open your browser
- Auto-reload when HTML files change

### 2. Generate a Report
```bash
# Generate glassmorphism theme
python3 generate_glass_html.py

# Or generate cyberpunk theme
python3 generate_complete_html.py
```

### 3. View in Browser
The preview server will automatically show your generated HTML files. If you need to manually open:

```bash
python3 ui_dev_tools.py list    # See available files
python3 ui_dev_tools.py open output/report.html
```

## 🎨 UI Development Workflow

1. **Generate HTML**: Run one of the generator scripts
2. **Start Server**: Run `preview_server.py` in a separate terminal
3. **Edit Code**: Modify the Python scripts (HTML generation code)
4. **Regenerate**: Run the generator script again
5. **Auto-Reload**: Browser automatically refreshes (checks every 2 seconds)

## 🔧 Using Browser MCP Tools

If you have browser MCP tools configured, you can:

```python
# In Cursor/Claude, you can use browser tools to:
# - Take screenshots of your designs
# - Inspect elements
# - Test interactions
# - Check responsive layouts
```

## 📝 Tips

- **Edit Python Scripts**: The HTML is generated in Python, so edit the generator scripts
- **Test HTML Directly**: You can also edit generated HTML files for quick tests
- **Multiple Themes**: Try both `generate_glass_html.py` and `generate_complete_html.py`
- **Browser Dev Tools**: Use F12 to inspect and experiment with CSS

## 🎯 Next Steps

See `UI_OPTIMIZATION_GUIDE.md` for detailed optimization recommendations.

