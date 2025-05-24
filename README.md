# PixelAlchemy Studio ✨🎨

PixelAlchemy Studio is an interactive 2D drawing application built with Python and Pygame, supercharged with Generative AI capabilities from Google's Gemini and Veo APIs. Sketch your ideas, refine them with AI-powered image generation, and bring them to life with video animation!

## 🌟 Features

### Intuitive Drawing Tools:
- Pixel-perfect drawing
- Line drawing: DDA & Bresenham algorithms
- Circle drawing: Bresenham's algorithm
- Ellipse drawing: Midpoint algorithm
- Cubic Bézier curves
- Basic shapes: Triangles, Rectangles
- Multi-point Polygons

### AI-Powered Image Generation & Editing (Gemini):
- Provide a text prompt to generate an image or modify the existing canvas content
- Uses Google's `gemini-2.0-flash-exp` model (configurable)
- Intelligent prompt enhancement for style consistency ("Keep the same minimal line doodle style")

### AI-Powered Video Animation (Veo):
- Animate the current canvas image using a fixed prompt: "animate keep the style Keep the same minimal line doodle style."
- Uses Google's `veo-2.0-generate-001` model (configurable)
- Asynchronous operation handling with on-screen status updates and polling
- Generated videos are saved locally as MP4 files

### User-Friendly Interface:
- Clear canvas functionality
- Selectable drawing colors
- Dedicated control panel for tools and colors
- Status bar for AI operation feedback
- Keyboard shortcuts for quick tool access

## 🛠️ Tech Stack

- **Python 3.11+**
- **Pygame**: For graphics, UI, and event handling
- **Google Generative AI SDK** (google-genai): To interact with Gemini & Veo APIs
- **Pillow (PIL)**: For image manipulation and processing
- **UV**: For fast project and virtual environment management
- **python-dotenv**: For managing API keys via .env files

## 📂 Project Structure

The project is organized as follows:

```
pixel-alchemy-studio/
├── .env.example         # Example environment file
├── pyproject.toml       # Project metadata and dependencies for UV
├── README.md            # This file
├── run.py               # Script to easily run the application
├── src/
│   └── graficador/
│       ├── algorithms/  # Drawing algorithms (Bresenham, DDA, Bezier, etc.)
│       ├── geometry/    # Geometric primitives (e.g., Point)
│       ├── ui/          # UI components (Button, Canvas, Controls)
│       ├── app.py       # Main application class, event handling, AI integration
│       ├── config.py    # Configuration (screen size, colors, API models)
│       └── main.py      # Entry point of the application
├── assets/              # (Optional) For static assets like icons, fonts
├── docs/                # (Optional) For extended documentation, demo GIFs
├── tests/               # Test files
└── uv.lock              # UV lock file
```

## ⚙️ Setup and Installation

Follow these steps to get PixelAlchemy Studio up and running on your local machine.

