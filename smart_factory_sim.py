import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import networkx as nx
from math import erfc, sqrt
import time

# ==========================================
# Step 1: Applications & QoS Requirements
# ==========================================
# Applications:
# 1. Robot Control (Low Latency, High Reliability, Low Throughput)
# 2. Video Surveillance (High Throughput, Moderate Latency, Moderate Reliability)
# 3. Sensor Telemetry (Low Throughput, Moderate Latency, High Reliability)

applications = {
    'Robot_Control': {'lambda': 100, 'packet_size': 256, 'req_latency': 5, 'req_reliability': 0.999}, # pkts/s, bytes, ms
    'Video_Surveillance': {'lambda': 500, 'packet_size': 1500, 'req_latency': 50, 'req_reliability': 0.95},
    'Sensor_Telemetry': {'lambda': 50, 'packet_size': 128, 'req_latency': 100, 'req_reliability': 0.99}
}

# ==========================================
# Step 2: Packet Generation (Poisson)
# ==========================================
def generate_packets(lam, duration=1.0):
    """Generate packet inter-arrival times based on Exponential distribution (Poisson process)."""
    # Number of packets expected
    n_packets = np.random.poisson(lam * duration)
    # Inter-arrival times
    inter_arrivals = np.random.exponential(1/lam, n_packets)
    arrival_times = np.cumsum(inter_arrivals)
    # Filter arrivals within duration
    arrival_times = arrival_times[arrival_times <= duration]
    return arrival_times

# ==========================================
# Step 3: Node Addressing & Topology
# ==========================================
# 5 nodes: 0 (Gateway), 1 (Switch), 2 (Robot), 3 (Camera), 4 (Sensor)
nodes = {
    0: {'ip': '192.168.1.1', 'role': 'Gateway'},
    1: {'ip': '192.168.1.2', 'role': 'Switch'},
    2: {'ip': '192.168.1.3', 'role': 'Robot'},
    3: {'ip': '192.168.1.4', 'role': 'Camera'},
    4: {'ip': '192.168.1.5', 'role': 'Sensor'}
}

# Create a graph
G = nx.Graph()
for node_id, data in nodes.items():
    G.add_node(node_id, **data)

# Add edges with weights (representing propagation delay in ms)
edges = [
    (0, 1, 1.0), # Gateway to Switch
    (1, 2, 2.0), # Switch to Robot
    (1, 3, 5.0), # Switch to Camera
    (1, 4, 3.0)  # Switch to Sensor
]
G.add_weighted_edges_from(edges)

# ==========================================
# Step 4: Routing Protocol (Dijkstra)
# ==========================================
def find_route(src, dst):
    return nx.dijkstra_path(G, src, dst, weight='weight')

def route_delay(path):
    delay = 0
    for i in range(len(path)-1):
        delay += G[path[i]][path[i+1]]['weight']
    return delay

# ==========================================
# Step 5 & 6 & 7: Physical Layer & Data Link (ARQ + AWGN)
# ==========================================
def bpsk_ber(snr_db):
    """Compute BER for BPSK in AWGN given SNR in dB."""
    snr_linear = 10**(snr_db / 10.0)
    ber = 0.5 * erfc(sqrt(snr_linear))
    return ber

def simulate_arq(packet_size_bytes, ber):
    """Simulate Stop-and-Wait ARQ for a given packet."""
    packet_bits = packet_size_bytes * 8
    # Probability of packet error
    per = 1 - (1 - ber)**packet_bits
    
    transmissions = 1
    while np.random.rand() < per:
        transmissions += 1
    return transmissions, per

# ==========================================
# Queueing Theory Analysis (M/M/1)
# ==========================================
def analyze_mm1(lam, mu):
    """M/M/1 Queue Analysis."""
    rho = lam / mu
    if rho >= 1:
        return {'rho': rho, 'L': float('inf'), 'W': float('inf')}
    
    L = rho / (1 - rho) # Average number of packets in the system
    W = L / lam         # Average waiting time in system
    return {'rho': rho, 'L': L, 'W': W}

# Simulate queue over time
def simulate_queue(lam, mu, duration=1.0):
    arrival_times = generate_packets(lam, duration)
    service_times = np.random.exponential(1/mu, len(arrival_times))
    
    events = sorted([(t, 'A', i) for i, t in enumerate(arrival_times)])
    
    q_len = 0
    t_list = []
    q_list = []
    
    sys_time = 0
    departures = []
    
    for t, event_type, idx in events:
        # Before processing, check if any departures happened before this arrival
        while departures and departures[0] <= t:
            dep_t = departures.pop(0)
            q_len -= 1
            t_list.append(dep_t)
            q_list.append(q_len)
            sys_time = dep_t
            
        q_len += 1
        t_list.append(t)
        q_list.append(q_len)
        
        # Schedule departure
        start_service = max(sys_time, t)
        departure_time = start_service + service_times[idx]
        departures.append(departure_time)
        departures.sort()
        sys_time = start_service
        
    while departures:
        dep_t = departures.pop(0)
        q_len -= 1
        t_list.append(dep_t)
        q_list.append(q_len)
        
    return t_list, q_list

