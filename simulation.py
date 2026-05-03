"""
Professional Smart Factory Network Simulation
Overhauled to include physical, data link, network, transport, and queueing layers.
"""

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import networkx as nx
import math
import random
import collections

# ==========================================
# CONFIGURATION
# ==========================================
# Configure dark theme for all plots
plt.style.use('dark_background')

LINK_CAPACITY_BPS = 10e6 # 10 Mbps
BANDWIDTH_HZ = 10e6      # 10 MHz

APPS = {
    'Robot_Control': {'lam': 100, 'size': 256, 'req_latency': 5.0, 'req_reliability': 0.999, 'req_tput': 0.1, 'req_jitter': 2.0, 'class': 'EF'},
    'Video_Surveillance': {'lam': 500, 'size': 1500, 'req_latency': 50.0, 'req_reliability': 0.95, 'req_tput': 5.0, 'req_jitter': 10.0, 'class': 'AF41'},
    'Sensor_Telemetry': {'lam': 50, 'size': 128, 'req_latency': 100.0, 'req_reliability': 0.99, 'req_tput': 0.01, 'req_jitter': 20.0, 'class': 'BE'}
}

# ==========================================
# SECTION 1: PHYSICAL LAYER
# ==========================================
def qfunc(x):
    """Q-function using standard math library."""
    return 0.5 * math.erfc(x / math.sqrt(2))

def ber_bpsk(snr_linear):
    """BER for BPSK in AWGN."""
    return qfunc(math.sqrt(2 * snr_linear))

def ber_qpsk(snr_linear):
    """BER for QPSK in AWGN."""
    return qfunc(math.sqrt(2 * snr_linear))

def ber_16qam(snr_linear):
    """Approximated BER for 16-QAM in AWGN."""
    P_sqrt = 2 * (1 - 1/math.sqrt(16)) * qfunc(math.sqrt(3 * snr_linear / 15))
    P_M = 1 - (1 - P_sqrt)**2
    return P_M / 4

def ber_64qam(snr_linear):
    """Approximated BER for 64-QAM in AWGN."""
    P_sqrt = 2 * (1 - 1/math.sqrt(64)) * qfunc(math.sqrt(3 * snr_linear / 63))
    P_M = 1 - (1 - P_sqrt)**2
    return P_M / 6

def ber_rayleigh_bpsk(snr_linear):
    """BER for BPSK in Rayleigh fading channel."""
    return 0.5 * (1 - math.sqrt(snr_linear / (1 + snr_linear)))

def shannon_capacity(snr_linear, bandwidth):
    """Shannon channel capacity (bps)."""
    return bandwidth * math.log2(1 + snr_linear)

def path_loss_log_distance(d, d0=1.0, pl_d0=40.0, n=3.0):
    """Log-distance path loss model."""
    if d < d0: d = d0
    return pl_d0 + 10 * n * math.log10(d / d0)

# ==========================================
# SECTION 2: DATA LINK LAYER
# ==========================================
def arq_efficiencies(a, pf):
    """Throughput efficiency of ARQ protocols."""
    eff_sw = (1 - pf) / (1 + 2 * a)
    eff_gbn4 = (1 - pf) / (1 + 4 * pf)
    eff_gbn8 = (1 - pf) / (1 + 8 * pf)
    eff_sr = 1 - pf
    return eff_sw, eff_gbn4, eff_gbn8, eff_sr

def simulate_crc16(ber, num_frames=10000, frame_size_bytes=100):
    """Simulate CRC-16 Error Detection."""
    total_errors = 0
    undetected = 0
    detected = 0
    for _ in range(num_frames):
        per = 1 - (1 - ber)**(frame_size_bytes * 8)
        if random.random() < per:
            total_errors += 1
            if random.random() < (1.0 / 65536.0):
                undetected += 1
            else:
                detected += 1
    return total_errors, detected, undetected

def frame_efficiency(payload_bytes, header_bytes=40):
    """Calculate protocol frame efficiency."""
    return payload_bytes / (payload_bytes + header_bytes)

