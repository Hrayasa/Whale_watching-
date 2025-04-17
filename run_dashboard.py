import sys
from pathlib import Path

# Add the src directory to Python path
src_path = str(Path(__file__).parent / 'src')
sys.path.append(src_path)

# Import and run the dashboard
from visualization.dashboard import app

if __name__ == '__main__':
    app.run(debug=True) 