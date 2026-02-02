import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import os
import re
from typing import Dict, List, Optional, Tuple

# --- CONFIGURATION ---
DATA_FOLDER = 'data'
SYMBOL_DURATION_SEC = 35.7e-6  # Symbol duration in seconds (35.7 microseconds)
BUFFER_SIZE_US = 143          # Total buffer size in microseconds

class NetworkLoader:
    """Handles robust data loading and cleaning."""
    
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.pkt_stats: Dict[int, pd.DataFrame] = {}
        self.throughput: Dict[int, pd.DataFrame] = {}

    def load_pkt_stats(self) -> Dict[int, pd.Series]:
        """Loads and processes packet statistics files."""
        files = sorted(glob.glob(os.path.join(self.folder_path, "pkt-stats-cell-*.dat")))
        if not files:
            print("❌ No 'pkt-stats' files found!")
            return {}
        
        print(f"🔹 Loading {len(files)} packet stat files...")
        loss_data = {}
        
        for filepath in files:
            cell_id = self._extract_cell_id(filepath)
            if cell_id is None: continue
            
            try:
                # Load data (skip irregular header)
                df = pd.read_csv(filepath, sep=r'\s+', skiprows=1, names=['timestamp', 'tx', 'rx', 'too_late'])
                
                # Calculate Effective Loss = (Tx - Rx) + TooLate
                df['loss'] = (df['tx'] - df['rx']) + df['too_late']
                
                # Store full DF for later analysis
                self.pkt_stats[cell_id] = df.set_index('timestamp')
                
                # Setup Loss Series for Topology Mapping
                loss_data[cell_id] = self.pkt_stats[cell_id]['loss']
                
            except Exception as e:
                print(f"⚠️ Error loading stats for Cell {cell_id}: {e}")
                
        return loss_data

    def load_throughput(self, cell_ids: List[int]) -> Dict[int, pd.DataFrame]:
        """Loads throughput data only for relevant cells to save memory."""
        # Clean previous loads to manage memory if needed, or just append
        # For this scale (24 cells), we can keep them in memory or clear if needed.
        # We will clear existing for the new batch to be safe.
        self.throughput.clear()
        
        print(f"🔹 Loading throughput data for {len(cell_ids)} cells...")
        
        for cell_id in cell_ids:
            filepath = os.path.join(self.folder_path, f"throughput-cell-{cell_id}.dat")
            if not os.path.exists(filepath):
                print(f"⚠️ Throughput file missing for Cell {cell_id}")
                continue
                
            try:
                # Throughput file: timestamp <space> bits
                df = pd.read_csv(filepath, sep=r'\s+', names=['timestamp', 'bits'])
                
                # Handling duplicates: group by timestamp and sum bits
                df = df.groupby('timestamp').sum()
                
                self.throughput[cell_id] = df
            except Exception as e:
                print(f"⚠️ Error loading throughput for Cell {cell_id}: {e}")
                
        return self.throughput

    @staticmethod
    def _extract_cell_id(filepath: str) -> Optional[int]:
        match = re.search(r'cell-(\d+)', filepath)
        return int(match.group(1)) if match else None


class TopologyMapper:
    """Identifies network topology using statistical correlation."""
    
    def __init__(self, loss_data: Dict[int, pd.Series]):
        self.loss_df = pd.DataFrame(loss_data).sort_index(axis=1).fillna(0)
        self.clusters: Dict[int, List[int]] = {} # Map LinkID -> List[CellID]
        self.independent_cells: List[int] = []

    def identify_topology(self, correlation_threshold: float = 0.70):
        """ 
        Clusters cells based on loss correlation.
        
        Methodology:
        1. Binarize Loss: Convert loss counts to binary events (1 if loss > 0, else 0).
           This focuses on the *timing* of loss events rather than magnitude.
        2. Pearson Correlation: specific timestamps of packet loss are compared between all pairs of cells.
           Cells sharing a physical link will experience congestion-induced loss at the exact same moments.
           High correlation coefficient (> 0.70) indicates shared infrastructure (Shared Risk Link Group).
        """
        # Binarize loss (1 if loss > 0)
        binary_loss = (self.loss_df > 0).astype(int)
        
        if binary_loss.sum().sum() == 0:
            print("✅ Perfect Network: No packet loss detected.")
            # Treat all as independent
            self.independent_cells = self.loss_df.columns.tolist()
            return

        corr_matrix = binary_loss.corr()
        
        # heatmap
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=False, cmap='RdYlGn_r', vmin=0, vmax=1)
        plt.title("Network Topology Correlation Map")
        plt.tight_layout()
        output_dir = os.path.join("results", "figures")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'topology_heatmap.png')
        plt.savefig(output_path)
        print(f"✅ Topology Heatmap saved to '{output_path}'")

        # Grouping Logic
        processed = set()
        link_id = 1
        
        columns = self.loss_df.columns.tolist()
        for cell in columns:
            if cell in processed:
                continue
            
            # Find correlated neighbours
            neighbours = corr_matrix[cell][corr_matrix[cell] > correlation_threshold].index.tolist()
            
            if len(neighbours) > 1:
                self.clusters[link_id] = neighbours
                processed.update(neighbours)
                print(f"🔗 LINK {link_id} Identified: Cells {neighbours}")
                link_id += 1
            else:
                self.independent_cells.append(cell)
                # processed added later or ignored. 
                # If we don't add to processed, it might be picked up later? 
                # No, if it has no >0.70 neighbours, it won't be picked up by others either (symmetry).
                processed.add(cell)
        
        print(f"⚡ Independent/Singleton Cells: {self.independent_cells}")


