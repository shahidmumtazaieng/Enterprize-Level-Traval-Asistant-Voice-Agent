import asyncio
import logging
from typing import Dict, Any, Optional
import time
from dataclasses import dataclass, field
from collections import deque
import json

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring latency and throughput"""
    request_count: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    error_count: int = 0
    throughput: float = 0.0  # requests per second
    timestamp: float = field(default_factory=time.time)

class RealTimeOptimizer:
    """Optimizes the backend for low latency and real-time performance"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.request_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.is_processing = False
        
    def record_request_start(self, endpoint: str) -> float:
        """
        Record the start time of a request
        
        Args:
            endpoint: Endpoint name
            
        Returns:
            float: Start time
        """
        if endpoint not in self.metrics:
            self.metrics[endpoint] = PerformanceMetrics()
        
        self.metrics[endpoint].request_count += 1
        return time.time()
    
    def record_request_end(self, endpoint: str, start_time: float, success: bool = True):
        """
        Record the end of a request and update metrics
        
        Args:
            endpoint: Endpoint name
            start_time: Request start time
            success: Whether the request was successful
        """
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        
        if endpoint not in self.metrics:
            self.metrics[endpoint] = PerformanceMetrics()
            
        metrics = self.metrics[endpoint]
        metrics.total_response_time += response_time
        metrics.avg_response_time = metrics.total_response_time / metrics.request_count
        metrics.min_response_time = min(metrics.min_response_time, response_time)
        metrics.max_response_time = max(metrics.max_response_time, response_time)
        
        if not success:
            metrics.error_count += 1
            
        # Calculate throughput (requests per second) based on recent history
        if len(self.response_times) > 1:
            time_window = self.response_times[-1] - self.response_times[0] if len(self.response_times) > 1 else 1
            metrics.throughput = len(self.response_times) / max(time_window, 0.001)
    
    def get_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            endpoint: Optional specific endpoint
            
        Returns:
            Dict with metrics
        """
        if endpoint:
            return self.metrics.get(endpoint, PerformanceMetrics())
        return self.metrics
    
    async def queue_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Queue a request for processing to prevent overload
        
        Args:
            request_data: Request data
            
        Returns:
            Dict with response
        """
        try:
            # Add request to queue
            await self.request_queue.put(request_data)
            
            # Process if not already processing
            if not self.is_processing:
                self.is_processing = True
                asyncio.create_task(self._process_queue())
            
            # Wait for response
            response = await self._wait_for_response(request_data.get('request_id'))
            return response
        except Exception as e:
            self.logger.error(f"Error queuing request: {str(e)}")
            raise
    
    async def _process_queue(self):
        """Process requests from the queue"""
        try:
            while not self.request_queue.empty():
                request_data = await self.request_queue.get()
                try:
                    # Process the request (implementation depends on request type)
                    response = await self._process_request(request_data)
                    
                    # Store response for retrieval
                    request_id = request_data.get('request_id')
                    if request_id:
                        # In a real implementation, you would store this in a proper cache
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error processing queued request: {str(e)}")
                finally:
                    self.request_queue.task_done()
        finally:
            self.is_processing = False
    
    async def _process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single request
        
        Args:
            request_data: Request data
            
        Returns:
            Dict with response
        """
        # This is a placeholder implementation
        # In a real system, you would implement actual request processing
        request_type = request_data.get('type', 'unknown')
        
        if request_type == 'session_create':
            # Simulate session creation
            await asyncio.sleep(0.01)  # 10ms
            return {'status': 'success', 'session_id': 'sess_12345'}
        elif request_type == 'audio_process':
            # Simulate audio processing
            await asyncio.sleep(0.005)  # 5ms
            return {'status': 'success', 'ack': True}
        else:
            return {'status': 'unknown_request_type', 'type': request_type}
    
    async def _wait_for_response(self, request_id: str) -> Dict[str, Any]:
        """
        Wait for a response to a queued request
        
        Args:
            request_id: Request identifier
            
        Returns:
            Dict with response
        """
        # In a real implementation, you would wait for the actual response
        # This is a simplified implementation
        await asyncio.sleep(0.001)  # 1ms
        return {'status': 'success', 'message': 'Request queued'}

# Global optimizer instance
optimizer = RealTimeOptimizer(logging.getLogger(__name__))

def get_optimizer() -> RealTimeOptimizer:
    """Get the global optimizer instance"""
    return optimizer