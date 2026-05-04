#  SmartFactory-OSI: Professional Network Simulation
> **A High-Fidelity, Professional-Grade Telecom Simulation of a 10-Node Industrial IoT Ecosystem.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)
![NetworkX](https://img.shields.io/badge/topology-networkx-orange?style=for-the-badge)
![Matplotlib](https://img.shields.io/badge/viz-matplotlib-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-red?style=for-the-badge)

---

##  Project Vision
The **SmartFactory-OSI** project is a comprehensive cross-layer simulation environment that models the intricate networking requirements of a modern automated factory. By integrating Physical, Data Link, Network, and Transport layer dynamics, this simulation provides engineers with an empirical dashboard to evaluate **QoS, Reliability, and Throughput** for mission-critical industrial applications.

---

##  System Architecture (The OSI Stack)

###  Layer 1: Physical (PHY)
*   **Modulation Schemes:** BPSK, QPSK, 16-QAM, 64-QAM.
*   **Channel Models:** AWGN & Rayleigh Fading for realistic wireless signal degradation.
*   **Capacity Modeling:** Real-time calculation of **Shannon-Hartley Capacity**.
*   **Path Loss:** Distance-based signal attenuation using the log-distance model ($n=3.0$).

###  Layer 2: Data Link (MAC)
*   **Error Control:** Advanced simulation of **Stop-and-Wait**, **Go-Back-N**, and **Selective Repeat** ARQ.
*   **Error Detection:** Implementation of **CRC-16** with random bit-flipping for reliability testing.
*   **Efficiency:** Automated calculation of protocol overhead vs. payload ($\eta$).

###  Layer 3: Network (NET)
*   **Topology:** 10-node complex graph featuring Core Switches, Edge Switches, Fog Nodes, and PLC endpoints.
*   **Addressing:** Dual-stack **IPv4 & IPv6** assignment per node.
*   **Intelligent Routing:** Dual-pass Dijkstra evaluating **Lowest-Latency** (ms) vs. **Highest-Reliability** ($1/R$).

###  Layer 4-7: Transport & Application
*   **QoS (DSCP):** Traffic prioritization using **Expedited Forwarding (EF)** for Robot Control and **Best Effort (BE)** for Telemetry.
*   **Congestion Control:** Visualization of **TCP Slow Start** and Congestion Window (`cwnd`) dynamics.
*   **Jitter Modeling:** Normal distribution variance modeling for real-time traffic stability analysis.

---

##  Mathematical Foundations
The simulation is grounded in classical Queueing Theory:
*   **M/D/1:** Deterministic service times for Robot Control.
*   **M/M/1:** Stochastic sensor telemetry modeling.
*   **M/M/2:** Multi-server high-capacity modeling for Video Surveillance streams.
*   **Performance Metrics:** $\rho$ (Utilization), $L$ (Queue Length), $W$ (Waiting Time).

---

##  Dashboard Gallery
Upon execution, the system exports five professional visualization reports:

| Report | Description |
| :--- | :--- |
| **Fig 1: Physical** | BER vs SNR, Path Loss Heatmap, and Shannon Limit. |
| **Fig 2: Data Link** | ARQ Protocol Efficiency & CRC Error Detection rates. |
| **Fig 3: Topology** | Interactive Network Graph with highlighted Dijkstra paths. |
| **Fig 4: Queueing** | Queue length PMFs and Inter-arrival/Service CDF curves. |
| **Fig 5: KPI Dashboard** | Pass/Fail assessment of Application requirements. |

---

## 👥 The Student's Team

| Profile | Information |
| :--- | :--- |
| 🛡️ **Raman Chaudhary** | **Roll No:** 22124034 |
| 🛠️ **Moksh Yadav** | **Roll No:** 22035042 |
| 📡 **Pravat Kumar Sahoo** | **Roll No:** 22085078 |

---

## 🛠 Installation & Usage

### 1. Clone & Prep
```bash
# Install the core mathematical & visualization engine
pip install numpy scipy matplotlib networkx
```

### 2. Launch Simulation
```bash
python simulation.py
```

### 3. Review Analytics
Check the **Terminal Output** for the ASCII KPI Dashboard and open the generated `.png` files for deep-dive technical analysis.

---

> *"Building the future of Industrial Connectivity, one packet at a time."*
