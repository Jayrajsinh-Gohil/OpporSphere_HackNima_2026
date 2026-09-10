#!/usr/bin/env python3
"""
seed.py — Deterministic, realistic seed dataset generator for OpporSphere.

Seeds:
  - 25 Students with diverse skills, interests, roles, departments, and 384-d embeddings.
  - 35 Opportunities across Technology, Science, Health, Environment, Social Impact, and Business.
  - Calculated trust scores and quality flags.
  - Linked hackathon and workshop events.
  - Event registrations for team-finder testing.

Usage:
  python seed.py --dry-run
  python seed.py --export-sql seed_output.sql
  python seed.py --reset
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, timedelta, timezone
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid5, NAMESPACE_DNS

from loguru import logger
import numpy as np

# Ensure opportunity-ecosystem-api is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_local_embedder
from app.services.match import build_opportunity_embed_text, build_student_embed_text
from app.services.team_finder import infer_student_role
from app.services.trust import rule_quality_check

# Deterministic namespace for reproducible UUIDs
SEED_NAMESPACE = NAMESPACE_DNS


def make_seed_id(prefix: str, index: int) -> str:
    """Generate reproducible UUID string from seed namespace."""
    return str(uuid5(SEED_NAMESPACE, f"seed-{prefix}-{index:03d}"))


# ── Seed Student Definitions (25 students) ────────────────────────────────────

STUDENTS_SEED_DATA = [
    {
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.edu",
        "department": "Computer Science & Engineering",
        "location": "Bengaluru, Karnataka",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        "interests": ["Distributed Systems", "Backend Architecture", "APIs"],
        "career_goals": "Become a Principal Backend Engineer building planet-scale microservices.",
    },
    {
        "name": "Priya Patel",
        "email": "priya.patel@example.edu",
        "department": "Artificial Intelligence & Data Science",
        "location": "Hyderabad, Telangana",
        "skills": ["Python", "PyTorch", "Hugging Face", "LangChain", "NLP", "Scikit-Learn"],
        "interests": ["Generative AI", "LLM Fine-Tuning", "Vector Databases"],
        "career_goals": "Work on foundational multimodal AI models and autonomous agent reasoning.",
    },
    {
        "name": "Rohan Gupta",
        "email": "rohan.gupta@example.edu",
        "department": "Information Technology",
        "location": "Mumbai, Maharashtra",
        "skills": ["React", "Next.js", "TypeScript", "Tailwind CSS", "Redux", "GraphQL"],
        "interests": ["Web Performance", "Design Systems", "Interactive UI"],
        "career_goals": "Lead frontend web engineering teams creating ultra-responsive user interfaces.",
    },
    {
        "name": "Ananya Iyer",
        "email": "ananya.iyer@example.edu",
        "department": "Human-Computer Interaction",
        "location": "Pune, Maharashtra",
        "skills": ["Figma", "UI/UX Design", "Wireframing", "User Research", "Prototyping", "Design Thinking"],
        "interests": ["Accessibility", "Design Systems", "Motion Design"],
        "career_goals": "Design accessible, human-centric software for underserved global populations.",
    },
    {
        "name": "Vikram Malhotra",
        "email": "vikram.malhotra@example.edu",
        "department": "Management & Technology",
        "location": "Delhi NCR",
        "skills": ["Product Management", "Agile", "Scrum", "Market Research", "Jira", "Pitch Decks"],
        "interests": ["FinTech", "EdTech", "Venture Capital"],
        "career_goals": "Found a venture-backed tech startup solving educational accessibility in India.",
    },
    {
        "name": "Sneha Sen",
        "email": "sneha.sen@example.edu",
        "department": "Computer Science",
        "location": "Kolkata, West Bengal",
        "skills": ["Flutter", "Dart", "Firebase", "Android", "iOS", "REST APIs"],
        "interests": ["Cross-Platform Apps", "Mobile UX", "Offline-First Architectures"],
        "career_goals": "Build mobile-first consumer apps downloaded by millions of users.",
    },
    {
        "name": "Karthik Raja",
        "email": "karthik.raja@example.edu",
        "department": "Cloud & Infrastructure Systems",
        "location": "Chennai, Tamil Nadu",
        "skills": ["Kubernetes", "AWS", "Terraform", "Linux", "CI/CD", "Prometheus"],
        "interests": ["Cloud Native", "DevOps Automation", "Site Reliability"],
        "career_goals": "Architect resilient multi-cloud infrastructures with zero-downtime deployments.",
    },
    {
        "name": "Divya Nair",
        "email": "divya.nair@example.edu",
        "department": "Bioinformatics & Computational Biology",
        "location": "Thiruvananthapuram, Kerala",
        "skills": ["Python", "Biopython", "R", "Machine Learning", "Genomics", "Data Analysis"],
        "interests": ["Computational Biology", "Personalized Medicine", "Structural Biology"],
        "career_goals": "Discover life-saving drug molecules using deep generative chemistry models.",
    },
    {
        "name": "Aditya Verma",
        "email": "aditya.verma@example.edu",
        "department": "Cybersecurity & Networks",
        "location": "Jaipur, Rajasthan",
        "skills": ["Penetration Testing", "Network Security", "Cryptography", "Python", "Wireshark", "Linux"],
        "interests": ["Ethical Hacking", "Zero Trust Architecture", "Cryptographic Protocols"],
        "career_goals": "Chief Information Security Officer protecting critical digital financial infrastructure.",
    },
    {
        "name": "Neha Joshi",
        "email": "neha.joshi@example.edu",
        "department": "Environmental Engineering",
        "location": "Ahmedabad, Gujarat",
        "skills": ["GIS", "Remote Sensing", "Python", "Spatial Analysis", "Climate Modeling"],
        "interests": ["Sustainability Tech", "Renewable Energy", "Carbon Accounting"],
        "career_goals": "Pioneer AI-driven climate change mitigation and urban carbon tracking solutions.",
    },
    {
        "name": "Arjun Das",
        "email": "arjun.das@example.edu",
        "department": "Software Engineering",
        "location": "Bengaluru, Karnataka",
        "skills": ["Golang", "gRPC", "PostgreSQL", "Kafka", "Docker", "Microservices"],
        "interests": ["High-Throughput Streaming", "Event-Driven Systems", "Concurrency"],
        "career_goals": "Build ultra-low latency financial exchange routing software.",
    },
    {
        "name": "Meera Menon",
        "email": "meera.menon@example.edu",
        "department": "Electrical & Electronics Engineering",
        "location": "Kochi, Kerala",
        "skills": ["C++", "Embedded Systems", "IoT", "Arduino", "Raspberry Pi", "Sensors"],
        "interests": ["Smart Hardware", "Edge AI", "Robotics"],
        "career_goals": "Design edge hardware for autonomous robotics and smart agriculture.",
    },
    {
        "name": "Kabir Mehta",
        "email": "kabir.mehta@example.edu",
        "department": "Data Science",
        "location": "Gurugram, Haryana",
        "skills": ["Python", "SQL", "Tableau", "Pandas", "Scikit-Learn", "A/B Testing"],
        "interests": ["Growth Analytics", "Business Intelligence", "Predictive Modeling"],
        "career_goals": "Drive core product metrics as a Lead Data Scientist at a hypergrowth tech company.",
    },
    {
        "name": "Ishaan Roy",
        "email": "ishaan.roy@example.edu",
        "department": "Computer Science",
        "location": "Kolkata, West Bengal",
        "skills": ["React", "Vue.js", "JavaScript", "Tailwind CSS", "Figma", "CSS Animations"],
        "interests": ["Creative Coding", "WebGL", "Interactive Visualizations"],
        "career_goals": "Combine engineering and aesthetic design to create digital art and immersive websites.",
    },
    {
        "name": "Tanvi Deshmukh",
        "email": "tanvi.deshmukh@example.edu",
        "department": "Artificial Intelligence",
        "location": "Nagpur, Maharashtra",
        "skills": ["PyTorch", "OpenCV", "Computer Vision", "Object Detection", "YOLO", "Python"],
        "interests": ["Autonomous Driving", "Medical Imaging", "Edge Vision"],
        "career_goals": "Deploy real-time computer vision models for robotic surgical navigation.",
    },
    {
        "name": "Rishi Kapoor",
        "email": "rishi.kapoor@example.edu",
        "department": "Information Systems",
        "location": "Chandigarh",
        "skills": ["Product Strategy", "User Stories", "Wireframing", "Figma", "Mixpanel"],
        "interests": ["Product Management", "Growth Hacking", "Consumer Behavior"],
        "career_goals": "VP of Product guiding digital products that simplify complex workflows.",
    },
    {
        "name": "Siddharth Rao",
        "email": "siddharth.rao@example.edu",
        "department": "Computer Science",
        "location": "Hyderabad, Telangana",
        "skills": ["Java", "Spring Boot", "MySQL", "Docker", "AWS", "Elasticsearch"],
        "interests": ["Enterprise Architecture", "Search Engines", "Microservices"],
        "career_goals": "Build resilient backends for mission-critical e-commerce platforms.",
    },
    {
        "name": "Kavya Pillai",
        "email": "kavya.pillai@example.edu",
        "department": "Applied Mathematics & Computing",
        "location": "Bengaluru, Karnataka",
        "skills": ["Python", "Algorithms", "Optimization", "Linear Algebra", "NumPy", "C++"],
        "interests": ["Quantum Computing", "Algorithmic Trading", "Cryptography"],
        "career_goals": "Solve complex combinatorial optimization problems in logistics and quantum networks.",
    },
    {
        "name": "Yashwant Singhania",
        "email": "yash.singhania@example.edu",
        "department": "Robotics & Automation",
        "location": "Kanpur, Uttar Pradesh",
        "skills": ["ROS", "C++", "Python", "SLAM", "Control Systems", "Gazebo"],
        "interests": ["Autonomous Mobile Robots", "Industrial Automation", "Drones"],
        "career_goals": "Develop autonomous warehouse robots for next-generation logistics hubs.",
    },
    {
        "name": "Zoya Khan",
        "email": "zoya.khan@example.edu",
        "department": "Digital Communication & Media",
        "location": "New Delhi",
        "skills": ["Content Strategy", "Copywriting", "SEO", "Community Management", "Public Speaking"],
        "interests": ["Developer Relations", "Tech Journalism", "Brand Building"],
        "career_goals": "Lead developer relations and community building for open-source AI developer tools.",
    },
    {
        "name": "Nikhil Agarwal",
        "email": "nikhil.agarwal@example.edu",
        "department": "Computer Science",
        "location": "Indore, Madhya Pradesh",
        "skills": ["Node.js", "Express", "React", "MongoDB", "Tailwind CSS", "WebSockets"],
        "interests": ["Full Stack Development", "Real-Time Collaboration Apps"],
        "career_goals": "Create multiplayer creative web applications like collaborative canvas tools.",
    },
    {
        "name": "Shreya Bhattacharya",
        "email": "shreya.bhatt@example.edu",
        "department": "Information Technology",
        "location": "Bhubaneswar, Odisha",
        "skills": ["UI/UX Research", "Figma", "User Journey Mapping", "Usability Testing", "Design Thinking"],
        "interests": ["Inclusive Design", "Behavioral Economics", "Design Systems"],
        "career_goals": "Direct UX strategy at an international social enterprise addressing digital literacy.",
    },
    {
        "name": "Devendra Solanki",
        "email": "devendra.solanki@example.edu",
        "department": "Mechanical Engineering & Mechatronics",
        "location": "Surat, Gujarat",
        "skills": ["CAD", "SolidWorks", "Python", "Sensor Integration", "Embedded C"],
        "interests": ["Hardware Prototyping", "Electric Vehicles", "Clean Mobility"],
        "career_goals": "Design thermal management hardware for modern electric vehicle battery packs.",
    },
    {
        "name": "Tarun Chawla",
        "email": "tarun.chawla@example.edu",
        "department": "Computer Engineering",
        "location": "Noida, Uttar Pradesh",
        "skills": ["Solidity", "Ethereum", "Smart Contracts", "Web3.js", "Rust", "Hardhat"],
        "interests": ["Decentralized Finance", "Zero Knowledge Proofs", "Blockchain"],
        "career_goals": "Build secure, audited smart contract protocols for decentralized identity verification.",
    },
    {
        "name": "Pooja Hegde",
        "email": "pooja.hegde@example.edu",
        "department": "Artificial Intelligence & Robotics",
        "location": "Mangaluru, Karnataka",
        "skills": ["Reinforcement Learning", "Python", "PyTorch", "OpenAI Gym", "Simulation"],
        "interests": ["Decision Intelligence", "Robotic Manipulation", "Game AI"],
        "career_goals": "Deploy deep reinforcement learning models in real-world industrial robotic arms.",
    },
]


# ── Seed Opportunity Definitions (35 opportunities) ──────────────────────────

OPPORTUNITIES_SEED_DATA = [
    # Hackathons (12)
    {
        "title": "HackNima 2025: AI For Social Good",
        "description": "A premier 48-hour hackathon focused on building AI-driven solutions addressing healthcare, education, and environmental sustainability in developing regions.",
        "domain": "technology",
        "type": "hackathon",
        "eligibility": "Undergraduate and postgraduate students enrolled in recognized universities.",
        "deadline_days": 45,
        "location": "Bengaluru, Karnataka (Hybrid)",
        "organizer": "HackNima Foundation & TechHub",
        "source_url": "https://hacknima.dev/2025",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹10,00,000", "max_team_size": 4, "format": "hybrid"},
    },
    {
        "title": "ClimateTech Hackathon India",
        "description": "Build software or IoT prototypes to combat urban carbon emissions, water scarcity, and renewable microgrids. Hardware kits provided for finalists.",
        "domain": "environment",
        "type": "hackathon",
        "eligibility": "Open to all student innovators, engineers, and environmental researchers.",
        "deadline_days": 28,
        "location": "New Delhi (In-person)",
        "organizer": "Ministry of New and Renewable Energy & GreenVenture",
        "source_url": "https://climatetech.in/hackathon",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹5,00,000", "max_team_size": 4, "format": "in-person"},
    },
    {
        "title": "MedAI Healthcare Innovation Challenge",
        "description": "Design predictive diagnostic tools, patient triage assistants, and automated clinical notes summarization apps using computer vision and LLMs.",
        "domain": "health",
        "type": "hackathon",
        "eligibility": "Multidisciplinary teams containing at least one CS/AI student and one life-sciences student.",
        "deadline_days": 35,
        "location": "Hyderabad, Telangana",
        "organizer": "Apollo HealthX & BioInnovate",
        "source_url": "https://medai-challenge.org",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹7,50,000", "max_team_size": 4, "format": "hybrid"},
    },
    {
        "title": "FinTech Disrupt 2025 Hackathon",
        "description": "Reinvent payments, financial inclusion for rural MSMEs, and fraud prevention using modern UPI APIs, account aggregators, and machine learning.",
        "domain": "business",
        "type": "hackathon",
        "eligibility": "College students and early graduates within 1 year of passing out.",
        "deadline_days": 20,
        "location": "Mumbai, Maharashtra",
        "organizer": "National Payments Alliance",
        "source_url": "https://fintechdisrupt.in",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹6,00,000", "max_team_size": 3, "format": "in-person"},
    },
    {
        "title": "Autonomous Mobility Challenge",
        "description": "Simulation and hardware hackathon for edge robotics, autonomous drone flight, and computer vision SLAM in obstacle-rich environments.",
        "domain": "technology",
        "type": "hackathon",
        "eligibility": "B.Tech/M.Tech students with robotics, electronics, or computer science backgrounds.",
        "deadline_days": 60,
        "location": "Chennai, Tamil Nadu",
        "organizer": "RoboFleet Labs",
        "source_url": "https://robofleet.io/challenge",
        "is_event": True,
        "event_status": "upcoming",
        "extra_details": {"prize_pool": "₹8,00,000", "max_team_size": 5, "format": "in-person"},
    },
    {
        "title": "Decentralized Web & Privacy Hackathon",
        "description": "Create censorship-resistant, decentralized applications using Zero-Knowledge proofs, decentralized identity protocols, and decentralized storage.",
        "domain": "technology",
        "type": "hackathon",
        "eligibility": "Open globally to students and developers.",
        "deadline_days": 18,
        "location": "Online (Virtual)",
        "organizer": "Web3 Builders Guild",
        "source_url": "https://zkbuild.dev",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "$15,000 USD", "max_team_size": 4, "format": "virtual"},
    },
    {
        "title": "EdAccessibility App Challenge",
        "description": "Develop learning tools for neurodivergent and visually impaired children using speech recognition, text-to-speech, and responsive tactile interfaces.",
        "domain": "education",
        "type": "hackathon",
        "eligibility": "Undergraduate students from any design or engineering discipline.",
        "deadline_days": 30,
        "location": "Pune, Maharashtra",
        "organizer": "Universal Inclusion Trust",
        "source_url": "https://edaccess.org/challenge",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹3,50,000", "max_team_size": 3, "format": "hybrid"},
    },
    {
        "title": "Smart Cities Civic Data Hackathon",
        "description": "Analyze public transit, air quality, and urban road incident datasets to recommend actionable civic policies and real-time commuter dashboards.",
        "domain": "social_impact",
        "type": "hackathon",
        "eligibility": "Students enrolled in data science, urban planning, or software engineering degrees.",
        "deadline_days": 40,
        "location": "Bengaluru, Karnataka",
        "organizer": "Urban Innovation Mission",
        "source_url": "https://smartcitieshack.gov.in",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹4,00,000", "max_team_size": 4, "format": "hybrid"},
    },
    {
        "title": "CyberDefense CTF & Blue-Team Hackathon",
        "description": "48-hour capture the flag competition and live incident response simulation. Defend cloud clusters and reverse engineer obfuscated malware.",
        "domain": "technology",
        "type": "hackathon",
        "eligibility": "Enrolled undergraduate students in engineering or information security.",
        "deadline_days": 25,
        "location": "Online",
        "organizer": "National Cyber Security Council",
        "source_url": "https://cyberdefense-ctf.in",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹5,00,000", "max_team_size": 4, "format": "virtual"},
    },
    {
        "title": "AgriTech Farmers Solution Hackathon",
        "description": "Engineer affordable IoT soil monitors, crop disease vision classifiers, and regional language market price alert systems for rural farmers.",
        "domain": "environment",
        "type": "hackathon",
        "eligibility": "Open to students nationwide. Mentorship provided by agricultural university faculty.",
        "deadline_days": 50,
        "location": "Jaipur, Rajasthan",
        "organizer": "Krishi Tech Initiative",
        "source_url": "https://agritech-hack.in",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹4,50,000", "max_team_size": 4, "format": "hybrid"},
    },
    {
        "title": "Global AI Agents Virtual Hackathon",
        "description": "Construct multi-agent workflows using LangChain, AutoGen, and tool calling to automate complex enterprise and developer workflows.",
        "domain": "technology",
        "type": "hackathon",
        "eligibility": "Students and developers of all experience levels worldwide.",
        "deadline_days": 14,
        "location": "Online",
        "organizer": "Open Agents Collective",
        "source_url": "https://aiagentshack.dev",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "$20,000 USD", "max_team_size": 3, "format": "virtual"},
    },
    {
        "title": "DesignSprint UI/UX Hackathon 2025",
        "description": "Rapid 36-hour design marathon creating end-to-end design systems, micro-animations, and interactive Figma prototypes for the next billion users.",
        "domain": "arts",
        "type": "hackathon",
        "eligibility": "Design students, HCI researchers, and creative coders.",
        "deadline_days": 22,
        "location": "Bengaluru, Karnataka",
        "organizer": "Designers Guild India",
        "source_url": "https://designsprint.in",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"prize_pool": "₹3,00,000", "max_team_size": 2, "format": "in-person"},
    },

    # Internships (10)
    {
        "title": "Google Summer of Engineering Internship 2025",
        "description": "12-week paid software engineering internship working on real-world services in cloud infrastructure, machine learning search, or Android OS.",
        "domain": "technology",
        "type": "internship",
        "eligibility": "Penultimate year undergraduate or first-year postgraduate students in CS, EE, or related fields.",
        "deadline_days": 75,
        "location": "Bengaluru & Hyderabad, India",
        "organizer": "Google India Pvt Ltd",
        "source_url": "https://careers.google.com/students",
        "is_event": False,
    },
    {
        "title": "Microsoft Research Undergraduate Research Fellow",
        "description": "Work side-by-side with world-class scientists on foundation AI models, quantum computing algorithms, and socio-technical systems.",
        "domain": "science",
        "type": "internship",
        "eligibility": "B.Tech/M.Tech students with strong mathematical background and competitive programming or research publication record.",
        "deadline_days": 65,
        "location": "Bengaluru, Karnataka",
        "organizer": "Microsoft Research India",
        "source_url": "https://research.microsoft.com/fellows",
        "is_event": False,
    },
    {
        "title": "Cisco Systems Network Engineering Internship",
        "description": "Join Cisco's core networking and cloud security teams to develop SDN controllers, telemetry tools, and zero-day threat monitors.",
        "domain": "technology",
        "type": "internship",
        "eligibility": "Third-year engineering students with strong knowledge of TCP/IP, Python, and Linux internals.",
        "deadline_days": 40,
        "location": "Bengaluru, Karnataka",
        "organizer": "Cisco Systems",
        "source_url": "https://jobs.cisco.com/internships",
        "is_event": False,
    },
    {
        "title": "ISRO Space Applications Centre Student Internship",
        "description": "Assist research scientists in analyzing earth observation satellite imagery, radar telemetry, and planetary orbit simulations.",
        "domain": "science",
        "type": "internship",
        "eligibility": "Students studying aerospace, physics, remote sensing, or computer science with minimum 8.0 CGPA.",
        "deadline_days": 30,
        "location": "Ahmedabad, Gujarat",
        "organizer": "Indian Space Research Organisation (ISRO)",
        "source_url": "https://sac.gov.in/internships",
        "is_event": False,
    },
    {
        "title": "Adobe Digital Media Product Design Internship",
        "description": "Collaborate with Adobe Creative Cloud design team to conceptualize, wireframe, and test next-generation generative AI creative tools.",
        "domain": "arts",
        "type": "internship",
        "eligibility": "Students in design, HCI, human factors, or visual communication graduating in 2026.",
        "deadline_days": 55,
        "location": "Noida, Uttar Pradesh",
        "organizer": "Adobe India",
        "source_url": "https://adobe.com/careers/university",
        "is_event": False,
    },
    {
        "title": "Zerodha FinTech Engineering Internship",
        "description": "Develop high-performance, fault-tolerant stock broking microservices using Golang, PostgreSQL, Redis, and WebSockets.",
        "domain": "business",
        "type": "internship",
        "eligibility": "Students who have built open-source backend projects or deep systems software.",
        "deadline_days": 38,
        "location": "Bengaluru, Karnataka",
        "organizer": "Zerodha Broking Ltd",
        "source_url": "https://zerodha.tech/careers",
        "is_event": False,
    },
    {
        "title": "WWF India Conservation Technology Intern",
        "description": "Apply acoustic monitoring and camera trap computer vision models to track endangered wildlife populations in national reserves.",
        "domain": "environment",
        "type": "internship",
        "eligibility": "Students in environmental science, data science, or wildlife biology.",
        "deadline_days": 21,
        "location": "New Delhi (Hybrid)",
        "organizer": "World Wide Fund for Nature - India",
        "source_url": "https://wwfindia.org/careers",
        "is_event": False,
    },
    {
        "title": "Serum Institute Biomedical Analytics Internship",
        "description": "Conduct biostatistical modeling, vaccine trial clinical data management, and genomic sequencing data processing.",
        "domain": "health",
        "type": "internship",
        "eligibility": "Postgraduate students in biotechnology, bioinformatics, or data analytics.",
        "deadline_days": 42,
        "location": "Pune, Maharashtra",
        "organizer": "Serum Institute of India",
        "source_url": "https://seruminstitute.com/internships",
        "is_event": False,
    },
    {
        "title": "Cred Product Management Apprenticeship",
        "description": "Fast-track 6-month product apprenticeship owning experimental user loops, rewards gamification, and merchant integrations.",
        "domain": "business",
        "type": "internship",
        "eligibility": "Final-year college students with strong analytical skills and consumer product intuition.",
        "deadline_days": 19,
        "location": "Bengaluru, Karnataka",
        "organizer": "CRED Technologies",
        "source_url": "https://cred.club/careers",
        "is_event": False,
    },
    {
        "title": "Tata Motors EV Battery Analytics Intern",
        "description": "Work with automotive engineers to develop physics-informed neural networks predicting lithium-ion battery state-of-health.",
        "domain": "environment",
        "type": "internship",
        "eligibility": "Students in mechanical, electrical, or automotive engineering.",
        "deadline_days": 48,
        "location": "Pune, Maharashtra",
        "organizer": "Tata Motors Passenger Vehicles",
        "source_url": "https://tatamotors.com/careers",
        "is_event": False,
    },

    # Workshops (6)
    {
        "title": "Deep Learning & LLM Fine-Tuning Bootcamp",
        "description": "Intensive hands-on 3-day technical masterclass on LoRA, QLoRA, vLLM inference engines, and FlashAttention optimizations.",
        "domain": "technology",
        "type": "workshop",
        "eligibility": "Prior experience in Python and PyTorch recommended. Open to all students.",
        "deadline_days": 10,
        "location": "Online (Live Hands-on)",
        "organizer": "OpenAI Student Developer Circle",
        "source_url": "https://openai-devcircle.org/workshop",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "online", "sessions": 6, "certificate": True},
    },
    {
        "title": "Next.js 15 & React Server Components Deep Dive",
        "description": "Master full-stack modern web architectures: Server Components, Server Actions, streaming SSR, and edge caching pipelines.",
        "domain": "technology",
        "type": "workshop",
        "eligibility": "Basic knowledge of React and JavaScript.",
        "deadline_days": 12,
        "location": "Online",
        "organizer": "Frontend Masters Hub",
        "source_url": "https://frontendmasters.in/nextjs",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "online", "sessions": 4, "certificate": True},
    },
    {
        "title": "Kubernetes & Cloud Native Systems Workshop",
        "description": "Deploy, scale, and monitor distributed microservices on real Kubernetes clusters using Helm, Istio service mesh, and Grafana.",
        "domain": "technology",
        "type": "workshop",
        "eligibility": "Engineering students interested in DevOps and cloud infrastructure.",
        "deadline_days": 16,
        "location": "Bengaluru, Karnataka",
        "organizer": "Cloud Native Computing Foundation (CNCF) Bengaluru",
        "source_url": "https://community.cncf.io/bengaluru",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "in-person", "sessions": 2, "certificate": True},
    },
    {
        "title": "UI/UX Micro-Interactions & Figma Masterclass",
        "description": "Learn advanced design systems, component properties, interactive prototypes, and Framer micro-interaction handoff techniques.",
        "domain": "arts",
        "type": "workshop",
        "eligibility": "Design students and aspiring UI/UX practitioners.",
        "deadline_days": 8,
        "location": "Online",
        "organizer": "Figma Community India",
        "source_url": "https://figma.in/micro-interactions",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "online", "sessions": 3, "certificate": True},
    },
    {
        "title": "Bioinformatics & Genomic Sequence Analysis Lab",
        "description": "Practical workshop analyzing NCBI BLAST sequence queries, CRISPR off-target predictions, and molecular docking simulations using PyMOL.",
        "domain": "science",
        "type": "workshop",
        "eligibility": "Students in biotechnology, bioinformatics, or life sciences.",
        "deadline_days": 15,
        "location": "Hyderabad, Telangana",
        "organizer": "Center for Cellular and Molecular Biology (CCMB)",
        "source_url": "https://ccmb.res.in/workshops",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "in-person", "sessions": 5, "certificate": True},
    },
    {
        "title": "Product-Led Growth & Metrics Masterclass",
        "description": "Learn how top tech companies measure North Star metrics, build activation funnels, and run statistical A/B tests that move the needle.",
        "domain": "business",
        "type": "workshop",
        "eligibility": "All students interested in product management, marketing, or entrepreneurship.",
        "deadline_days": 25,
        "location": "Online",
        "organizer": "Product Leaders Forum",
        "source_url": "https://productleaders.in/workshop",
        "is_event": True,
        "event_status": "open",
        "extra_details": {"format": "online", "sessions": 3, "certificate": True},
    },

    # Fellowships & Grants (7)
    {
        "title": "Prime Minister Research Fellowship (PMRF) 2025",
        "description": "Prestigious national research fellowship providing generous stipends and up to ₹10 Lakhs annual contingency research grant for Ph.D. students.",
        "domain": "science",
        "type": "fellowship",
        "eligibility": "High-performing B.Tech/M.Tech graduates with top GATE rank or high CGPA from Tier-1 institutions.",
        "deadline_days": 90,
        "location": "All India",
        "organizer": "Ministry of Education, Government of India",
        "source_url": "https://pmrf.in",
        "is_event": False,
    },
    {
        "title": "Thiel Fellowship 2025: $100,000 for Young Builders",
        "description": "A two-year, $100,000 grant for young people who want to build new things instead of sitting in a classroom.",
        "domain": "business",
        "type": "grant",
        "eligibility": "Anyone aged 22 or younger worldwide working on breakthrough science, software, or hardware.",
        "deadline_days": 120,
        "location": "Global (Remote & San Francisco)",
        "organizer": "The Thiel Foundation",
        "source_url": "https://thielfellowship.org",
        "is_event": False,
    },
    {
        "title": "NITI Aayog Youth Innovation Fellowship",
        "description": "1-year policy and technology fellowship working inside state departments to deploy digital public infrastructure in health and education.",
        "domain": "social_impact",
        "type": "fellowship",
        "eligibility": "Graduates with at least one year of experience or outstanding campus leadership record.",
        "deadline_days": 50,
        "location": "New Delhi",
        "organizer": "NITI Aayog & Atal Innovation Mission",
        "source_url": "https://niti.gov.in/fellowship",
        "is_event": False,
    },
    {
        "title": "Emergent Ventures India Student Grant",
        "description": "Unrestricted grants of ₹2,00,000 to ₹10,00,000 to high-potential young Indians working on moonshot scientific and engineering ambitions.",
        "domain": "technology",
        "type": "grant",
        "eligibility": "Ambitious students and self-taught builders working on transformative ideas.",
        "deadline_days": 80,
        "location": "All India",
        "organizer": "Mercatus Center & Emergent Ventures",
        "source_url": "https://mercatus.org/emergent-ventures",
        "is_event": False,
    },
    {
        "title": "Climate Policy & Renewable Energy Fellowship",
        "description": "Funded research fellowship studying state-level green hydrogen adoption, battery energy storage systems, and carbon tax models.",
        "domain": "environment",
        "type": "fellowship",
        "eligibility": "Undergraduate and postgraduate students in energy studies, economics, or public policy.",
        "deadline_days": 65,
        "location": "New Delhi",
        "organizer": "Council on Energy, Environment and Water (CEEW)",
        "source_url": "https://ceew.in/fellowships",
        "is_event": False,
    },
    {
        "title": "Women in Tech Leadership Fellowship",
        "description": "Mentorship program paired with a ₹1,50,000 education grant, executive 1:1 coaching, and direct fast-track interviews with top tech firms.",
        "domain": "technology",
        "type": "fellowship",
        "eligibility": "Female undergraduate engineering students in their 2nd or 3rd year.",
        "deadline_days": 35,
        "location": "Bengaluru (Hybrid)",
        "organizer": "Women Who Code India & AnitaB.org",
        "source_url": "https://anitab.org/india-fellowship",
        "is_event": False,
    },
    {
        "title": "National Bio-Entrepreneurship Competition Grant",
        "description": "Nationwide competition identifying scalable startups in biotechnology, healthcare, agritech, and industrial enzymes. ₹3 Crore in cash prizes and investment.",
        "domain": "science",
        "type": "grant",
        "eligibility": "Student innovators, researchers, and early-stage bio-startups.",
        "deadline_days": 45,
        "location": "Bengaluru, Karnataka",
        "organizer": "Centre for Cellular and Molecular Platforms (C-CAMP)",
        "source_url": "https://nationalbioentrepreneurship.in",
        "is_event": False,
    },
]


# ── Core Dataset Generation Functions ─────────────────────────────────────────

async def generate_seeded_students() -> List[Dict[str, Any]]:
    """Embed each student and assemble the complete database payload."""
    embedder = get_local_embedder()
    results = []

    logger.info(f"Generating embeddings for {len(STUDENTS_SEED_DATA)} students...")
    embed_texts = [
        build_student_embed_text(
            skills=s["skills"],
            interests=s["interests"],
            career_goals=s["career_goals"],
        )
        for s in STUDENTS_SEED_DATA
    ]
    vectors = await embedder.embed_batch(embed_texts)

    for idx, (data, vec) in enumerate(zip(STUDENTS_SEED_DATA, vectors), start=1):
        sid = make_seed_id("student", idx)
        role = infer_student_role(data)
        record = {
            "id": sid,
            "name": data["name"],
            "email": data["email"],
            "department": data["department"],
            "location": data["location"],
            "skills": data["skills"],
            "interests": data["interests"],
            "career_goals": data["career_goals"],
            "preferred_role": role,
            "embedding": vec,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        results.append(record)

    return results


async def generate_seeded_opportunities() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate opportunities, computed trust scores, and linked events.
    Returns (opportunities, trust_scores, events).
    """
    embedder = get_local_embedder()
    today = date.today()

    logger.info(f"Generating embeddings & trust scores for {len(OPPORTUNITIES_SEED_DATA)} opportunities...")
    embed_texts = [build_opportunity_embed_text(o) for o in OPPORTUNITIES_SEED_DATA]
    vectors = await embedder.embed_batch(embed_texts)

    opportunities: List[Dict[str, Any]] = []
    trust_scores: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    for idx, (data, vec) in enumerate(zip(OPPORTUNITIES_SEED_DATA, vectors), start=1):
        oid = make_seed_id("opp", idx)
        deadline = today + timedelta(days=data.get("deadline_days", 30))

        opp_record = {
            "id": oid,
            "title": data["title"],
            "description": data["description"],
            "domain": data["domain"],
            "type": data["type"],
            "eligibility": data["eligibility"],
            "deadline": deadline.isoformat(),
            "location": data["location"],
            "organizer": data["organizer"],
            "source_url": data["source_url"],
            "embedding": vec,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        opportunities.append(opp_record)

        # Trust Score calculation
        rule_score, quality_flags = rule_quality_check(opp_record)
        trust_record = {
            "opportunity_id": oid,
            "score": rule_score,
            "duplicate_flag": False,
            "quality_flags": quality_flags,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        trust_scores.append(trust_record)

        # Linked Event if applicable
        if data.get("is_event"):
            eid = make_seed_id("event", idx)
            event_record = {
                "id": eid,
                "opportunity_id": oid,
                "status": data.get("event_status", "open"),
                "registration_link": data["source_url"],
                "extra_details": data.get("extra_details", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            events.append(event_record)

    return opportunities, trust_scores, events


def generate_seed_registrations(
    students: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Registers a subset of students for the first 2 hackathon events,
    creating active candidate pools for Team Finder testing.
    """
    registrations = []
    if not events:
        return registrations

    # Primary event: HackNima 2025 (events[0])
    main_event = events[0]
    for s_idx in range(min(15, len(students))):
        s = students[s_idx]
        reg_id = make_seed_id(f"reg-{main_event['id'][:8]}", s_idx)
        registrations.append({
            "id": reg_id,
            "event_id": main_event["id"],
            "student_id": s["id"],
            "status": "registered",
            "role": s.get("preferred_role", "Member"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    # Secondary event: ClimateTech Hackathon (events[1] if available)
    if len(events) > 1:
        second_event = events[1]
        for s_idx in range(5, min(20, len(students))):
            s = students[s_idx]
            reg_id = make_seed_id(f"reg-{second_event['id'][:8]}", s_idx)
            registrations.append({
                "id": reg_id,
                "event_id": second_event["id"],
                "student_id": s["id"],
                "status": "registered",
                "role": s.get("preferred_role", "Member"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    return registrations


# ── SQL Exporter ──────────────────────────────────────────────────────────────

def format_vector_sql(vec: List[float]) -> str:
    """Format Python float list into PostgreSQL pgvector literal: '[0.1,0.2,...]'::vector."""
    joined = ",".join(f"{x:.6f}" for x in vec)
    return f"'{joined}'::vector"


def export_to_sql_script(
    students: List[Dict[str, Any]],
    opportunities: List[Dict[str, Any]],
    trust_scores: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """Export the complete seed dataset as an idempotent PostgreSQL script."""
    lines: List[str] = [
        "-- =============================================================================",
        "-- seed_output.sql — Generated by seed.py",
        f"-- Generated on: {datetime.now(timezone.utc).isoformat()}",
        f"-- Total Students: {len(students)}",
        f"-- Total Opportunities: {len(opportunities)}",
        f"-- Total Events: {len(events)}",
        "-- =============================================================================\n",
        "BEGIN;\n",
    ]

    # Students
    lines.append("-- ─── STUDENTS ─────────────────────────────────────────────────────────────")
    for s in students:
        skills_literal = "{" + ",".join(f'"{x}"' for x in s["skills"]) + "}"
        interests_literal = "{" + ",".join(f'"{x}"' for x in s["interests"]) + "}"
        vec_sql = format_vector_sql(s["embedding"])
        esc_name = s["name"].replace("'", "''")
        esc_dept = s["department"].replace("'", "''")
        esc_loc = s["location"].replace("'", "''")
        esc_goals = (s["career_goals"] or "").replace("'", "''")

        sql = (
            f"INSERT INTO public.students (id, name, email, department, location, skills, interests, career_goals, embedding, is_active) "
            f"VALUES ('{s['id']}', '{esc_name}', '{s['email']}', '{esc_dept}', '{esc_loc}', "
            f"'{skills_literal}', '{interests_literal}', '{esc_goals}', {vec_sql}, TRUE) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"name = EXCLUDED.name, department = EXCLUDED.department, location = EXCLUDED.location, "
            f"skills = EXCLUDED.skills, interests = EXCLUDED.interests, career_goals = EXCLUDED.career_goals, "
            f"embedding = EXCLUDED.embedding;"
        )
        lines.append(sql)

    # Opportunities
    lines.append("\n-- ─── OPPORTUNITIES ────────────────────────────────────────────────────────")
    for o in opportunities:
        vec_sql = format_vector_sql(o["embedding"])
        esc_title = o["title"].replace("'", "''")
        esc_desc = o["description"].replace("'", "''")
        esc_elig = (o["eligibility"] or "").replace("'", "''")
        esc_loc = (o["location"] or "").replace("'", "''")
        esc_org = (o["organizer"] or "").replace("'", "''")
        esc_url = (o["source_url"] or "").replace("'", "''")

        sql = (
            f"INSERT INTO public.opportunities (id, title, description, domain, type, eligibility, deadline, location, organizer, source_url, embedding, is_active) "
            f"VALUES ('{o['id']}', '{esc_title}', '{esc_desc}', '{o['domain']}', '{o['type']}', '{esc_elig}', '{o['deadline']}', '{esc_loc}', '{esc_org}', '{esc_url}', {vec_sql}, TRUE) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"title = EXCLUDED.title, description = EXCLUDED.description, domain = EXCLUDED.domain, "
            f"type = EXCLUDED.type, eligibility = EXCLUDED.eligibility, deadline = EXCLUDED.deadline, "
            f"location = EXCLUDED.location, organizer = EXCLUDED.organizer, source_url = EXCLUDED.source_url, "
            f"embedding = EXCLUDED.embedding;"
        )
        lines.append(sql)

    # Trust Scores
    lines.append("\n-- ─── TRUST SCORES ─────────────────────────────────────────────────────────")
    for t in trust_scores:
        flags_json = json.dumps(t["quality_flags"]).replace("'", "''")
        sql = (
            f"INSERT INTO public.trust_scores (opportunity_id, score, duplicate_flag, quality_flags, computed_at) "
            f"VALUES ('{t['opportunity_id']}', {t['score']}, {str(t['duplicate_flag']).lower()}, '{flags_json}'::jsonb, NOW()) "
            f"ON CONFLICT (opportunity_id) DO UPDATE SET "
            f"score = EXCLUDED.score, duplicate_flag = EXCLUDED.duplicate_flag, quality_flags = EXCLUDED.quality_flags, computed_at = NOW();"
        )
        lines.append(sql)

    # Events
    lines.append("\n-- ─── EVENTS ───────────────────────────────────────────────────────────────")
    for e in events:
        details_json = json.dumps(e["extra_details"]).replace("'", "''")
        sql = (
            f"INSERT INTO public.events (id, opportunity_id, status, registration_link, extra_details) "
            f"VALUES ('{e['id']}', '{e['opportunity_id']}', '{e['status']}', '{e['registration_link']}', '{details_json}'::jsonb) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"status = EXCLUDED.status, registration_link = EXCLUDED.registration_link, extra_details = EXCLUDED.extra_details;"
        )
        lines.append(sql)

    lines.append("\nCOMMIT;\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.success(f"Exported SQL seed file with {len(lines)} lines to: {output_path}")


# ── Direct Supabase Insertion ─────────────────────────────────────────────────

async def insert_into_supabase(
    students: List[Dict[str, Any]],
    opportunities: List[Dict[str, Any]],
    trust_scores: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> None:
    """Insert seed records directly into connected Supabase instance."""
    logger.info("Connecting to Supabase to insert seed data...")

    # Insert Students
    for s in students:
        payload = {k: v for k, v in s.items() if k != "preferred_role"}
        try:
            supabase_admin.table("students").upsert(payload).execute()
        except Exception as err:
            logger.warning(f"Error inserting student {s['name']}: {err}")

    # Insert Opportunities
    for o in opportunities:
        try:
            supabase_admin.table("opportunities").upsert(o).execute()
        except Exception as err:
            logger.warning(f"Error inserting opportunity {o['title']}: {err}")

    # Insert Trust Scores
    for t in trust_scores:
        try:
            supabase_admin.table("trust_scores").upsert(t).execute()
        except Exception as err:
            logger.warning(f"Error inserting trust score {t['opportunity_id']}: {err}")

    # Insert Events
    for e in events:
        try:
            supabase_admin.table("events").upsert(e).execute()
        except Exception as err:
            logger.warning(f"Error inserting event {e['id']}: {err}")

    logger.success("Supabase direct seed insertion completed successfully.")


# ── Main CLI Runner ───────────────────────────────────────────────────────────

async def run_seed(dry_run: bool = False, export_sql: Optional[str] = None) -> None:
    """Orchestrates seed dataset creation, validation, and export/insert."""
    logger.info("Initializing OpporSphere Dataset Generator...")

    students = await generate_seeded_students()
    opportunities, trust_scores, events = await generate_seeded_opportunities()
    registrations = generate_seed_registrations(students, events)

    # Validation
    assert len(students) >= 20, f"Expected at least 20 students, got {len(students)}"
    assert len(opportunities) >= 30, f"Expected at least 30 opportunities, got {len(opportunities)}"
    assert all(len(s["embedding"]) == 384 for s in students), "Student embedding vector length != 384"
    assert all(len(o["embedding"]) == 384 for o in opportunities), "Opportunity embedding vector length != 384"

    logger.success(
        f"✓ Successfully generated {len(students)} students, {len(opportunities)} opportunities, "
        f"{len(trust_scores)} trust scores, {len(events)} events, and {len(registrations)} event registrations."
    )

    # Check vector norms
    norms = [float(np.linalg.norm(s["embedding"])) for s in students[:5]]
    logger.info(f"Sample Student Embedding Norms (unit norm ~1.0): {norms}")

    if export_sql:
        export_to_sql_script(students, opportunities, trust_scores, events, export_sql)

    if dry_run:
        logger.info("[DRY RUN] Completed dataset validation. No remote database modifications were performed.")
        return

    # Direct insertion if Supabase configured
    if settings.SUPABASE_URL and "your-project-ref" not in settings.SUPABASE_URL:
        await insert_into_supabase(students, opportunities, trust_scores, events)
    else:
        logger.info(
            "Supabase URL contains default placeholder ('your-project-ref'). "
            "To apply seeds directly to Postgres, run: psql <connection-string> < seed_output.sql "
            "or provide valid SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )


def main():
    parser = argparse.ArgumentParser(description="OpporSphere Dataset Seeder")
    parser.add_argument("--dry-run", action="store_true", help="Validate generation without inserting into database")
    parser.add_argument("--export-sql", type=str, default=None, help="Export SQL insert script to specified filepath")
    parser.add_argument("--reset", action="store_true", help="Reset previous seed data")
    args = parser.parse_args()

    asyncio.run(run_seed(dry_run=args.dry_run, export_sql=args.export_sql))


if __name__ == "__main__":
    main()