# ==========================================
# SECTION 3: NETWORK LAYER
# ==========================================
def build_topology():
    """Build factory network topology (10 nodes) and assign addressing."""
    G = nx.Graph()
    nodes = {
        0: {'role': 'Gateway', 'ip4': '192.168.1.1', 'ip6': 'fe80::1', 'pos': (0, 2)},
        1: {'role': 'Core_Switch', 'ip4': '192.168.1.2', 'ip6': 'fe80::2', 'pos': (1, 2)},
        2: {'role': 'Edge_Switch_1', 'ip4': '192.168.1.3', 'ip6': 'fe80::3', 'pos': (2, 3)},
        3: {'role': 'Edge_Switch_2', 'ip4': '192.168.1.4', 'ip6': 'fe80::4', 'pos': (2, 1)},
        4: {'role': 'Fog_Compute', 'ip4': '192.168.1.5', 'ip6': 'fe80::5', 'pos': (1, 3)},
        5: {'role': 'Wireless_AP', 'ip4': '192.168.1.6', 'ip6': 'fe80::6', 'pos': (3, 3)},
        6: {'role': 'PLC_Node', 'ip4': '192.168.1.7', 'ip6': 'fe80::7', 'pos': (3, 2)},
        7: {'role': 'Robot', 'ip4': '192.168.1.8', 'ip6': 'fe80::8', 'pos': (4, 3)},
        8: {'role': 'Camera', 'ip4': '192.168.1.9', 'ip6': 'fe80::9', 'pos': (4, 1)},
        9: {'role': 'Sensor', 'ip4': '192.168.1.10', 'ip6': 'fe80::10', 'pos': (4, 2)}
    }
    for n, d in nodes.items():
        G.add_node(n, **d)
        
    edges = [
        (0, 1, 1.0, 0.999, 0.2), (1, 2, 0.5, 0.999, 0.3), (1, 3, 0.5, 0.999, 0.2),
        (1, 4, 0.2, 0.9999, 0.1), (2, 5, 1.0, 0.99, 0.4), (2, 6, 0.5, 0.999, 0.1),
        (3, 8, 2.0, 0.99, 0.5), (5, 7, 3.0, 0.98, 0.2), (6, 9, 1.5, 0.99, 0.1),
        (3, 6, 1.0, 0.99, 0.2)
    ]
    for u, v, delay, rel, load in edges:
        inv_rel = 1.0 / rel if rel > 0 else float('inf')
        ospf_cost = delay * (1 + load)
        G.add_edge(u, v, delay=delay, rel=rel, load=load, inv_rel=inv_rel, ospf_cost=ospf_cost)
    return G

# ==========================================
# SECTION 4: TRANSPORT & APP LAYER
# ==========================================
def tcp_congestion_window(rtts=20):
    """Simulate TCP Slow Start and Congestion Avoidance."""
    cwnd = 1
    ssthresh = 16
    cwnds = []
    for _ in range(rtts):
        cwnds.append(cwnd)
        if cwnd < ssthresh:
            cwnd *= 2
        else:
            cwnd += 1
    return cwnds

class PriorityQueueSim:
    """Discrete-event simulation of DSCP/QoS Priority Queueing."""
    def __init__(self, capacity_bps):
        self.capacity = capacity_bps
        self.queues = {'EF': collections.deque(), 'AF41': collections.deque(), 'BE': collections.deque()}
        self.time = 0.0
        self.server_busy_until = 0.0
        self.waiting_times = {'EF': [], 'AF41': [], 'BE': []}
        
    def add_packet(self, arr_time, pkt_class, size_bits):
        self.queues[pkt_class].append((arr_time, size_bits))
        
    def process_all(self, events):
        events.sort(key=lambda x: x[0])
        idx = 0
        while idx < len(events) or any(self.queues.values()):
            if not any(self.queues.values()):
                self.time = max(self.time, events[idx][0])
                
            while idx < len(events) and events[idx][0] <= self.time:
                self.add_packet(*events[idx])
                idx += 1
                
            if self.time >= self.server_busy_until:
                served = False
                for q_class in ['EF', 'AF41', 'BE']:
                    if self.queues[q_class]:
                        arr_time, size = self.queues[q_class].popleft()
                        wait = self.time - arr_time
                        self.waiting_times[q_class].append(wait)
                        tx_time = size / self.capacity
                        self.server_busy_until = self.time + tx_time
                        self.time = self.server_busy_until
                        served = True
                        break
                if not served and idx < len(events):
                    self.time = events[idx][0]

