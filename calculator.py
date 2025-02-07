import math

class RedisCalculator:
    # Constants for calculations
    MEMORY_OVERHEAD_PER_KEY = 150  # bytes
    BASE_MEMORY = 50 * 1024 * 1024  # 50MB base memory
    MAX_KEYS_PER_CPU_CORE = 1000000
    BASE_LATENCY = 0.2  # ms
    
    @staticmethod
    def calculate_memory(avg_object_size, num_keys):
        """Calculate total memory requirements in bytes"""
        data_size = avg_object_size * num_keys
        overhead = RedisCalculator.MEMORY_OVERHEAD_PER_KEY * num_keys
        total_memory = data_size + overhead + RedisCalculator.BASE_MEMORY
        return total_memory

    @staticmethod
    def calculate_latency(avg_object_size, num_keys, tps=0):
        """Estimate latency in milliseconds"""
        # Base latency + overhead based on data size and load
        size_factor = math.log2(max(1, avg_object_size / 1024))  # Size impact
        load_factor = math.log2(max(1, tps / 1000)) if tps else 0  # TPS impact
        keys_factor = math.log2(max(1, num_keys / 100000))  # Keys impact
        
        latency = (RedisCalculator.BASE_LATENCY + 
                  (0.1 * size_factor) +
                  (0.2 * load_factor) +
                  (0.1 * keys_factor))
        return latency

    @staticmethod
    def calculate_cpu_cores(num_keys, tps=0):
        """Estimate required CPU cores"""
        # Base calculation on keys and TPS
        cores_by_keys = math.ceil(num_keys / RedisCalculator.MAX_KEYS_PER_CPU_CORE)
        cores_by_tps = math.ceil(tps / 50000) if tps else 0  # Assume 50k TPS per core
        
        return max(1, max(cores_by_keys, cores_by_tps))

    @staticmethod
    def format_memory_size(bytes_size):
        """Format memory size to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
