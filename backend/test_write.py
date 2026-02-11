import os

path = "alembic/versions/test.txt"
try:
    with open(path, "w") as f:
        f.write("test")
    print(f"Successfully wrote to {os.path.abspath(path)}")
    os.remove(path)
except Exception as e:
    print(f"Failed to write: {e}")
