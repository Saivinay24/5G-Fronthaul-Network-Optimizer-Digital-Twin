"""
Layer 1: Telemetry & Analysis Layer - 3-Link Compliance Extension

This module adds hierarchical clustering to force exactly 3 links,
satisfying the problem statement while maintaining our high-resolution mode.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


def discover_topology_3link(loss_data) -> Dict[int, List[int]]:
    """
    Compliance mode: Force exactly 3 links using hierarchical clustering.
    This satisfies the problem statement requirement while our standard
    discover_topology() provides higher-resolution analysis.
    
    Args:
        loss_data: DataFrame or Dict with packet loss per cell
        
    Returns:
        Dictionary mapping link_id → [cell_ids] (exactly 3 links)
    """
    print(f"\n🔗 Discovering topology (3-Link Compliance Mode)...")
    
    # Convert dict to DataFrame if needed
    if isinstance(loss_data, dict):
        loss_df = pd.DataFrame(loss_data)
    else:
        loss_df = loss_data
        
    # Binarize loss events
    binary_loss = (loss_df > 0).astype(int)
    
    if binary_loss.sum().sum() == 0:
        print("✅ No packet loss detected")
        # Distribute cells evenly across 3 links
        cells = list(loss_df.columns)
        n = len(cells)
        return {
            1: cells[:n//3],
            2: cells[n//3:2*n//3],
            3: cells[2*n//3:]
        }
        
    # Correlation matrix
    corr_matrix = binary_loss.corr()
    
    # Convert correlation to distance (1 - correlation)
    distance_matrix = 1 - corr_matrix.fillna(0)
    
    # Ensure symmetric and non-negative
    distance_matrix = distance_matrix.clip(lower=0)
    
    # Convert to condensed distance matrix
    condensed_dist = squareform(distance_matrix, checks=False)
    
    # Hierarchical clustering
    Z = linkage(condensed_dist, method='average')
    
    # Cut dendrogram to get exactly 3 clusters
    labels = fcluster(Z, t=3, criterion='maxclust')
    
    # Build clusters dictionary
    clusters = {}
    for link_id in range(1, 4):
        cells_in_link = [cell for i, cell in enumerate(corr_matrix.columns) 
                       if labels[i] == link_id]
        if cells_in_link:
            clusters[link_id] = sorted(cells_in_link)
    
    # Print discovered links
    print(f"\n📊 3-LINK TOPOLOGY (Problem Statement Compliance):")
    for link_id, cells in clusters.items():
        print(f"   🔗 LINK {link_id}: Cells {cells} (Count: {len(cells)})")
            
    return clusters
