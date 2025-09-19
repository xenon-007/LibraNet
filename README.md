# 📚 LibraNet – Smart Library Management System

LibraNet is a **Streamlit-based library management system** that supports **books, audiobooks, magazines, and newspapers**, with features like user registration, borrowing/returning, fine calculation, subscription management, and audiobook previews.

The system is designed to provide a **modern digital library experience** with payment tracking, automatic fine calculation, and audiobook expiry handling.



## ✨ Features

* 👤 **User Management**

  * Register/login users with unique IDs.
  * Track borrowing history and outstanding fines.

* 📕 **Library Catalog**

  * Preloaded with:

    * 100 books
    * 3 audiobooks (with previews)
    * 5 magazines/newspapers
  * Search by category or keyword.

* 🎧 **Audiobook Support**

  * Preview MP3 samples before borrowing.
  * Borrow audiobooks for 1–7 days.
  * Automatic expiry after the due date.
  * Rental fee applied (₹50/day).

* ⏳ **Borrowing & Returns**

  * Borrow any item for 1–7 days.
  * Automatic fine calculation for late returns (₹10/day).
  * Instant fine clearance option.

* 📰 **Subscriptions**

  * Subscribe to magazines/newspapers with daily, weekly, or monthly frequency.

* 📝 **User History**

  * Complete borrowing, returning, subscription, and fine payment history.

---

## 🛠️ Tech Stack

* **Frontend/UI:** [Streamlit](https://streamlit.io/)
* **Backend:** Python
* **Storage:** JSON file (lightweight database)
* **Dependencies:** pandas, datetime, base64, random, os

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/LibraNet.git
cd LibraNet
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

* Windows:

  ```bash
  venv\Scripts\activate
  ```
* Linux/Mac:

  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

(If `requirements.txt` is missing, install manually:)

```bash
pip install streamlit pandas
```

### 4. Run the App

```bash
streamlit run app.py
```

---

## 📂 Project Structure

```
LibraNet/
│── app.py              # Main Streamlit application
│── library_data.json   # JSON-based storage (auto-generated/reset)
│── previews/           # Folder for audiobook preview MP3 files
│── requirements.txt    # Dependencies
└── README.md           # Project documentation
```

---

## ⚡ Usage

1. **Register/Login** via the sidebar.
2. **Browse Catalog** by selecting category & searching.
3. **Borrow Items** (books, audiobooks, magazines).
4. **Return Items** – fines auto-calculated if late.
5. **Pay Fines** directly via UI.
6. **Subscribe** to newspapers/magazines.
7. **Preview Audiobooks** before renting.
8. **Check History** for all transactions.

---

## 🔮 Future Enhancements

* 💳 Payment gateway integration (Razorpay/Stripe).
* 🛢️ Replace JSON with **SQLite/PostgreSQL** for scalability.
* 🌐 Multi-user deployment on cloud servers.
* 📈 Admin analytics dashboard (borrow trends, popular items).


Would you like me to also generate a **requirements.txt** file for your repo (so users don’t have to install manually)?
