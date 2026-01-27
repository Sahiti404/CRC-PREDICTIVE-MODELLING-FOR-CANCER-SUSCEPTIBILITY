# Major Project

## 📌 Project Overview

**Short Description:**
This project is a healthcare-focused web application for the early prediction of sporadic Colorectal Cancer (CRC) risk. It uses a biologically grounded stochastic model based on the accumulation of somatic mutations in APC, KRAS, and TP53 genes to provide a personalised 5–10 year cancer risk estimate, enabling proactive and preventive clinical decision-making.

This project is a healthcare-focused full-stack application for the **early prediction of sporadic Colorectal Cancer (CRC) risk** using a biologically grounded stochastic mathematical model.

Unlike traditional screening tools that detect cancer only after a tumor forms, this system is designed to **predict future CRC susceptibility 5–10 years in advance** by modeling the sequential accumulation of somatic mutations in three key driver genes:

* **APC**
* **KRAS**
* **TP53**

The theoretical foundation of this project is based on the stochastic evolutionary model proposed by **Paterson et al. (2020)**, which simulates:

* Mutation rates in colonic crypt stem cells
* Selective fitness advantage of mutant clones
* Crypt fission and clonal expansion
* Waiting time to malignant transformation

The system bridges the gap between:

* Hereditary risk tools (MMRpro, PREMM5), and
* The unmet need for **sporadic, non-hereditary CRC prediction** in the general population.

---

## 🎯 What This Project Does

This application provides a **predictive risk assessment tool for sporadic Colorectal Cancer** by combining clinical inputs with a stochastic biological model.

The system allows clinicians or users to:

* Enter patient-specific clinical and genetic parameters
* Simulate the stochastic accumulation of somatic mutations in APC, KRAS, and TP53
* Compute a **personalised 5–10 year CRC risk profile**
* Identify high-risk individuals before clinical symptoms or detectable lesions appear

In simple terms, the system:

1. Takes individual patient input from the frontend
2. Validates and processes it in the backend
3. Sends it to the ML service implementing the stochastic model
4. Computes mutation-driven cancer initiation timelines
5. Returns a personalised CRC risk prediction
6. Displays the risk profile to the user

This project is:

* **Predictive**, not diagnostic
* Focused on **sporadic CRC**, not hereditary syndromes
* Biologically grounded in the Vogelstein mutation sequence

---

## 🏗️ Project Structure

```
major_project/
│
├── backend/            # Node.js + Express backend
│   ├── config/        # Database configuration
│   ├── middleware/   # Authentication middleware
│   ├── models/       # MongoDB models
│   ├── server.js     # Main backend entry point
│   └── package.json
│
├── frontend/          # Frontend (Vite + React)
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── ml_services/       # Machine Learning microservice
│   ├── app.py        # Flask application
│   ├── *.csv         # Trained model coefficients and datasets
│
└── README.md
```

---

## ⚙️ Technologies Used

### Frontend

* Vite
* React
* JavaScript / HTML / CSS

### Backend

* Node.js
* Express.js
* MongoDB (Mongoose)
* JWT Authentication

### Machine Learning Service

* Python
* Flask
* Pandas, NumPy, scikit-learn

---

## 🚀 How to Run the Project

You need to run **three services separately**: Backend, Frontend, and ML Service.

---

### 1️⃣ Backend Setup

```bash
cd major_project/backend
npm install
```

Create a `.env` file inside `backend/` with the following variables:

```
PORT=5000
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_secret_key
```

Start the backend server:

```bash
npm start
```

Backend will run on:

```
http://localhost:5000
```

---

### 2️⃣ Frontend Setup

```bash
cd major_project/frontend
npm install
npm run dev
```

Frontend will run on:

```
http://localhost:5173
```

---

### 3️⃣ Machine Learning Service Setup

```bash
cd major_project/ml_services
pip install -r requirements.txt   # if available
python app.py
```

ML service will typically run on:

```
http://localhost:8000
```

---

## 🔗 API Communication

* Frontend communicates with Backend via REST APIs
* Backend communicates with ML Service for prediction requests
* Authentication is handled using JWT tokens

---

## 📊 Features

* User authentication (Register / Login)
* Secure API using JWT
* Prediction system using trained ML models
* Separate ML microservice architecture
* Modular and scalable project structure

---
