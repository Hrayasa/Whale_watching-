import unittest
import sys
from pathlib import Path

def run_tests():
    # Add the src directory to the Python path
    src_path = str(Path(__file__).parent / 'src')
    if src_path not in sys.path:
        sys.path.append(src_path)
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 