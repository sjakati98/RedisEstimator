import math
import pandas as pd
import numpy as np

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

    @staticmethod
    def simulate_memory_usage(avg_object_size, initial_keys, tps, ttl, eviction_policy, duration_hours=24):
        """Simulate memory usage over time considering TPS and eviction"""
        timestamps = np.linspace(0, duration_hours * 3600, num=100)  # 100 points over duration
        memory_usage = []
        current_keys = initial_keys

        for t in timestamps:
            # Calculate new keys added
            new_keys = tps * t

            # Calculate expired keys based on TTL
            if ttl > 0:
                expired_keys = tps * max(0, t - ttl)
            else:
                expired_keys = 0

            # Apply eviction policy effects
            if eviction_policy != "noeviction":
                # Simulate different eviction policies
                if eviction_policy.startswith("allkeys"):
                    # More aggressive eviction
                    eviction_factor = 0.8
                else:  # volatile policies
                    # Less aggressive, only affects keys with TTL
                    eviction_factor = 0.9

                if current_keys * avg_object_size > RedisCalculator.BASE_MEMORY * 10:
                    expired_keys += (current_keys * (1 - eviction_factor))

            # Update current keys
            current_keys = initial_keys + new_keys - expired_keys
            current_keys = max(0, current_keys)  # Ensure non-negative

            # Calculate memory at this point
            memory = RedisCalculator.calculate_memory(avg_object_size, current_keys)
            memory_usage.append(memory)

        # Create DataFrame for visualization
        df = pd.DataFrame({
            'timestamp': timestamps / 3600,  # Convert to hours
            'memory': memory_usage
        })

        return df

    @staticmethod
    def analyze_memory_trend(df):
        """Analyze the memory usage trend from simulation data"""
        memory_values = df['memory'].values
        start_memory = memory_values[0]
        end_memory = memory_values[-1]

        # Calculate percentage change
        percent_change = ((end_memory - start_memory) / start_memory) * 100

        # Determine trend
        if abs(percent_change) < 1:  # Less than 1% change
            return "stable", percent_change
        elif percent_change > 0:
            return "growing", percent_change
        else:
            return "shrinking", percent_change