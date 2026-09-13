🏏 Cricket Analytics

A full-stack cricket analytics platform for exploring international cricket and IPL data through player, team, match, venue, season and leaderboard analytics, with an AI/ML-powered ODI match predictor and Monte Carlo tournament simulator.

Live Application

Frontend: https://cricket-analytics-two.vercel.app/

GitHub: https://github.com/MallickSayan407/CricketAnalytics

Overview

Cricket Analytics combines a large historical cricket dataset with a Java/Spring Boot REST backend, a React frontend, and a Python machine-learning service.

The application supports:

International ODI analytics

International Test analytics

International T20I analytics

Indian Premier League (IPL) analytics

Player profiles and career statistics

Player-to-player comparison

Team profiles and performance analytics

Match and scorecard exploration

Venue analytics

Competition and season exploration

Career and competition leaderboards

ODI match prediction using machine learning

ODI tournament simulation using Monte Carlo methods

The project is organized as a single repository containing the backend, frontend and data/ML layers.

Architecture

                         ┌──────────────────────────┐
                         │       React Frontend     │
                         │   React + Recharts + CSS │
                         │        Vercel            │
                         └────────────┬─────────────┘
                                      │ REST / JSON
                                      ▼
                         ┌──────────────────────────┐
                         │     Spring Boot API      │
                         │ Java 21 + JPA + REST     │
                         │       Railway            │
                         └───────────┬───────┬──────┘
                                     │       │
                         SQL / JPA    │       │ HTTP
                                     ▼       ▼
                         ┌──────────────┐  ┌─────────────────────┐
                         │    MySQL     │  │ Python ML API       │
                         │   Railway    │  │ FastAPI + scikit-   │
                         │              │  │ learn + joblib      │
                         └──────────────┘  └─────────────────────┘

Repository Structure

CricketAnalytics/
│
├── cricket-analytics-backend/
│   ├── src/
│   ├── build.gradle
│   ├── gradlew
│   └── ...
│
├── cricket-analytics-frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── cricket-analytics-data/
│   ├── ml/
│   │   ├── api/
│   │   ├── models/
│   │   ├── scripts/
│   │   └── datasets/
│   ├── processed/
│   └── ...
│
├── backups/
├── .gitignore
└── README.md

Technology Stack

Frontend

React

JavaScript

Vite

Recharts

Axios

CSS

Vercel

Backend

Java 21

Spring Boot 4.1.1

Spring Web MVC

Spring Data JPA

Hibernate

Jakarta Bean Validation

Lombok

MySQL

Gradle

REST APIs

Machine Learning

Python 3.11

Pandas

NumPy

scikit-learn

XGBoost

FastAPI

Uvicorn

Joblib

Development Tools

IntelliJ IDEA / Eclipse

MySQL Workbench

Postman

Git

GitHub

Data Coverage

The database contains historical records from:

Competition

Coverage

International ODI

Historical ODI dataset

International Test

Historical Test dataset

International T20I

Historical T20I dataset

Indian Premier League

Historical IPL dataset

The imported production database contains approximately:

11,040 matches

8,416 players

216 teams

602 venues

95 seasons

4 competitions

These counts represent the imported dataset at the time of deployment and can change if the dataset is updated.

Main Application Modules

Dashboard

Provides a high-level view of the cricket database, including player, team, match and competition counts, together with leaderboard highlights.

Players

Players can be searched and explored through individual profile pages.

Player profiles include:

Career overview

Batting statistics

Bowling statistics

Match-level performance

Recent form

Runs by match

Strike rate by match

Wickets by match

Match-by-match records

Player Comparison

Two players can be compared across:

Overall career

International ODI

International Test

International T20I

IPL

Available seasons

Teams

Team pages provide:

Match record

Wins/losses/ties/no-results

Win percentage

Runs scored

Runs conceded

Average runs

Run rate

Bowling rate

Net run rate

Performance charts

Matches

The match explorer provides access to recorded matches and scorecard information.

Venues

Venue pages provide information about cricket grounds and venue-level performance.

Seasons

Competition seasons can be explored independently, including international and IPL seasons.

Leaderboards

Leaderboards support rankings for:

Runs

Batting average

Strike rate

Centuries

Wickets

They can be filtered by competition and season.

AI / ML ODI Predictor

The project includes a pre-match men's ODI classifier.

Prediction

The predictor estimates:

Probability that Team A wins
Probability that Team B wins

The model uses historical information available before the prediction date, including:

Team historical match record

Team win rate

Recent form

Historical scoring performance

Historical wickets

Venue-specific records

Head-to-head records

Toss and in-match statistics are intentionally not used because the predictor is designed as a pre-match model.

Production Model

Model: Logistic Regression
Feature Set: V2
Features: 51
Preprocessing: StandardScaler
C: 0.001
Calibration: Raw model probabilities
Artifact: odi_v2_production_model.joblib
Version: ODI_V2_PRODUCTION_1.0

Locked Evaluation

The final locked test set contained 488 matches.

Key results:

Metric

Score

Accuracy

61.68%

Precision

56.84%

Recall

80.60%

F1

66.67%

ROC-AUC

67.35%

Log Loss

0.6656

Brier Score

0.2364

The model is intended as an analytics/educational prediction feature, not as a guarantee of match outcomes.

ODI Tournament Simulator

The application also includes an ODI tournament simulator.

Default tournament format:

8 teams

Single round-robin league

28 league matches

Top 4 qualify

1st vs 4th — Semi-final 1

