# 📝 UNotes — Minimalist Note-Taking Web App

## ✨ About

**UNotes** is a lightweight, distraction-free note-taking web application built with **FastAPI** and **HTMX**.
It provides a fluid, JavaScript-light experience while offering optional **GitHub sync**, letting you securely store your notes in a private repository.

Perfect for students, developers, and minimalists who want fast, synced, and clean note-taking on any device.

---

## 🚀 Features

* 🎨 **Clean & responsive UI** — adapted from a beautiful HTML/JS/CSS design
* ⚡ **FastAPI backend** — lightweight and performant
* 🔄 **HTMX-powered interactivity** — minimal JavaScript needed
* ☁️ **GitHub Sync** — automatically sync notes to a private repo
* 🔐 **GitHub OAuth login** — auto-creates a notes repository securely
* 📦 **Store notes as individual JSON files** in `/notes/` directory
* 💨 **Fast, small, and perfect for everyday use**

---

## 🌐 Live Demo

Try it here:
👉 [https://unotes.leapcell.app/](https://unotes.leapcell.app/)

---

## 🛠️ Technologies Used

* 🐍 Python
* ⚡ FastAPI
* 🔗 HTMX
* 🗂️ GitHub API
* 🎨 HTML / CSS

---

## 🔧 How It Works (Detailed Workflow)

### **1️⃣ Login with GitHub**

* User clicks **Login with GitHub**
* Redirects to GitHub OAuth
* Requests minimal scope: `repo`
* UNotes receives an access token

### **2️⃣ Auto Repository Management**

Using the token:

* Checks if a private repo (default: **UNotes-Data**) exists
* If missing → **automatically creates it**
* Stores repo metadata (name, URL, privacy)

### **3️⃣ Using Notes Locally (Session Storage)**

Notes are stored in the user session:

* Each note = `{ id, head, info, date, color }`
* Created, updated, and deleted in memory instantly

### **4️⃣ Syncing Notes to GitHub**

Every create/update/delete triggers:

* Encode note JSON → Base64
* Upload to GitHub via `/contents/` API
* Each note is saved as:

  ```
  notes/<uuid>.json
  ```

### **5️⃣ Loading Notes from GitHub**

When user loads notes:

* Fetches all `.json` files from `notes/` folder
* Parses them and populates the UI seamlessly

Full workflow ensures:

* ✔️ Always backed-up
* ✔️ Accessible across devices
* ✔️ Notes remain private
* ✔️ Simple, reliable syncing

---

## 📦 Installation

```bash
git clone https://github.com/Tanmandal/UNotes
cd UNotes
pip install -r requirements.txt
```

### Environment variables you need to set:

```
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
CALLBACK_URL=your_callback_url
REPO_NAME=naame_of_your_storage_repo
```

---

## ▶️ Running the App

```bash
uvicorn main:app --reload
```

Visit:
👉 [http://localhost:8000/](http://localhost:8000/)

---

## 🙏 Special Thanks

Inspired by the original design by:
🔗 [https://github.com/sinster23/Notesapp](https://github.com/sinster23/Notesapp)

UNotes ports the UI to FastAPI/HTMX and adds full GitHub sync + backend logic.

---

## 📄 License

Licensed under the **MIT License**.
🔗 [https://github.com/Tanmandal/UNotes/blob/main/LICENSE](https://github.com/Tanmandal/UNotes/blob/main/LICENSE)
