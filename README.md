# MorphoContour

**Extract and analyze object boundaries with precision—tailored for droplets, bubbles, cells, and more.**

---

## Overview

**MorphoContour** is a Python library for extracting and analyzing boundary contours of objects in images. Originally designed for droplets and bubbles, its adaptable settings allow it to handle other use cases, such as biological cells or arbitrary objects. The library's current configuration is fine-tuned for droplet analysis but can be customized for different types of objects.

---

## Features

- **Robust Contour Extraction**: Extracts object boundaries with precision.
- **Versatile Applications**: Suitable for droplets, bubbles, biological cells, and more.
- **Customizable Settings**: Tune parameters to adapt the algorithm for various object types.
- **Lightweight and Easy to Use**: A single Python file with no complex dependencies.

---

## Installation

Clone the repository and import the library into your project:

```bash
# Clone the repository
git clone https://github.com/ARHashemi/MorphoContour.git

# Navigate to the repository directory
cd MorphoContour

# Install required packages
pip install -r requirements.txt
```

---

## Usage

Here’s an example of how to use **MorphoContour**:

```python
import morphocontour

# Load your image
image_path = "path/to/your/image.png"



# Initialize the contour extraction
detected_contours, contours_area, contour_centroids, hierarchy = morphocontour.contour_finder(image_path)

# Display or analyze the results
for contour in detected_contours:
    print("Contour points:", contour)
```

---

## Applications

- **Droplet and Bubble Analysis**: Analyze contours for size, shape, or dynamics.
- **Biological Imaging**: Extract cell boundaries for morphological studies.
- **General Object Detection**: Apply to any objects in grayscale or binary images.

---

## How to Cite

If you use **MorphoContour** in your research, please cite the following:

- Repository: [MorphoContour GitHub Repository](https://github.com/ARHashemi/MorphoContour)


---

## License

This project is licensed under the **European Union Public License (EUPL) v1.2 with additional terms**:

- The software may not be used for activities violating the United Nations Universal Declaration of Human Rights (UDHR).
- Any modifications must retain this license and explicitly indicate changes.

For more details, see the full license in the `LICENSE` file.


---

## Contact

For questions or inquiries, please open an issue on the GitHub repository.
Contributions are welcome! 
