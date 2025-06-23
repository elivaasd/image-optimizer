# 🖼️ Image Optimization Service

A lightweight, fast, and production-ready **on-the-fly image optimization backend** using **FastAPI**.  
It resizes and converts images to modern formats (like WebP), ideal for integration with CDNs like **CloudFront**.

---

## 🚀 Features

- 🔧 Resize images dynamically via query params
- 🌐 Convert to `webp`, `jpeg`, or `png`
- 📦 Built with FastAPI and Pillow
- 🔐 CORS enabled for browser and CDN use
- ⚡ Ready to be deployed behind CloudFront

---

## 📁 Project Structure

```
image-optimizer/
├── backend/
│ ├── main.py # FastAPI app
│ ├── image_utils.py # Image processing logic
│ ├── requirements.txt
│ └── Dockerfile (optional)
```