# ==========================================
# Step 8: KPI Evaluation & Simulation Run
# ==========================================
def run_simulation():
    snr_db = 10 # dB
    ber = bpsk_ber(snr_db)

    results = {}

    print("="*50)
    print("SMART FACTORY NETWORK SIMULATION - KPI REPORT")
    print("="*50)
    print(f"Physical Layer: AWGN Channel, SNR = {snr_db} dB, BER = {ber:.2e}")
    print("-" * 50)

    # Service rate (e.g., 10 Mbps link capacity)
    link_capacity_bps = 10 * 1e6 

    for app_name, req in applications.items():
        lam = req['lambda']
        pkt_size_bits = req['packet_size'] * 8
        
        # Calculate service rate mu (packets/s) for this app's packet size
        mu = link_capacity_bps / pkt_size_bits
        
        # M/M/1 Analysis
        mm1_stats = analyze_mm1(lam, mu)
        
        # ARQ Simulation
        # Simulating 1000 packets to find average retransmissions
        n_sim_pkts = 1000
        total_tx = 0
        per = 0
        for _ in range(n_sim_pkts):
            tx, current_per = simulate_arq(req['packet_size'], ber)
            total_tx += tx
            per = current_per # PER is constant given packet size and BER
        
        avg_tx = total_tx / n_sim_pkts
        packet_loss_rate = per
        
        # Network Delay (Routing)
        if app_name == 'Robot_Control': dst = 2
        elif app_name == 'Video_Surveillance': dst = 3
        else: dst = 4
        
        path = find_route(0, dst)
        prop_delay_ms = route_delay(path)
        
        # End-to-End Latency = Waiting Time + Transmission Time + Propagation Delay (x avg_tx for ARQ)
        waiting_time_ms = mm1_stats['W'] * 1000 if mm1_stats['W'] != float('inf') else float('inf')
        tx_time_ms = (pkt_size_bits / link_capacity_bps) * 1000
        
        e2e_latency = (waiting_time_ms + tx_time_ms + prop_delay_ms) * avg_tx
        
        # Throughput (successful bits per second)
        throughput_bps = lam * pkt_size_bits * (1 - per)
        
        results[app_name] = {
            'e2e_latency': e2e_latency,
            'packet_loss_rate': per,
            'throughput_bps': throughput_bps,
            'ber': ber,
            'queue_len': mm1_stats['L'],
            'utilization': mm1_stats['rho']
        }
        
        print(f"Application: {app_name}")
        print(f"  - Route: {path} (Prop Delay: {prop_delay_ms} ms)")
        print(f"  - Utilization (rho): {mm1_stats['rho']:.4f}")
        print(f"  - Avg Queue Length: {mm1_stats['L']:.4f} pkts")
        print(f"  - End-to-End Latency: {e2e_latency:.2f} ms (Req: {req['req_latency']} ms)")
        print(f"  - Packet Error Rate (PER): {per:.4e}")
        print(f"  - Throughput: {throughput_bps/1e6:.4f} Mbps")
        print("-" * 50)

    # ==========================================
    # Plots
    # ==========================================
    plt.figure(figsize=(15, 5))

    # 1. BER vs SNR
    snr_range = np.linspace(0, 12, 50)
    ber_range = [bpsk_ber(snr) for snr in snr_range]
    plt.subplot(1, 3, 1)
    plt.semilogy(snr_range, ber_range, 'b-', label='BPSK')
    plt.title("BER vs SNR (AWGN)")
    plt.xlabel("SNR (dB)")
    plt.ylabel("Bit Error Rate (BER)")
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend()

    # 2. Queue Length vs Time (Video Surveillance)
    t_list, q_list = simulate_queue(applications['Video_Surveillance']['lambda'], 
                                    link_capacity_bps / (applications['Video_Surveillance']['packet_size']*8), 
                                    duration=0.1)
    plt.subplot(1, 3, 2)
    plt.step(t_list, q_list, where='post')
    plt.title("Queue Length vs Time (Video Surv.)")
    plt.xlabel("Time (s)")
    plt.ylabel("Queue Length")
    plt.grid(True)

    # 3. KPI Comparison (Latency)
    plt.subplot(1, 3, 3)
    apps = list(results.keys())
    latencies = [results[app]['e2e_latency'] for app in apps]
    plt.bar(apps, latencies, color=['red', 'green', 'blue'])
    plt.title("End-to-End Latency Comparison")
    plt.ylabel("Latency (ms)")
    plt.xticks(rotation=15)

    plt.tight_layout()
    plt.savefig('simulation_plots.png')
    print("Plots saved to 'simulation_plots.png'")

if __name__ == '__main__':
    run_simulation()
