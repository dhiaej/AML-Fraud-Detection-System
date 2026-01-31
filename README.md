# 🛡️ AML Fraud Detection System

> A high-fidelity Anti-Money Laundering (AML) detection platform powered by Graph Neural Networks (GNNs) with real-time transaction monitoring, risk scoring, and explainable AI decision support.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0+-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The AML Fraud Detection System is a comprehensive platform designed to identify and prevent money laundering activities through advanced graph-based machine learning. The system analyzes transaction patterns, detects suspicious behaviors (structuring, smurfing, circular flows), and provides real-time risk assessments with explainable AI insights.

### Key Capabilities

- **Real-time Transaction Monitoring**: Track and analyze transactions as they occur
- **AI-Powered Risk Scoring**: Graph Neural Network (GNN) models for fraud detection
- **Pattern Detection**: Identify structuring, smurfing, circular flows, and high-velocity transactions
- **Account Management**: Freeze/unfreeze accounts, handle appeals, and review audit trails
- **Explainable AI**: Detailed audit logs showing why transactions were flagged
- **Professional Dashboards**: Separate interfaces for users and administrators

## ✨ Features

### User Dashboard
- 💰 **Banking Interface**: Deposit funds, send transactions, view balance
- 📊 **Financial Overview**: Monthly spending, credit score, transaction history
- 🚨 **Compliance Alerts**: Real-time notifications for flagged transactions
- 📝 **Appeal System**: Submit appeals for frozen accounts

### Admin Dashboard
- 🔍 **Transaction Monitor**: Filter and analyze all transactions
- ⚠️ **Risk Alerts**: Dedicated view for flagged users and suspicious activities
- 📈 **Visual Analytics**: Risk score visualizations and transaction activity graphs
- 🎯 **AI Decision Support**: Detailed risk assessments with contributing factors
- 📋 **Audit Trails**: Complete explainability logs for flagged transactions
- 🔒 **Account Management**: Freeze/unfreeze accounts, approve/reject appeals

### Detection Capabilities
- **Structuring Detection**: Identifies transactions near $10,000 threshold
- **Smurfing Detection**: Detects multiple small transactions
- **Circular Flow Detection**: Identifies money laundering rings
- **High Velocity Detection**: Flags rapid transaction patterns
- **Risk Scoring**: AI-powered risk assessment (0-100%)

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (with migration support)
- **AI/ML**: PyTorch Geometric (GNN models)
- **Authentication**: Token-based auth with role management

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **HTTP Client**: Axios

### Development Tools
- **API Documentation**: FastAPI auto-generated Swagger UI
- **Code Quality**: TypeScript strict mode, ESLint
- **Database Migrations**: Custom migration scripts

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React Client  │ ◄─────► │   FastAPI Server │ ◄─────► │   SQLite DB     │
│   (Port 3000)   │  HTTP   │   (Port 8000)   │  SQL    │   (Local)       │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                      │
                                      ▼
                            ┌─────────────────┐
                            │  GNN Model      │
                            │  (Risk Scoring) │
                            └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/aml-fraud-detection.git
   cd aml-fraud-detection
   ```

2. **Set up the Backend**
   ```bash
   cd server
   pip install -r requirements.txt
   
   # Run database migration
   python migrate_database.py
   
   # Seed mock data (optional)
   python seed_mock_data.py
   
   # Create admin user (optional)
   python create_admin.py
   
   # Start the server
   uvicorn src.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

3. **Set up the Frontend**
   ```bash
   cd client
   npm install
   npm start
   ```
   The app will open at `http://localhost:3000`

### Default Credentials

- **Admin**: Email ending with `@admin.com` (e.g., `admin@admin.com`)
- **Regular User**: Any other email format

## 📁 Project Structure

```
aml-fraud-detection/
├── server/
│   ├── src/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database/
│   │   │   ├── sqlite_connector.py # Database operations
│   │   │   └── neo4j_connector.py  # Neo4j connector (optional)
│   │   ├── routes/
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   └── fraud_detection.py  # Fraud detection endpoints
│   │   ├── services/
│   │   │   ├── fraud_service.py    # Fraud detection logic
│   │   │   └── transaction_service.py # Transaction processing
│   │   ├── models/
│   │   │   └── gnn_model.py        # GNN model implementation
│   │   └── schemas/
│   │       └── fraud_schemas.py   # Pydantic models
│   ├── migrate_database.py         # Database migration script
│   ├── seed_mock_data.py           # Mock data generator
│   ├── create_admin.py              # Admin user creation
│   └── requirements.txt             # Python dependencies
│
├── client/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.tsx           # Login component
│   │   │   ├── Signup.tsx          # Signup component
│   │   │   ├── UserDashboard.tsx   # User dashboard
│   │   │   └── AdminDashboard.tsx  # Admin dashboard
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript type definitions
│   │   └── App.tsx                  # Main app component
│   ├── package.json                 # Node dependencies
│   └── tailwind.config.js            # Tailwind CSS configuration
│
└── README.md                         # This file
```

## 💻 Usage

### User Workflow

1. **Sign Up/Login**: Create an account or login with existing credentials
2. **Deposit Funds**: Add funds to your account (simulation)
3. **Send Transactions**: Transfer money to other users
4. **Monitor Activity**: View transaction history and account status
5. **Appeal Frozen Accounts**: Submit appeals if account is frozen

### Admin Workflow

1. **Login**: Access admin dashboard with admin credentials
2. **Monitor Transactions**: View all transactions with filtering options
3. **Review Risk Alerts**: Analyze flagged users and suspicious activities
4. **View Audit Logs**: Check explainability factors for flagged transactions
5. **Manage Accounts**: Freeze/unfreeze accounts, approve/reject appeals

### API Endpoints

Key endpoints include:
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/users/{user_id}` - Get user details
- `GET /api/v1/detect-fraud/{user_id}` - Get fraud analysis
- `GET /api/v1/audit-logs/{user_id}` - Get audit trail

Full API documentation available at `http://localhost:8000/docs`

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript strict mode for frontend
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the powerful frontend library
- PyTorch Geometric for GNN capabilities
- Tailwind CSS for beautiful styling

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This is a demonstration system. For production use, implement additional security measures, use proper authentication (JWT), encrypt sensitive data, and follow financial regulations.
