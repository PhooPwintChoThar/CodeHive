# CodeHive - Collaborative Learning Platform 🐝

> Where teaching innovation meets learning excellence

![CodeHive](https://img.shields.io/badge/CodeHive-Education_Platform-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Python-green)
![AI Powered](https://img.shields.io/badge/AI-Powered-orange)

A comprehensive educational platform that brings together teachers and students with AI-powered quizzes, discussion forums, plagiarism detection, and personalized learning analytics.

## 🚀 Live Demo

**Experience CodeHive Live:** [Demo Link Coming Soon]

*Note: The live demo will be available once the project is deployed*

## 🎯 Quick Start - Test Immediately

Use the pre-configured accounts in data.py to explore the platform.

*No password required - just enter the ID*

## ✨ Features

### 🎓 For Students
- **AI-Powered Quizzes** with real-time code testing
- **Discussion Forums** for collaborative learning
- **AI Tutor** for instant course help
- **Skill Analytics** with visual progress tracking
- **Performance Dashboard** with detailed feedback

### 👨‍🏫 For Teachers
- **Smart Quiz Creation** with AI validation
- **Automated Grading** with detailed feedback
- **Plagiarism Detection** using AST analysis
- **Student Progress Monitoring**
- **Course Management** tools

### 🔒 Security & Integrity
- **Quiz Lockdown Mode** with tab switching detection
- **Activity Logging** for academic integrity
- **Time-limited Assessments**
- **Real-time Monitoring**

## 🛠 Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd codehive

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