### Prerequisites
- Python 3.11 or higher
- **UV**: Installed on your system. If you don't have it, follow the installation instructions at [UV's official website](https://docs.astral.sh/uv/)

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/pixel-alchemy-studio.git # Replace with your actual repo URL
   cd pixel-alchemy-studio
   ```

2. **Create and Activate Virtual Environment using UV:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   # .venv\Scripts\activate   # On Windows
   ```

3. **Install Dependencies using UV and pyproject.toml:**
   
   Ensure your `pyproject.toml` file has the necessary dependencies listed under `[project.dependencies]`.
   
   Example for `pyproject.toml` (ensure yours matches your project's needs):
   ```toml
   [project]
   name = "pixel_alchemy_studio" # Or "graficador_geometrico" if you prefer
   version = "0.1.0"
   description = "Interactive drawing with AI-powered image and video generation."
   requires-python = ">=3.11"
   dependencies = [
       "pygame>=2.5.0",
       "google-genai>=1.10.0", # Check for the latest Veo-compatible version
       "Pillow>=10.0.0",
       "python-dotenv>=1.0.0"
   ]

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```
   
   Then install dependencies using:
   ```bash
   uv pip sync
   ```

4. **Set Up Google API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/) to get your API key
   - Ensure that the Generative Language API (for Gemini) and the Vertex AI API (Veo model access is enabled for your project) are enabled in your Google Cloud Project
   - **Important for Veo**: Veo is a paid feature. Make sure billing is enabled on your Google Cloud Project associated with the API key
   - Create a file named `.env` in the root directory of the project (`pixel-alchemy-studio/.env`)
   - Add your API key to the `.env` file like this:
     ```
     GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY_HERE"
     ```
   - (A `.env.example` file should be provided in your repository as a template)

## 🚀 How to Run

Once the setup is complete, run the application from the root directory of the project:

```bash
uv run python -m src.graficador.main
```

## 🎮 How to Use

- **Main Interface**: The application window is divided into a drawing canvas on the left and a control panel on the right.

- **Selecting Tools**: Click on buttons in the control panel to select drawing tools or AI functions. Keyboard shortcuts are also available (indicated on buttons).

- **Drawing**:
  - **Pixel (P)**: Click and drag to draw freehand
  - **Lines (L, B), Circle (O), Ellipse (E)**: Click for the first point (e.g., start of line, center of circle/ellipse), then click for the second point (e.g., end of line, point on radius/edge)
  - **Bézier Curve (Z)**: Click four times to define the two endpoints and two control points
  - **Triangle (T)**: Click three times for the vertices
  - **Rectangle (R)**: Click twice for two opposite corners
  - **Polygon (Y)**: Click for each vertex. Click near the first vertex (within threshold) to close the polygon

- **Choosing Colors**: Click on color swatches in the control panel.

- **Clearing Canvas (C)**: Click the "Clear" button or press 'C'. This also resets AI states.

- **Gemini - Image Generation/Editing (G)**:
  - Press 'G' or click the "Generate with AI" button. The status bar will prompt you to type
  - Type your desired modification or generation prompt (e.g., "a cat wearing a hat", "make this blue")
  - Press Enter. Gemini will process the current canvas image with your prompt
  - The canvas will update with the AI-generated image

- **Veo - Video Animation (V)**:
  - Ensure there's a drawing on the canvas
  - Press 'V' or click the "Video with Veo" button
  - The application will use the current canvas image and a fixed internal prompt ("animate keep the style Keep the same minimal line doodle style.") to generate a video
  - Monitor the status bar for progress (Initializing → Generating → Polling → Done/Error)
  - Generated videos (MP4) are saved in the project's root directory (e.g., `veo_video_12345_0.mp4`)
  - **Note**: Video generation can take several minutes. The UI will remain responsive during polling

- **Exiting**: Close the Pygame window or press Ctrl+C in the terminal where it's running.

## ⚙️ Configuration

Advanced parameters like FPS, default colors, API model names, and Veo generation settings (default aspect ratio, duration) can be tweaked in:
`src/graficador/config.py`

## 🔮 Potential Future Enhancements

- Advanced color picker and custom palettes
- Image import/export options
- Layer management system
- Undo/Redo functionality
- More sophisticated brush/drawing tools
- UI controls for Veo parameters (prompt, duration, aspect ratio)
- In-app video playback
- Inpainting/Outpainting with Gemini using drawn masks

## 🙏 Acknowledgements & Inspiration

This project was inspired by the creative possibilities demonstrated in other AI-powered drawing applications. Special thanks and acknowledgement to:

**Trudy's "Gemini Co-Drawing"** on Hugging Face Spaces: This project served as an initial inspiration for exploring collaborative and AI-enhanced drawing. You can find it here: [Trudy/gemini-codrawing](https://huggingface.co/spaces/Trudy/gemini-codrawing).

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.

**Happy sketching and alchemizing with PixelAlchemy Studio!**