2nd vs 3rd — Semi-final 2

Final

Monte Carlo Simulation

The simulator repeatedly generates complete tournaments using the ODI model's match probabilities.

For each team it reports:

Qualification probability

Final appearance probability

Championship probability

1st-place count

2nd-place count

3rd-place count

4th-place count

A single-tournament mode is also available to inspect one simulated league table and playoff bracket.

The simulator is stochastic, so repeated runs can produce different results.

Backend API

The Spring Boot application exposes REST endpoints for the application's analytics modules.

Representative endpoint groups include:

/api/players
/api/teams
/api/matches
/api/venues
/api/seasons
/api/leaderboards
/api/predictor
/api/simulator/odi

The exact endpoint list is implemented in the backend controllers.

The Python ML service exposes:

GET  /health
GET  /model-info
POST /predict/odi

Local Development

Prerequisites

Install:

Java 21

Python 3.11

Node.js

npm

MySQL

Git

1. Clone

git clone https://github.com/MallickSayan407/CricketAnalytics.git
cd CricketAnalytics

2. Database

Create a MySQL database:

CREATE DATABASE cricket_analytics;

Configure the backend environment variables:

DB_URL=jdbc:mysql://localhost:3306/cricket_analytics
DB_USERNAME=root
DB_PASSWORD=<your-password>

Do not place database passwords in source code.

3. Start the ML API

From:

cricket-analytics-data

create/activate the Python virtual environment and install:

pip install -r ml/api/requirements.txt

Start FastAPI:

python -m uvicorn ml.api.app:app --host 127.0.0.1 --port 8000 --http h11

4. Start the Spring Boot Backend

From:

cricket-analytics-backend

set the database password and run:

./gradlew bootRun

On Windows PowerShell:

$env:DB_PASSWORD="<your-password>"
.\gradlew bootRun

The backend runs on:

http://localhost:8080

5. Start the Frontend

From:

cricket-analytics-frontend

create:

.env.local

with:

VITE_API_BASE_URL=http://localhost:8080/api

Then:

npm install
npm run dev

The Vite development server will provide the local frontend URL.

Production Deployment

The project is deployed as a multi-service application:

React frontend  → Vercel
Spring Boot API → Railway
FastAPI ML API  → Railway
MySQL database  → Railway

The frontend communicates with the Spring Boot API.

The Spring Boot API communicates with MySQL and the ML service.

The MySQL database remains private inside Railway.

Environment Variables

Frontend

VITE_API_BASE_URL=<spring-boot-api-url>/api

Spring Boot

DB_URL=<railway-jdbc-url>
DB_USERNAME=<railway-mysql-user>
DB_PASSWORD=<railway-mysql-password>
ML_API_BASE_URL=<ml-api-url>
PORT=<railway-port>

FastAPI

DB_HOST=<mysql-host>
DB_PORT=<mysql-port>
DB_NAME=<mysql-database>
DB_USERNAME=<mysql-user>
DB_PASSWORD=<mysql-password>
PORT=<railway-port>

Secrets should be configured through the hosting platform's environment-variable system and must not be committed to Git.

Testing

The project was tested at multiple layers during development:

Backend Gradle build

REST API testing with Postman

Frontend production build

Browser-based route testing

Database reconciliation after data imports

ODI ML model evaluation

Historical ODI predictor replay validation

FastAPI health/model/prediction tests

Spring Boot → FastAPI end-to-end prediction

ODI single-tournament simulation

Monte Carlo tournament integrity checks

Production frontend verification

Data Engineering

The data pipeline processes raw cricket JSON datasets into normalized structures used by the backend.

The pipeline covers:

Raw dataset inspection

Match and delivery processing

Team normalization

Player registry creation

Venue normalization

Match creation

Match-team statistics

Player-match performance

Career/player statistics

Database import

Aggregate reconciliation

Large raw datasets and generated model artifacts are intentionally excluded from normal Git tracking where appropriate.

Git Repository

This project uses one Git repository for the complete application:

CricketAnalytics
├── cricket-analytics-backend
├── cricket-analytics-frontend
└── cricket-analytics-data

This keeps the frontend, backend and ML/data work versioned together.

Security Notes

Database credentials are supplied through environment variables.

Local .env/.env.local files are ignored by Git.

Large raw datasets are excluded from Git tracking.

Python virtual environments are excluded from Git.

Railway local metadata is excluded from Git.

Production services use platform-managed environment variables.

Project Status

Completed

Cricket data ingestion

International ODI analytics

International Test analytics

International T20I analytics

IPL analytics

Player analytics

Team analytics

Match explorer

Venue explorer

Season explorer

Leaderboards

Player comparison

ODI ML predictor

ODI tournament simulator

Monte Carlo tournament simulation

React production build

Railway MySQL deployment

Railway ML API deployment

Vercel frontend deployment

Production browser verification

Intentionally Not Included

What-If scenario simulation

Future Improvements

Possible future work includes:

Additional prediction models for Test and T20I cricket

More advanced model calibration

Additional player and team visualizations

Automated data refresh pipelines

More granular venue analysis

Improved mobile-first layouts

Expanded API documentation

Disclaimer

Cricket Analytics is a portfolio/analytics project built for data exploration and machine-learning experimentation. Prediction probabilities are statistical model outputs and should not be interpreted as certain outcomes.

Author

Subrata Mallick

B.Tech — Electronics and Communication Engineering

Interested in software development, full-stack engineering, data analytics and machine learning.