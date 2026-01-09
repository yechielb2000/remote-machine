import os
import sys

# Ensure package root is on sys.path for tests in this environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