# ==========================================
# SECTION 5: QUEUEING THEORY
# ==========================================
def theoretical_queues(apps, capacity_bps):
    """Compute queueing theory metrics for M/M/1, M/D/1, M/M/c models."""
    results = {}
    
    # 1. Robot: M/D/1
    lam = apps['Robot_Control']['lam']
    mu = capacity_bps / (apps['Robot_Control']['size'] * 8)
    rho = lam / mu
    Lq = (rho**2) / (2 * (1 - rho)) if rho < 1 else float('inf')
    Wq = Lq / lam if lam > 0 else 0
    W = Wq + 1/mu
    L = lam * W
    results['M/D/1 (Robot)'] = {'rho': rho, 'L': L, 'Lq': Lq, 'W': W*1000, 'Wq': Wq*1000}
    
    # 2. Video: M/M/2
    lam = apps['Video_Surveillance']['lam']
    mu = (capacity_bps/2) / (apps['Video_Surveillance']['size'] * 8)
    c = 2
    rho_sys = lam / (c * mu)
    if rho_sys < 1:
        P0 = 1.0 / (1 + (2*rho_sys) + ((2*rho_sys)**2 / (2*(1-rho_sys))))
        Lq = P0 * ((2*rho_sys)**2 * rho_sys) / (2 * (1-rho_sys)**2)
        L = Lq + 2*rho_sys
        W = L / lam
        Wq = Lq / lam
    else:
        Lq, L, W, Wq = float('inf'), float('inf'), float('inf'), float('inf')
    results['M/M/2 (Video)'] = {'rho': rho_sys, 'L': L, 'Lq': Lq, 'W': W*1000, 'Wq': Wq*1000}
    
    # 3. Sensor: M/M/1
    lam = apps['Sensor_Telemetry']['lam']
    mu = capacity_bps / (apps['Sensor_Telemetry']['size'] * 8)
    rho = lam / mu
    L = rho / (1 - rho) if rho < 1 else float('inf')
    W = L / lam if lam > 0 else 0
    Wq = W - 1/mu if rho < 1 else float('inf')
    Lq = lam * Wq
    results['M/M/1 (Sensor)'] = {'rho': rho, 'L': L, 'Lq': Lq, 'W': W*1000, 'Wq': Wq*1000}
    
    return results

def simulate_queue_pmf(lam, mu, qtype='MM1', max_t=50):
    """Simulate a queue and return its empirical length probability mass function."""
    t, q_len = 0, 0
    time_in_state = collections.defaultdict(float)
    next_arr = random.expovariate(lam)
    deps = []
    
    while t < max_t:
        min_dep = min(deps) if deps else float('inf')
        if next_arr < min_dep:
            dt = next_arr - t
            time_in_state[q_len] += dt
            t = next_arr
            q_len += 1
            next_arr = t + random.expovariate(lam)
            
            if qtype == 'MM1' and len(deps) < 1:
                deps.append(t + random.expovariate(mu))
            elif qtype == 'MD1' and len(deps) < 1:
                deps.append(t + 1.0/mu)
            elif qtype == 'MM2' and len(deps) < 2:
                deps.append(t + random.expovariate(mu))
        else:
            dt = min_dep - t
            time_in_state[q_len] += dt
            t = min_dep
            q_len -= 1
            deps.remove(min_dep)
            
            if q_len >= (1 if qtype != 'MM2' else 2):
                if qtype == 'MD1':
                    deps.append(t + 1.0/mu)
                else:
                    deps.append(t + random.expovariate(mu))
                    
    total = sum(time_in_state.values())
    max_k = min(20, max(time_in_state.keys()))
    return [time_in_state.get(k, 0) / total for k in range(max_k + 1)]

