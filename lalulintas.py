import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import time
import pandas as pd
from datetime import datetime
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Pengendali Lampu Lalu Lintas Cerdas",
    page_icon="🚦",
    layout="wide"
)

# CSS Custom
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1e40af;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .green-light {
        background-color: #10b981;
        color: white;
    }
    .yellow-light {
        background-color: #f59e0b;
        color: white;
    }
    .red-light {
        background-color: #ef4444;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi session state
if 'phase' not in st.session_state:
    st.session_state.phase = 0
if 'time_in_phase' not in st.session_state:
    st.session_state.time_in_phase = 0
if 'running' not in st.session_state:
    st.session_state.running = False
if 'history' not in st.session_state:
    st.session_state.history = []
if 'manual_mode' not in st.session_state:
    st.session_state.manual_mode = False

# Definisi FSA dan Graf
class TrafficLightFSA:
    def __init__(self):
        # State (Q)
        self.states = ['S0_NS_Green', 'S1_NS_Yellow', 'S2_EW_Green', 'S3_EW_Yellow']
        
        self.alphabet = ['timer_30s', 'timer_5s']
        
        self.transitions = {
            'S0_NS_Green': {'timer_30s': 'S1_NS_Yellow'},
            'S1_NS_Yellow': {'timer_5s': 'S2_EW_Green'},
            'S2_EW_Green': {'timer_30s': 'S3_EW_Yellow'},
            'S3_EW_Yellow': {'timer_5s': 'S0_NS_Green'}
        }
        
        self.start_state = 'S0_NS_Green'
        
        # Accept states (F) - all states are accepting
        self.accept_states = self.states
        
        # Current state
        self.current_state = self.start_state
        
        # Phase configurations
        self.phase_config = {
            'S0_NS_Green': {
                'name': 'Fase 1: Utara-Selatan HIJAU',
                'north': 'GREEN', 'south': 'GREEN',
                'east': 'RED', 'west': 'RED',
                'duration': 30
            },
            'S1_NS_Yellow': {
                'name': 'Transisi 1: Utara-Selatan KUNING',
                'north': 'YELLOW', 'south': 'YELLOW',
                'east': 'RED', 'west': 'RED',
                'duration': 5
            },
            'S2_EW_Green': {
                'name': 'Fase 2: Timur-Barat HIJAU',
                'north': 'RED', 'south': 'RED',
                'east': 'GREEN', 'west': 'GREEN',
                'duration': 30
            },
            'S3_EW_Yellow': {
                'name': 'Transisi 2: Timur-Barat KUNING',
                'north': 'RED', 'south': 'RED',
                'east': 'YELLOW', 'west': 'YELLOW',
                'duration': 5
            }
        }
    
    def get_current_config(self):
        return self.phase_config[self.current_state]
    
    def transition(self):
        config = self.get_current_config()
        if config['duration'] == 30:
            event = 'timer_30s'
        else:
            event = 'timer_5s'
        
        self.current_state = self.transitions[self.current_state][event]
        return self.current_state

# Fungsi untuk membuat graf persimpangan
def create_intersection_graph():
    G = nx.Graph()
    
    # Nodes: persimpangan dan arah
    nodes = {
        'Center': (0, 0),
        'North': (0, 2),
        'South': (0, -2),
        'East': (2, 0),
        'West': (-2, 0)
    }
    
    for node, pos in nodes.items():
        G.add_node(node, pos=pos)
    
    # Edges: jalan yang menghubungkan
    edges = [
        ('Center', 'North', 2),
        ('Center', 'South', 2),
        ('Center', 'East', 2),
        ('Center', 'West', 2)
    ]
    
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    
    return G

# Fungsi untuk menggambar graf persimpangan
def draw_intersection_graph(fsa):
    fig, ax = plt.subplots(figsize=(8, 8))
    G = create_intersection_graph()
    pos = nx.get_node_attributes(G, 'pos')
    
    config = fsa.get_current_config()
    
    # Warna node berdasarkan status lampu
    node_colors = {
        'Center': '#4b5563',
        'North': '#ef4444' if config['north'] == 'RED' else '#f59e0b' if config['north'] == 'YELLOW' else '#10b981',
        'South': '#ef4444' if config['south'] == 'RED' else '#f59e0b' if config['south'] == 'YELLOW' else '#10b981',
        'East': '#ef4444' if config['east'] == 'RED' else '#f59e0b' if config['east'] == 'YELLOW' else '#10b981',
        'West': '#ef4444' if config['west'] == 'RED' else '#f59e0b' if config['west'] == 'YELLOW' else '#10b981'
    }
    
    # Gambar edges
    nx.draw_networkx_edges(G, pos, width=8, alpha=0.6, edge_color='#6b7280', ax=ax)
    
    # Gambar nodes
    for node in G.nodes():
        x, y = pos[node]
        circle = Circle((x, y), 0.3, color=node_colors[node], ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, node, ha='center', va='center', fontsize=10, 
                fontweight='bold', color='white', zorder=4)
    
    # Label edges (jarak)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=10, ax=ax)
    
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.axis('off')
    ax.set_aspect('equal')
    
    plt.title('Graf Persimpangan Jalan\n(Teori Graf - Weighted Graph)', 
              fontsize=14, fontweight='bold', pad=20)
    
    return fig

# Fungsi untuk menggambar FSA diagram
def draw_fsa_diagram(fsa):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Posisi states dalam lingkaran
    positions = {
        'S0_NS_Green': (0, 2),
        'S1_NS_Yellow': (2, 0),
        'S2_EW_Green': (0, -2),
        'S3_EW_Yellow': (-2, 0)
    }
    
    # Gambar states
    for state, (x, y) in positions.items():
        # Highlight current state
        if state == fsa.current_state:
            color = '#3b82f6'
            linewidth = 4
        else:
            color = '#e5e7eb'
            linewidth = 2
        
        circle = Circle((x, y), 0.5, color=color, ec='black', linewidth=linewidth, zorder=2)
        ax.add_patch(circle)
        
        # Label state
        state_label = state.replace('_', '\n')
        ax.text(x, y, state_label, ha='center', va='center', 
                fontsize=9, fontweight='bold', zorder=3)
    
    # Gambar transisi
    transitions_visual = [
        ('S0_NS_Green', 'S1_NS_Yellow', '30s', (1, 1)),
        ('S1_NS_Yellow', 'S2_EW_Green', '5s', (1, -1)),
        ('S2_EW_Green', 'S3_EW_Yellow', '30s', (-1, -1)),
        ('S3_EW_Yellow', 'S0_NS_Green', '5s', (-1, 1))
    ]
    
    for start, end, label, offset in transitions_visual:
        x1, y1 = positions[start]
        x2, y2 = positions[end]
        
        # Arrow dengan curve
        arrow = FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle='->', mutation_scale=30, linewidth=2,
            color='#6b7280', connectionstyle="arc3,rad=0.3", zorder=1
        )
        ax.add_patch(arrow)
        
        # Label transisi
        mid_x, mid_y = (x1 + x2) / 2 + offset[0] * 0.3, (y1 + y2) / 2 + offset[1] * 0.3
        ax.text(mid_x, mid_y, label, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray'),
                fontsize=10, fontweight='bold')
    
    # Tanda start state
    ax.annotate('', xy=(0, 2), xytext=(-0.5, 2.5),
                arrowprops=dict(arrowstyle='->', lw=2, color='green'))
    ax.text(-0.8, 2.5, 'Start', fontsize=10, fontweight='bold', color='green')
    
    ax.set_xlim(-4, 3)
    ax.set_ylim(-3, 3)
    ax.axis('off')
    ax.set_aspect('equal')
    
    plt.title('Finite State Automaton (FSA)\nPengendali Lampu Lalu Lintas', 
              fontsize=14, fontweight='bold', pad=20)
    
    return fig

