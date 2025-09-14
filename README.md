# AIDE - Android App Development on Android Phone 📱

AIDE lets you **create and build Android apps directly on your Android phone**, without Android Studio or a computer.  
It includes **Python-based tools** and utilities to generate projects, manage imports, and simplify the development process.

---

## ✨ Features
- 📦 **Project Generator**
  - Generate a new Android project by simply providing:
    - **Package Name**
    - **App Name**
  - Automatically generates the required file structure.
  - Supports creating **Jetpack Compose apps**.

- 🛠 **Auto Import Manager** (`checkimport.py`)
  - Analyzes your Kotlin files and automatically adds required imports.  
  - Saves time by fixing missing imports for **Jetpack Compose**.

- 🌐 **Web-based Control Panel** (`aide.py`)
  - A Flask-based web interface to:
    - Create new projects  
    - Run an app  
    - Delete existing projects  

---

## 📂 Project Structure




---

## ⚙️ Requirements

To use AIDE on your Android phone, you need:

- 📱 **Android Phone**
- 📦 **Termux App** → [Download from F-Droid](  https://f-droid.org/packages/com.termux)
- 🐍 **Python 3** (via Termux)
- 🛠 **Essential build tools**

---

## 🛠 Installation (Termux Setup)

Run the following commands inside **Termux**:

```bash
# Update and upgrade Termux
pkg update && pkg upgrade -y

# Install required packages
pkg install python git clang openjdk-17 -y

# (Optional) Install curl, wget, unzip, nano/vim
pkg install curl wget unzip vim -y

# Clone this repository
git clone https://github.com/<your-username>/AIDE.git
cd AIDE

# Install Python dependencies (Flask, etc.)
pip install -r requirements.txt

# Run the Flask web app
python aide.py
```

---

## 🚧 Work in Progress / Coming Soon
We are actively improving **AIDE**.  
Upcoming updates may include:
- step by step tutorials and examples

Stay tuned for updates!
