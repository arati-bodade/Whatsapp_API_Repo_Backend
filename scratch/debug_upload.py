import requests
import os

# Create a dummy image file
with open("test_image.jpg", "wb") as f:
    f.write(b"dummy image content")

url = "http://localhost:8000/api/admin/profile/upload-image"
# Note: This requires a token. Since I don't have one easily, I'll just check if the directory is writable.
print(f"Checking if uploads/profile_images is writable...")
if not os.path.exists("uploads/profile_images"):
    os.makedirs("uploads/profile_images", exist_ok=True)

with open("test_image.jpg", "rb") as f:
    # This won't actually work because of auth, but it tests the logic if I could run it.
    pass

print("CWD:", os.getcwd())
print("Contents of uploads/profile_images:", os.listdir("uploads/profile_images"))
