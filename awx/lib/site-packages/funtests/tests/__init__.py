import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))
print(sys.path[0])
sys.path.insert(0, os.getcwd())
print(sys.path[0])
