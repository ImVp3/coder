import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

class GraphLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        log_file = os.path.join(self.log_dir, f"graph_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Configure logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("GraphLogger")
        
    def log_graph_start(self, graph_id: str, config: Dict[str, Any]):
        """Log when a graph starts running"""
        self.logger.info(f"Graph {graph_id} started with config: {config}")
        
    def log_graph_end(self, graph_id: str, status: str, duration: float):
        """Log when a graph finishes running"""
        self.logger.info(f"Graph {graph_id} completed with status {status} in {duration:.2f} seconds")
        
    def log_node_execution(self, graph_id: str, node_id: str, input_data: Optional[Dict[str, Any]] = None):
        """Log when a node starts executing"""
        self.logger.info(f"Graph {graph_id} - Node {node_id} executing with input: {input_data}")
        
    def log_node_completion(self, graph_id: str, node_id: str, output_data: Optional[Dict[str, Any]] = None, duration: float = 0.0):
        """Log when a node completes execution"""
        self.logger.info(f"Graph {graph_id} - Node {node_id} completed in {duration:.2f} seconds with output: {output_data}")
        
    def log_error(self, graph_id: str, node_id: Optional[str], error: Exception):
        """Log any errors that occur during execution"""
        self.logger.error(f"Graph {graph_id} - Node {node_id if node_id else 'N/A'} - Error: {str(error)}", exc_info=True)
        
    def log_graph_state(self, graph_id: str, state: str):
        """Log graph state changes"""
        self.logger.info(f"Graph {graph_id} state changed to: {state}") 