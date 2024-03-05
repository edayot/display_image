
from PIL import Image







def crop_null_rectangle(image):
    # Convert image to grayscale
    grayscale_image = image.convert('L')
    
    # Get image size
    width, height = grayscale_image.size
    
    # Find bounding box of non-null pixels
    left = width
    top = height
    right = 0
    bottom = 0
    
    for x in range(width):
        for y in range(height):
            pixel_value = grayscale_image.getpixel((x, y))
            if pixel_value != 0:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    
    # Crop the image based on bounding box
    if left < right and top < bottom:
        cropped_image = image.crop((left, top, right + 1, bottom + 1))
        return cropped_image
    else:
        return None  # No non-null pixels found


def add_transparency_border(image, border_size):
    # Calculate new dimensions
    width, height = image.size
    new_width = width + 2 * border_size
    new_height = height + 2 * border_size
    
    # Create a new image with larger dimensions and transparent background
    new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    
    # Paste the cropped image onto the new image with an offset to add the border
    offset = (border_size, border_size)
    new_image.paste(image, offset)
    
    # Draw a rectangle around the pasted image with a specified border color
    border_color = (0, 0, 0, 128)  # Example: RGBA color with 50% opacity (adjust as needed)
    border_rectangle = Image.new("RGBA", (new_width, new_height), border_color)
    border_rectangle.paste(new_image, (0, 0), mask=new_image)
    
    return border_rectangle

def add_empty_line(image):
    width, height = image.size
    
    # Check if height is not a multiple of 2
    if height % 2 != 0:
        # Create a new image with an extra line at the top
        new_height = height + 1
        new_image = Image.new("RGBA", (width, new_height), (0, 0, 0, 0))
        new_image.paste(image, (0, 1))  # Paste the original image with an offset to leave an empty line at the top
        return new_image
    else:
        return image