def simulate_queue_length_trace(lam, mu, duration=1.0):
    """Simulate M/M/1 queue over time for step plotting."""
    t, q_len = 0, 0
    trace = [(0.0, 0)]
    next_arr = random.expovariate(lam)
    next_dep = float('inf')
    
    while t < duration:
        if next_arr < next_dep:
            t = next_arr
            q_len += 1
            trace.append((t, q_len))
            next_arr = t + random.expovariate(lam)
            if q_len == 1:
                next_dep = t + random.expovariate(mu)
        else:
            t = next_dep
            q_len -= 1
            trace.append((t, q_len))
            if q_len > 0:
                next_dep = t + random.expovariate(mu)
            else:
                next_dep = float('inf')
    return trace

# ==========================================
# SECTION 6: VISUALIZATION
# ==========================================
def generate_plots(kpis, G):
    print("\nGenerating Professional Visualizations...")
    
    # ------------------------------------------
    # Fig 1: Physical Layer
    # ------------------------------------------
    fig1, axs = plt.subplots(1, 3, figsize=(18, 5))
    snr_db = np.linspace(0, 20, 100)
    snr_lin = 10**(snr_db/10)
    
    axs[0].semilogy(snr_db, [ber_bpsk(s) for s in snr_lin], label='BPSK (AWGN)')
    axs[0].semilogy(snr_db, [ber_qpsk(s) for s in snr_lin], '--', label='QPSK (AWGN)')
    axs[0].semilogy(snr_db, [ber_16qam(s) for s in snr_lin], label='16-QAM (AWGN)')
    axs[0].semilogy(snr_db, [ber_64qam(s) for s in snr_lin], label='64-QAM (AWGN)')
    axs[0].semilogy(snr_db, [ber_rayleigh_bpsk(s) for s in snr_lin], label='BPSK (Rayleigh)')
    axs[0].set(title='BER vs SNR Comparison', xlabel='SNR (dB)', ylabel='Bit Error Rate', ylim=[1e-6, 0.5])
    axs[0].grid(True, alpha=0.3); axs[0].legend()
    
    d_range = np.linspace(1, 100, 50)
    pl = [path_loss_log_distance(d) for d in d_range]
    rx_snr = [20 - p - (-100) for p in pl]
    axs[1].plot(d_range, pl, color='cyan', label='Path Loss (dB)')
    axs[1].set(xlabel='Distance (m)', ylabel='Path Loss (dB)')
    axs[1].yaxis.label.set_color('cyan')
    ax1_twin = axs[1].twinx()
    ax1_twin.plot(d_range, rx_snr, color='magenta', label='Received SNR (dB)')
    ax1_twin.set_ylabel('Received SNR (dB)', color='magenta')
    axs[1].set_title('Path Loss & Received SNR vs Distance')
    
    axs[2].plot(snr_db, [shannon_capacity(s, BANDWIDTH_HZ)/1e6 for s in snr_lin], color='yellow')
    axs[2].set(title='Shannon Channel Capacity', xlabel='SNR (dB)', ylabel='Capacity (Mbps)')
    axs[2].grid(True, alpha=0.3)
    fig1.tight_layout(); fig1.savefig('Fig1_Physical.png'); plt.close(fig1)

    # ------------------------------------------
    # Fig 2: Data Link Layer
    # ------------------------------------------
    fig2, axs = plt.subplots(1, 3, figsize=(18, 5))
    pf_range = np.linspace(0, 0.5, 50)
    effs = [arq_efficiencies(0.1, pf) for pf in pf_range]
    axs[0].plot(pf_range, [e[0] for e in effs], label='Stop-and-Wait')
    axs[0].plot(pf_range, [e[1] for e in effs], label='Go-Back-N (N=4)')
    axs[0].plot(pf_range, [e[2] for e in effs], label='Go-Back-N (N=8)')
    axs[0].plot(pf_range, [e[3] for e in effs], label='Selective Repeat')
    axs[0].set(title='ARQ Throughput Efficiency vs Error Rate', xlabel='Frame Error Rate (Pf)', ylabel='Efficiency (\eta)')
    axs[0].grid(True, alpha=0.3); axs[0].legend()
    
    apps = list(APPS.keys())
    axs[1].bar(apps, [frame_efficiency(APPS[a]['size']) for a in apps], color=['red', 'green', 'blue'])
    axs[1].set(title='Protocol Frame Efficiency', ylabel='Efficiency')
    axs[1].set_xticklabels([a.replace('_', ' ') for a in apps], rotation=15)
    
    tot_err, det, undet = simulate_crc16(ber_bpsk(10**(10/10))) # 10dB BPSK
    axs[2].bar(['Total Errors', 'Detected', 'Undetected'], [tot_err, det, undet], color=['orange', 'lime', 'red'])
    axs[2].set(title='CRC-16 Error Detection (10k Frames)', yscale='log', ylabel='Frames')
    fig2.tight_layout(); fig2.savefig('Fig2_DataLink.png'); plt.close(fig2)

    # ------------------------------------------
    # Fig 3: Network Topology
    # ------------------------------------------
    fig3, axs = plt.subplots(2, 2, figsize=(14, 12))
    pos = nx.get_node_attributes(G, 'pos')
    roles = nx.get_node_attributes(G, 'role')
    color_map = {'Gateway': 'red', 'Core_Switch': 'blue', 'Edge_Switch_1': 'blue', 'Edge_Switch_2': 'blue', 
                 'Wireless_AP': 'blue', 'Fog_Compute': 'purple', 'PLC_Node': 'green', 'Robot': 'green',
                 'Camera': 'green', 'Sensor': 'green'}
    node_colors = [color_map[roles[n]] for n in G.nodes()]
    
    nx.draw(G, pos, ax=axs[0,0], with_labels=True, node_color=node_colors, node_size=600, font_color='white')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): f"{d['delay']}ms" for u, v, d in G.edges(data=True)}, ax=axs[0,0])
    axs[0,0].set_title('Full Smart Factory Network Topology')
    
    paths = {
        'Robot (Lowest Latency)': nx.dijkstra_path(G, 7, 0, weight='delay'),
        'Video (Lowest Latency)': nx.dijkstra_path(G, 8, 0, weight='delay'),
        'Sensor (Highest Reliability)': nx.dijkstra_path(G, 9, 0, weight='inv_rel')
    }
    
    axes = [axs[0,1], axs[1,0], axs[1,1]]
    for idx, (title, path) in enumerate(paths.items()):
        ax = axes[idx]
        nx.draw(G, pos, ax=ax, with_labels=True, node_color='gray', node_size=400, alpha=0.5)
        nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=path, node_color='red', node_size=500)
        nx.draw_networkx_edges(G, pos, ax=ax, edgelist=list(zip(path, path[1:])), edge_color='red', width=3.0)
        ax.set_title(f'Routing Path: {title}')
        
    fig3.tight_layout(); fig3.savefig('Fig3_Network.png'); plt.close(fig3)

    # ------------------------------------------
    # Fig 4: Queueing Theory
    # ------------------------------------------
    fig4, axs = plt.subplots(2, 2, figsize=(14, 10))
    pmf_mm1 = simulate_queue_pmf(50, 100, 'MM1', max_t=200)
    pmf_md1 = simulate_queue_pmf(50, 100, 'MD1', max_t=200)
    pmf_mm2 = simulate_queue_pmf(50, 50, 'MM2', max_t=200) # 2 servers
    
    max_len = max(len(pmf_mm1), len(pmf_md1), len(pmf_mm2))
    pmf_mm1 += [0] * (max_len - len(pmf_mm1))
    pmf_md1 += [0] * (max_len - len(pmf_md1))
    pmf_mm2 += [0] * (max_len - len(pmf_mm2))
    
    x = np.arange(max_len)
    axs[0,0].bar(x - 0.25, pmf_mm1, 0.25, label='M/M/1')
    axs[0,0].bar(x, pmf_md1, 0.25, label='M/D/1')
    axs[0,0].bar(x + 0.25, pmf_mm2, 0.25, label='M/M/2')
    axs[0,0].set(title='Queue Length Distributions', xlabel='Queue Length (packets)', ylabel='Probability')
    axs[0,0].legend()
    
    t_vals = np.linspace(0, 0.05, 100)
    A_t = 1 - np.exp(-50 * t_vals)
    B_t = 1 - np.exp(-100 * t_vals)
    axs[0,1].plot(t_vals, A_t, label='A(t) Arrivals')
    axs[0,1].plot(t_vals, B_t, label='B(t) Service')
    axs[0,1].fill_between(t_vals, A_t, B_t, color='white', alpha=0.1, label='Traffic Intensity Region')
    axs[0,1].set(title='Inter-arrival & Service Time CDFs', xlabel='Time (s)', ylabel='Probability')
    axs[0,1].legend()
    
    axs[1,0].plot(range(1, 21), tcp_congestion_window(20), marker='o', color='orange')
    axs[1,0].set(title='TCP Congestion Window vs Time', xlabel='RTTs', ylabel='cwnd (MSS)')
    axs[1,0].grid(True, alpha=0.3)
    
    events = simulate_queue_length_trace(50, 100, duration=5.0)
    axs[1,1].step([e[0] for e in events], [e[1] for e in events], where='post', color='cyan')
    axs[1,1].set(title='Queue Length vs Time (Sample Trace)', xlabel='Time (s)', ylabel='Queue Length')
    
    fig4.tight_layout(); fig4.savefig('Fig4_Queueing.png'); plt.close(fig4)

    # ------------------------------------------
    # Fig 5: KPI Dashboard
    # ------------------------------------------
    fig5, axs = plt.subplots(2, 2, figsize=(14, 10))
    apps_disp = ['Robot Control', 'Video Surv.', 'Sensor Telem.']
    metrics = ['Latency', 'Throughput', 'Packet Loss', 'Jitter']
    ylabels = ['Latency (ms)', 'Throughput (Mbps)', 'Loss Rate', 'Peak Jitter (ms)']
    
    for i, metric in enumerate(metrics):
        ax = axs[i//2, i%2]
        vals, reqs, colors = [], [], []
        for app in APPS.keys():
            sim_val, req_val = kpis[app][metric]
            vals.append(sim_val); reqs.append(req_val)
            if metric == 'Throughput': colors.append('lime' if sim_val >= req_val else 'red')
            else: colors.append('lime' if sim_val <= req_val else 'red')
                
        ax.bar(apps_disp, vals, color=colors)
        for j, req in enumerate(reqs):
            ax.hlines(y=req, xmin=j-0.4, xmax=j+0.4, color='white', linestyle='--', lw=2, label='Requirement' if j==0 else "")
            
        ax.set(title=f'{metric} KPI Analysis', ylabel=ylabels[i])
        if i == 0: ax.legend()
        
    fig5.tight_layout(); fig5.savefig('Fig5_KPIDashboard.png'); plt.close(fig5)
    print("-> 5 High-Quality Visualizations generated and saved.")


# ==========================================
# SECTION 7: SIMULATION ORCHESTRATION
# ==========================================
def run_simulation():
    print("\n" + "="*80)
    print("SMART FACTORY NETWORK SIMULATION - EXECUTIVE OVERHAUL")
    print("="*80)
    
    G = build_topology()
    
    print("\n" + "-"*80)
    print("NETWORK ROUTING PATH SELECTION")
    print("-" * 80)
    costs, paths = {}, {}
    for app_name, dst, desc in [('Robot_Control', 7, 'Lowest Latency'), 
                                ('Video_Surveillance', 8, 'Lowest Latency'), 
                                ('Sensor_Telemetry', 9, 'Highest Reliability')]:
        lat_path = nx.dijkstra_path(G, dst, 0, weight='delay')
        rel_path = nx.dijkstra_path(G, dst, 0, weight='inv_rel')
        
        print(f"Application: {app_name.replace('_', ' ')}")
        print(f"  - Option 1 (Latency): {lat_path} (Cost: {nx.dijkstra_path_length(G, dst, 0, weight='delay'):.2f} ms)")
        print(f"  - Option 2 (Reliab): {rel_path} (Cost: {nx.dijkstra_path_length(G, dst, 0, weight='inv_rel'):.4f})")
        
        if desc == 'Lowest Latency':
            paths[app_name], costs[app_name] = lat_path, nx.dijkstra_path_length(G, dst, 0, weight='delay')
            print(f"  -> Selected Option 1 ({desc})\n")
        else:
            paths[app_name], costs[app_name] = rel_path, nx.dijkstra_path_length(G, dst, 0, weight='inv_rel')
            print(f"  -> Selected Option 2 ({desc})\n")

    # Priority Queue QoS Simulation
    pq = PriorityQueueSim(LINK_CAPACITY_BPS)
    events = []
    for app, data in APPS.items():
        n_pkts = np.random.poisson(data['lam'] * 10)
        arrivals = np.cumsum(np.random.exponential(1.0/data['lam'], n_pkts))
        for a in arrivals:
            if a <= 10.0: events.append((a, data['class'], data['size'] * 8))
    pq.process_all(events)
    
    # Compile KPIs
    kpis = {}
    ber = ber_bpsk(10**(10/10)) # SNR = 10dB
    
    for app, req in APPS.items():
        # Latency = Avg QoS Waiting Time + Transmission Time + Propagation Delay
        avg_wq = np.mean(pq.waiting_times[req['class']]) * 1000 if pq.waiting_times[req['class']] else 0
        tx_ms = (req['size'] * 8 / LINK_CAPACITY_BPS) * 1000
        prop_ms = costs[app] if 'Latency' in paths[app] else nx.dijkstra_path_length(G, paths[app][0], paths[app][-1], weight='delay')
        latency = avg_wq + tx_ms + prop_ms
        
        # Loss Rate
        loss = 1 - ((1 - ber)**(req['size']*8))
        
        # Throughput
        tput = req['lam'] * req['size'] * 8 * (1 - loss) / 1e6
        
        # Jitter Modeling (Standard Deviation of wait times scaled)
        std_wait = np.std(pq.waiting_times[req['class']]) * 1000 if pq.waiting_times[req['class']] else 1.0
        peak_jitter = 3 * std_wait
        
        kpis[app] = {
            'Latency': (latency, req['req_latency']),
            'Throughput': (tput, req['req_tput']),
            'Packet Loss': (loss, 1 - req['req_reliability']),
            'Jitter': (peak_jitter, req['req_jitter'])
        }

    # Print Queueing Theory Summaries
    print("-" * 80)
    print("QUEUEING THEORY SUMMARY")
    print("-" * 80)
    print(f"{'Model (App)':<20} | {'Rho':<8} | {'L (pkts)':<10} | {'Lq (pkts)':<10} | {'W (ms)':<8} | {'Wq (ms)':<8}")
    print("-" * 80)
    q_stats = theoretical_queues(APPS, LINK_CAPACITY_BPS)
    for model, stats in q_stats.items():
        print(f"{model:<20} | {stats['rho']:<8.4f} | {stats['L']:<10.4f} | {stats['Lq']:<10.4f} | {stats['W']:<8.2f} | {stats['Wq']:<8.2f}")

    # Print KPI Dashboard
    print("\n" + "-" * 80)
    print("KPI DASHBOARD (ASCII REPORT)")
    print("-" * 80)
    print(f"{'Application':<20} | {'Metric':<15} | {'Requirement':<15} | {'Simulated':<12} | {'Status':<6}")
    print("-" * 80)
    
    passed_kpis = 0
    total_kpis = 0
    for app, metrics in kpis.items():
        for metric, (sim_val, req_val) in metrics.items():
            total_kpis += 1
            if metric == 'Throughput':
                passed = sim_val >= req_val
                req_str = f">= {req_val:.2f}"
            else:
                passed = sim_val <= req_val
                req_str = f"<= {req_val:.4f}"
                
            status = "PASS" if passed else "FAIL"
            if passed: passed_kpis += 1
            print(f"{app.replace('_', ' '):<20} | {metric:<15} | {req_str:<15} | {sim_val:<12.4f} | {status:<6}")

    # Health Score
    health = (passed_kpis / total_kpis) * 100
    print("\n" + "=" * 80)
    print(f"OVERALL NETWORK HEALTH SCORE: {health:.1f} / 100")
    print("=" * 80)

    # Plot Generation
    generate_plots(kpis, G)

if __name__ == '__main__':
    run_simulation()