class CapacityOptimizer:
    """Analyzes bottleneck capacity and proposes optimizations."""
    
    def __init__(self, loader: NetworkLoader, mapper: TopologyMapper):
        self.loader = loader
        self.mapper = mapper

    def analyze_bottlenecks(self):
        """Calculates aggregate throughput for identified links."""
        print("\n🚀 Starting Capacity Analysis & Optimization Simulation...")
        
        results = []
        
        # 1. Analyze Clusters
        for link_id, cells in self.mapper.clusters.items():
            res = self._analyze_group(f"Link {link_id}", cells)
            if res:
                results.append(res)
                # Plot
                self._plot_capacity(f"Link {link_id}", cells, res['throughput_gbps'], res['limit_est'])
                
                # Run Capacity Optimization
                self.optimize_capacity(f"Link {link_id}", res['throughput_gbps'])

        return pd.DataFrame([r for r in results if 'throughput_gbps' not in r]) # Strip series for dataframe printing

    def verify_independents(self):
        """Checks independent cells for hidden issues."""
        print("\n🔎 Verifying Independent Cells (Deep Scan)...")
        # Load all independent cells
        if not self.mapper.independent_cells:
            return
            
        self.loader.load_throughput(self.mapper.independent_cells)
        
        for cell in self.mapper.independent_cells:
            # Check loss first
            total_loss = self.mapper.loss_df[cell].sum()
            
            if cell in self.loader.throughput:
                df = self.loader.throughput[cell]
                # calc gbps
                gbps = (df['bits'] / SYMBOL_DURATION_SEC) / 1e9
                peak = gbps.max()
                avg = gbps.mean()
                
                status = "✅ Healthy" if total_loss == 0 else "⚠️  Has Loss"
                print(f"   Cell {cell}: Loss Events={total_loss} | Peak={peak:.2f}G | Avg={avg:.2f}G -> {status}")

    def _analyze_group(self, name: str, cells: List[int]):
        self.loader.load_throughput(cells)
        common_dfs = []
        for c in cells:
            if c in self.loader.throughput:
                common_dfs.append(self.loader.throughput[c]['bits'])
        
        if not common_dfs: return None
        
        combined = pd.concat(common_dfs, axis=1).fillna(0)
        total_bits = combined.sum(axis=1)
        
        throughput_gbps = (total_bits / SYMBOL_DURATION_SEC) / 1e9
        
        max_peak = throughput_gbps.max()
        avg_load = throughput_gbps.mean()
        
        papr = max_peak / avg_load if avg_load > 0 else 0
        
        limit_est = 20.0 if max_peak > 10.0 else 10.0
        if max_peak > 20.0: limit_est = 25.0
        
        overload_count = (throughput_gbps > limit_est).sum()
        
        print(f"\n📊 {name} Analysis (Cells {cells}):")
        print(f"   ► Peak Throughput: {max_peak:.2f} Gbps")
        print(f"   ► Avg Throughput:  {avg_load:.2f} Gbps")
        print(f"   ► PAPR: {papr:.2f}x")
        
        return {
            'link': name,
            'cells': str(cells),
            'peak_gbps': max_peak,
            'avg_gbps': avg_load,
            'papr': papr,
            'throughput_gbps': throughput_gbps, # Store for plotting
            'limit_est': limit_est
        }

    def optimize_capacity(self, name: str, throughput_gbps: pd.Series):
        """
        Determines the optimal link capacity required.
        Scenarios:
        1. No Buffer: Capacity >= Peak Traffic
        2. With Buffer (143us): Capacity >= Min rate to keep loss <= 1% and buffer <= 143us (implicit).
        
        Note on Buffer Size in Bits: The problem states buffer is 143us. 
        In bits, BufferSize = LinkRate * 143us.
        So higher link rate = larger buffer in bits.
        """
        print(f"   🌊 Capacity Optimization for {name}...")
        
        # Scenario 1: No Buffer
        # Required = Peak
        req_no_buffer = throughput_gbps.max()
        
        # Scenario 2: With Buffer
        # 🧠 ALGORITHM: Binary Search for Optimal Capacity
        # We need to find the global minimum capacity 'C' such that:
        # Loss(C, 143us Buffer) <= 1%
        # Range: [Avg, Peak] -> This is a monotonic function (Higher Capacity = Lower Loss), so Binary Search is perfect O(log N).
        low = throughput_gbps.mean()
        high = req_no_buffer
        optimal_rate = high
        
        # Optimization loop (Precision 0.1G)
        for _ in range(20): 
            mid = (low + high) / 2
            loss_ratio = self._simulate_loss(throughput_gbps, mid)
            
            if loss_ratio <= 0.01: # 1% allowed
                optimal_rate = mid
                high = mid
            else:
                low = mid
                
        savings = (1 - optimal_rate / req_no_buffer) * 100
        
        print(f"      ► Required Capacity (No Buffer):   {req_no_buffer:.2f} Gbps")
        print(f"      ► Required Capacity (With Buffer): {optimal_rate:.2f} Gbps (Loss allowed 1%)")
        print(f"      ► Optimization Savings:            {savings:.1f}%")

    def _simulate_loss(self, throughput_gbps: pd.Series, capacity_gbps: float) -> float:
        """Simulates Leaky Bucket to calculate loss ratio."""
        # Rates in Bits/Symbol
        incoming_bits = throughput_gbps.values * 1e9 * SYMBOL_DURATION_SEC
        leak_bits = capacity_gbps * 1e9 * SYMBOL_DURATION_SEC
        
        # Buffer Limit in Bits (Dynamic based on Link Rate)
        max_buffer_bits = capacity_gbps * 1e9 * (BUFFER_SIZE_US * 1e-6)
        
        current_buffer = 0.0
        total_loss_bits = 0.0
        total_input_bits = np.sum(incoming_bits)
        
        if total_input_bits == 0: return 0.0
        
        # Fast iterative simulation
        # Net flow = In - Out
        # We need to clamp buffer at 0 and max.
        
        # Using a simple python loop for correctness (numba would be faster but sticking to std libs)
        for bits in incoming_bits:
            current_buffer += (bits - leak_bits)
            
            if current_buffer < 0:
                current_buffer = 0
            elif current_buffer > max_buffer_bits:
                loss = current_buffer - max_buffer_bits
                total_loss_bits += loss
                current_buffer = max_buffer_bits
                
        return total_loss_bits / total_input_bits


    def _plot_capacity(self, name, cells, throughput_gbps, limit_est):
        plt.figure(figsize=(10, 4))
        plt.plot(throughput_gbps.index, throughput_gbps.values, label='Traffic', alpha=0.7)
        plt.axhline(y=limit_est, color='r', linestyle='--', label=f'Limit ({limit_est}G)')
        plt.title(f"{name} (Cells {cells}): Traffic vs Capacity")
        plt.xlabel("Time (s)")
        plt.ylabel("Gbps")
        plt.legend()
        output_dir = os.path.join("results", "figures")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{name.lower().replace(' ', '_')}_capacity.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close() # Free memory


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("\n🔹 initializing Fronthaul Network Optimizer...")
    try:
        loader = NetworkLoader(DATA_FOLDER)
        loss_data = loader.load_pkt_stats()
        
        if loss_data:
            mapper = TopologyMapper(loss_data)
            mapper.identify_topology(correlation_threshold=0.70)
            
            optimizer = CapacityOptimizer(loader, mapper)
            # Analyze Clusters
            summary = optimizer.analyze_bottlenecks()
            
            # Verify Independents
            optimizer.verify_independents()
            
            print("\n✅ Analysis Complete.")
            
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()