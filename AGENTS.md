# AGENTS.md

## Build/Run Commands
- **Run app**: `python main.py`
- **Install dependencies**: `pip install -r requirements.txt`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local imports
- **Formatting**: 4-space indentation, snake_case for functions/variables, PascalCase for classes
- **Types**: Use type hints where possible, follow existing patterns in main.py
- **Naming**: Descriptive names in Russian/English, consistent with existing code
- **Error handling**: Use try/except blocks with specific exceptions, log errors to console
- **Documentation**: Docstrings for classes and methods, comments in Russian
- **UI conventions**: Follow tkinter/ttk patterns, use consistent color scheme (#1f573fff background)

## Project Structure
- Single main.py file with tkinter GUI application
- Images in `images/` directory
- SQL prompt builder with system/user/final prompt sections
- Uses ChromaDB for vector database functionality