import os
from PIL import Image

for root, dirs, files in os.walk('gender_dataset_face'):
    for file in files:
        if file.endswith(('.jpg', '.png', '.jpeg')):
            path = os.path.join(root, file)
            try:
                Image.open(path).verify()
            except Exception:
                print('Removing corrupt image:', path)
                os.remove(path)
