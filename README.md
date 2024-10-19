# Framestop

## Description
Framestop is a Flatpak application designed to extract high-quality freeze frames from videos. Using advanced image analysis, the app identifies and selects the most representative and visually distinct frames from the video.

## How It Works
1. User loads the video and selects a frame on the timeline.
2. Five neighboring frames from the current frame are selected for analysis (this number can be changed in configs).
3. The software calculates perceptual color differences between neighboring pixels using the CIELAB color space.
4. The frame with the most perceptual pixel transitions (more details) is selected for the screenshot.

### CIELAB Color Space and Delta E

Framestop uses the CIELAB color space for its analysis due to its perceptual uniformity. Here's why it's important:

- CIELAB (also known as CIE L*a*b*) is designed to approximate human vision. It's particularly good at measuring small color differences the way the human eye perceives them.
- In CIELAB, 'L*' represents lightness, 'a*' represents the green–red component, and 'b*' represents the blue–yellow component.
- It is better for perceived detail then RGB color because the human eye don't perceive red, green and blue color with the same sensitivity.

Delta E (ΔE) is a metric used to measure the difference between two colors in the CIELAB color space:

![Delta E formula](https://wikimedia.org/api/rest_v1/media/math/render/svg/d30890885ec8cfc97e205208245f64d92c6688f0)

- It quantifies the amount of visual difference between two colors as perceived by the human eye.

- Frames with higher total Delta E values across all pixel comparisons are considered to have more visual information and are thus more likely to be selected as freeze frames.


## Installation
To install Framestop, make sure you have Flatpak installed on your system. Then, run the following command:
```
flatpak install [Flatpak package URL]
```
Replace `[Flatpak package URL]` with the actual URL of the app's Flatpak package. #TODO

## Usage
After installation, you can run the app using:
```
flatpak run io.github.Abstract-AA.Framestop
```

## Contributing
Contributions are welcome! Feel free for submitting pull requests. Some improvement ideas:
- Better zoom controls and viewport zoom auto adjust
- Icons on buttons

## License
This project is licensed under the MIT License - see the [License.txt](License.txt) file for details.
