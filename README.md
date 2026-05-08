# WiSpy Project – Network Activity Monitoring and Attack Recommendation System

## Mini Project Overview

**BGU University**
**Course:** Network Security
**Date:** April 2026
---

# Project Work Plan: WiSpy

## Project Definition and Scope

The goal of this mini-project is to develop a system that simulates endpoint device attacks by collecting and monitoring user network activity through the establishment of a fake Wi‑Fi Access Point (AP).

The system is designed to monitor and analyze captured information and generate recommendations for potential future attack paths. The tool will support attacks against:

* Open wireless networks
* Secured wireless networks where the password is already known in advance

The objective is to intercept traffic from devices connected to the rogue access point.

The platform will:

* Collect network information
* Detect behavioral patterns
* Identify weaknesses that may enable user exploitation
* Present monitored information in real time
* Suggest possible next-step attacks to the operator

The project also includes a real-time monitoring interface that visualizes the collected data and provides recommendations for further actions.

---

# Operational Workflow Scenarios

The project is divided into five major phases:

## Phase A – Environment Mapping

* Scan available Wi‑Fi networks in the surrounding area
* Display technical information such as:

  * SSID (network name)
  * Encryption type
  * Additional network parameters

## Phase B – Rogue Network Deployment

* Create a fake wireless network
* Configure the rogue AP to imitate the original network
* Perform a forced disconnection (Deauthentication) against the target device
* Encourage the victim device to reconnect automatically to the fake network

## Phase C – Monitoring and Information Collection

* Monitor DNS requests in real time
* Identify connected devices using:

  * MAC addresses
  * Device type
  * Operating system
  * Hardware manufacturer/vendor

## Phase D – Information Analysis

* Extract and classify collected information
* Maintain long-term tracking and monitoring
* Identify behavioral patterns over time

## Phase E – Follow-Up Attack Recommendations

* Implement a recommendation engine
* Suggest vulnerabilities and possible attack vectors for future exploitation
* The mini-project itself will not execute the recommended attacks

---

# System Boundaries and Limitations

The project explicitly defines operational boundaries:

## Wireless Network Scope

* The system will scan nearby wireless networks
* The system will create a fake Wi‑Fi network according to collected parameters
* The system will not perform unauthorized intrusion into foreign networks
* The system will not intentionally disrupt external wireless networks beyond the simulated environment

## Traffic Monitoring Scope

* The system will monitor data from devices connected to the rogue network
* Monitoring will focus on information available in unencrypted form
* The system will not attempt to break or decrypt encrypted communication packets

## Attack Recommendation Scope

* The system may recommend possible future attacks based on collected information
* The project will not implement or execute these suggested attacks

---

# Technical Objectives

The following capabilities are planned for implementation:

## 1. Network Infrastructure

Use networking tools to:

* Scan the wireless environment
* Establish and manage the Access Point (AP)

## 2. Data Interception

Develop Python scripts using Scapy for:

* DNS request monitoring
* Traffic analysis
* Packet inspection and interpretation

## 3. Management Interface

Build a visual dashboard using:

* Flask
* JavaScript

The dashboard will:

* Display collected information visually
* Provide real-time monitoring
* Present analytical insights

## 4. Recommendation Engine

Implement analytical logic capable of:

* Identifying traffic characteristics
* Matching behaviors to known weaknesses
* Suggesting relevant attack strategies

---

# Project Timeline (Milestones)

## Phase A – April 30

* Prepare the development environment
* Install and configure Kali Linux
* Configure the wireless network adapter

## Phase B – May 10

* Launch the rogue wireless network
* Establish initial network connectivity

## Phase C – May 30

* Develop the network data analysis mechanism

## Phase D – June 5

* Develop the Flask monitoring interface
* Integrate the attack recommendation mechanism

## Phase E – June 20

* Final refinements and polishing
* Documentation
* Demo preparation

---

# Technical Challenges and Proposed Solutions

## Hardware Challenges

* Supplying a compatible wireless adapter capable of broadcasting a rogue Wi‑Fi signal from the attacking machine

## Communication Management Challenges

* Detecting nearby communication networks and their parameters
* Establishing a competing network using existing networking tools

## Information Collection and Identification Challenges

* Identifying the operating system through packet field analysis
* Understanding communication protocols and traffic structures
* Performing protocol-level traffic analysis

---

# Project Strengths

The project highlights several advantages:

* Combination of hardware and software technologies
* Exploitation of legitimate and public Wi‑Fi platforms within the attack scenario
* Extraction and analysis of information across multiple network layers
* Silent long-term information gathering with minimal traces
* Passive attack approach that avoids suspicious links or unusual user actions
* Use of social engineering techniques beginning from the fake-network lure stage and continuing through user browsing habits for future exploitation

---

# Planned Technologies

## Operating System

* Kali Linux

## Networking Tools

* Linux Wireless Tools

## Development Technologies

* Python

  * Scapy
  * Flask
* JavaScript

## Data Science

* pandas

## Intelligence and Security Frameworks

* OWASP
* MITRE ATT&CK

## Hardware

* TP-Link TL-WN722N wireless adapter

---

# Overall Project Theme

WiSpy is designed as a cybersecurity and network-security research project focused on:

* Wireless network monitoring
* Rogue access point simulation
* Passive traffic analysis
* Device fingerprinting
* Behavioral analysis
* Security intelligence gathering
* Attack path recommendation systems

The project combines:

* Wireless networking
* Traffic interception
* Real-time monitoring
* Data analytics
* Web-based visualization
* Security intelligence frameworks
* Social engineering concepts

Its primary emphasis is on understanding user behavior and network activity in order to identify weaknesses and recommend potential future attack vectors while remaining within the defined scope of passive monitoring and simulated offensive-security research.