# Main App
st.markdown('<div class="main-title">🚦 Pengendali Lampu Lalu Lintas Cerdas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pendekatan Finite State Automata dan Teori Graf</div>', unsafe_allow_html=True)

# Inisialisasi FSA
if 'fsa' not in st.session_state:
    st.session_state.fsa = TrafficLightFSA()

fsa = st.session_state.fsa

# Sidebar - Kontrol
with st.sidebar:
    st.header("⚙️ Kontrol Sistem")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start" if not st.session_state.running else "⏸️ Pause", 
                     use_container_width=True):
            st.session_state.running = not st.session_state.running
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.phase = 0
            st.session_state.time_in_phase = 0
            st.session_state.running = False
            st.session_state.fsa = TrafficLightFSA()
            st.session_state.history = []
            st.rerun()
    
    st.divider()
    
    # Mode manual
    st.session_state.manual_mode = st.checkbox("🎮 Mode Manual", value=st.session_state.manual_mode)
    
    if st.session_state.manual_mode:
        if st.button("⏭️ Next Phase", use_container_width=True):
            fsa.transition()
            st.session_state.time_in_phase = 0
            st.session_state.history.append({
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'state': fsa.current_state,
                'action': 'Manual Transition'
            })
            st.rerun()
    
    st.divider()
    
    st.header("📊 Statistik")
    config = fsa.get_current_config()
    st.metric("Fase Aktif", fsa.current_state)
    st.metric("Durasi Fase", f"{config['duration']}s")
    st.metric("Waktu Berlalu", f"{st.session_state.time_in_phase}s")
    st.metric("Total Transisi", len(st.session_state.history))
    
    st.divider()
    
    st.header("📖 Komponen FSA")
    with st.expander("States (Q)"):
        for state in fsa.states:
            st.code(state, language=None)
    
    with st.expander("Alphabet (Σ)"):
        for symbol in fsa.alphabet:
            st.code(symbol, language=None)
    
    with st.expander("Transition Function (δ)"):
        for state, trans in fsa.transitions.items():
            st.text(f"{state}:")
            for inp, next_state in trans.items():
                st.text(f"  {inp} → {next_state}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["🚦 Simulasi", "📈 Graf Persimpangan", "🤖 FSA Diagram", "📜 Riwayat"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Status fase saat ini
        config = fsa.get_current_config()
        st.subheader(f"📍 {config['name']}")
        
        # Progress bar
        progress = st.session_state.time_in_phase / config['duration']
        st.progress(progress)
        st.caption(f"Waktu: {st.session_state.time_in_phase}s / {config['duration']}s")
        
        # Visualisasi lampu
        st.subheader("Status Lampu Lalu Lintas")
        
        cols = st.columns(4)
        directions = ['north', 'south', 'east', 'west']
        direction_labels = ['🔼 Utara', '🔽 Selatan', '▶️ Timur', '◀️ Barat']
        
        for col, direction, label in zip(cols, directions, direction_labels):
            with col:
                state = config[direction]
                color_class = 'green-light' if state == 'GREEN' else 'yellow-light' if state == 'YELLOW' else 'red-light'
                st.markdown(f"""
                <div class="status-box {color_class}">
                    <h3 style="margin:0; font-size: 1.2em;">{label}</h3>
                    <p style="margin:5px 0 0 0; font-size: 1.5em; font-weight: bold;">{state}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Visualisasi persimpangan sederhana
        st.subheader("Visualisasi Persimpangan")
        
        fig_intersection, ax = plt.subplots(figsize=(8, 8))
        
        # Gambar jalan
        ax.add_patch(plt.Rectangle((-0.5, -3), 1, 6, color='#4b5563'))  # Vertikal
        ax.add_patch(plt.Rectangle((-3, -0.5), 6, 1, color='#4b5563'))  # Horizontal
        
        # Garis tengah
        ax.plot([0, 0], [-3, 3], 'y--', linewidth=2, alpha=0.7)
        ax.plot([-3, 3], [0, 0], 'y--', linewidth=2, alpha=0.7)
        
        # Lampu lalu lintas
        light_positions = {
            'north': (0.7, 1.5),
            'south': (-0.7, -1.5),
            'east': (1.5, -0.7),
            'west': (-1.5, 0.7)
        }
        
        for direction, (x, y) in light_positions.items():
            state = config[direction]
            color = '#10b981' if state == 'GREEN' else '#f59e0b' if state == 'YELLOW' else '#ef4444'
            circle = Circle((x, y), 0.3, color=color, ec='black', linewidth=2)
            ax.add_patch(circle)
        
        # Mobil
        car_positions = {
            'north': (0, 0.8) if config['north'] == 'GREEN' else (0, 2.5),
            'south': (0, -0.8) if config['south'] == 'GREEN' else (0, -2.5),
            'east': (0.8, 0) if config['east'] == 'GREEN' else (2.5, 0),
            'west': (-0.8, 0) if config['west'] == 'GREEN' else (-2.5, 0)
        }
        
        for direction, (x, y) in car_positions.items():
            if config[direction] == 'GREEN':
                ax.add_patch(plt.Rectangle((x-0.15, y-0.25), 0.3, 0.5, color='#3b82f6'))
            else:
                ax.add_patch(plt.Rectangle((x-0.15, y-0.25), 0.3, 0.5, color='#9ca3af', alpha=0.5))
        
        ax.set_xlim(-3.5, 3.5)
        ax.set_ylim(-3.5, 3.5)
        ax.axis('off')
        ax.set_aspect('equal')
        
        st.pyplot(fig_intersection)
        plt.close()
    
    with col2:
        st.subheader("🎯 State Saat Ini")
        st.info(f"**{fsa.current_state}**")
        
        st.subheader("🔄 Next State")
        next_states = fsa.transitions[fsa.current_state]
        for event, next_state in next_states.items():
            st.success(f"{event} → **{next_state}**")
        
        st.divider()
        
        st.subheader("📝 Penjelasan")
        st.write("""
        **Cara Kerja:**
        1. Sistem dimulai dari state S0 (Utara-Selatan Hijau)
        2. Setelah 30 detik, transisi ke S1 (Kuning)
        3. Setelah 5 detik, transisi ke S2 (Timur-Barat Hijau)
        4. Pola berulang secara siklis
        
        **Keamanan:**
        - Selalu ada fase kuning sebelum merah
        - Tidak ada konflik arah (NS dan EW tidak hijau bersamaan)
        """)

with tab2:
    st.header("📈 Representasi Teori Graf")
    st.write("""
    Graf persimpangan merepresentasikan:
    - **Nodes (Vertex):** Titik persimpangan dan arah jalan
    - **Edges:** Jalan yang menghubungkan titik-titik
    - **Weight:** Jarak atau waktu tempuh antar titik
    """)
    
    fig_graph = draw_intersection_graph(fsa)
    st.pyplot(fig_graph)
    plt.close()
    
    st.subheader("Adjacency Matrix")
    G = create_intersection_graph()
    adj_matrix = nx.adjacency_matrix(G).todense()
    df_adj = pd.DataFrame(adj_matrix, 
                         index=G.nodes(), 
                         columns=G.nodes())
    st.dataframe(df_adj)

with tab3:
    st.header("🤖 Diagram Finite State Automaton")
    st.write("""
    **Definisi Formal FSA:**
    - **Q** (States): Himpunan state sistem
    - **Σ** (Alphabet): Himpunan input (timer events)
    - **δ** (Transition Function): Fungsi transisi state
    - **q₀** (Start State): State awal
    - **F** (Accept States): Himpunan state akhir
    """)
    
    fig_fsa = draw_fsa_diagram(fsa)
    st.pyplot(fig_fsa)
    plt.close()
    
    st.subheader("Transition Table")
    transition_data = []
    for state in fsa.states:
        for event in fsa.alphabet:
            if event in fsa.transitions[state]:
                next_state = fsa.transitions[state][event]
                transition_data.append({
                    'Current State': state,
                    'Input': event,
                    'Next State': next_state
                })
    
    df_transitions = pd.DataFrame(transition_data)
    st.dataframe(df_transitions, use_container_width=True)

with tab4:
    st.header("📜 Riwayat Transisi")
    
    if st.session_state.history:
        df_history = pd.DataFrame(st.session_state.history)
        st.dataframe(df_history, use_container_width=True)
        
        # Grafik distribusi state
        st.subheader("Distribusi State")
        state_counts = df_history['state'].value_counts()
        st.bar_chart(state_counts)
    else:
        st.info("Belum ada riwayat transisi. Mulai simulasi untuk melihat riwayat.")

# Auto-update untuk mode otomatis
if st.session_state.running and not st.session_state.manual_mode:
    time.sleep(1)
    st.session_state.time_in_phase += 1
    
    config = fsa.get_current_config()
    if st.session_state.time_in_phase >= config['duration']:
        old_state = fsa.current_state
        fsa.transition()
        st.session_state.time_in_phase = 0
        
        st.session_state.history.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'state': fsa.current_state,
            'action': 'Auto Transition'
        })
    
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 20px;'>
    <b>Tugas Teori Graf & Automata</b><br>
    Pengendali Lampu Lalu Lintas Cerdas menggunakan FSA dan Teori Graf
</div>
""", unsafe_allow_html=True)