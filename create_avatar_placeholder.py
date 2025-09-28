#!/usr/bin/env python3
"""
Create a simple avatar placeholder image
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_avatar_placeholder():
    """Create a simple avatar placeholder image"""
    # Create a 512x512 image
    size = (512, 512)
    image = Image.new('RGB', size, color=(79, 70, 229))  # Indigo background
    
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    
    # Draw a circle for the face
    face_color = (255, 255, 255)  # White
    face_bbox = (100, 100, 412, 412)  # (left, top, right, bottom)
    draw.ellipse(face_bbox, fill=face_color)
    
    # Draw eyes
    eye_color = (79, 70, 229)  # Indigo
    left_eye_bbox = (170, 200, 210, 240)
    right_eye_bbox = (302, 200, 342, 240)
    draw.ellipse(left_eye_bbox, fill=eye_color)
    draw.ellipse(right_eye_bbox, fill=eye_color)
    
    # Draw a smile
    smile_bbox = (170, 250, 342, 350)
    draw.arc(smile_bbox, start=0, end=180, fill=eye_color, width=10)
    
    # Save the image
    avatar_dir = "agent-starter-react/public/avatars"
    if not os.path.exists(avatar_dir):
        os.makedirs(avatar_dir)
    
    avatar_path = os.path.join(avatar_dir, "placeholder_avatar.png")
    image.save(avatar_path)
    print(f"Avatar placeholder created at: {avatar_path}")
    
    # Also create a simple text file with instructions
    instructions_path = os.path.join(avatar_dir, "README.md")
    with open(instructions_path, "w") as f:
        f.write("""# Avatar Images

Place your avatar images in this directory.

## Supported Formats
- PNG
- JPEG
- GIF

## Recommended Size
- 512x512 pixels minimum
- Square aspect ratio

## Usage
Set the AVATAR_IMAGE_PATH environment variable to the path of your avatar image:

```
AVATAR_IMAGE_PATH=agent-starter-react/public/avatars/placeholder_avatar.png
```

## Customization
Replace placeholder_avatar.png with your own avatar image.
""")
    
    print(f"Instructions created at: {instructions_path}")

if __name__ == "__main__":
    create_avatar_placeholder()