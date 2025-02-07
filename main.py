import streamlit as st
from calculator import RedisCalculator
import altair as alt

def validate_input(value, min_value, max_value, field_name):
    """Validate numeric input within range"""
    try:
        value = float(value)
        if value < min_value or value > max_value:
            return False, f"{field_name} must be between {min_value} and {max_value}"
        return True, value
    except ValueError:
        return False, f"{field_name} must be a number"

def convert_to_bytes(size, unit):
    """Convert size to bytes based on unit"""
    units = {
        "Bytes": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "TB": 1024 * 1024 * 1024 * 1024
    }
    return size * units[unit]

def main():
    st.set_page_config(
        page_title="Redis Deployment Calculator",
        page_icon="🔄",
        layout="wide"
    )

    st.title("Redis Deployment Calculator")
    st.markdown("""
    Estimate memory, latency, and CPU requirements for your Redis deployment.
    Fill in the configuration parameters below to get started.
    """)

    # Input form
    with st.form("redis_calculator"):
        col1, col2 = st.columns(2)

        with col1:
            size_col1, size_col2 = st.columns([2, 1])
            with size_col1:
                avg_size = st.number_input(
                    "Average Object Size",
                    min_value=1,
                    value=1000,
                    help="Average size of your Redis objects"
                )
            with size_col2:
                size_unit = st.selectbox(
                    "Unit",
                    options=["Bytes", "KB", "MB", "GB", "TB"],
                    index=0,
                    help="Size unit for the average object size"
                )

            num_keys = st.number_input(
                "Number of Keys",
                min_value=1,
                value=100000,
                help="Total number of keys in your Redis database"
            )

            ttl = st.number_input(
                "TTL (seconds)",
                min_value=0,
                value=3600,
                help="Time-To-Live for keys (0 for no expiration)"
            )

        with col2:
            eviction_policy = st.selectbox(
                "Eviction Policy",
                options=[
                    "noeviction",
                    "allkeys-lru",
                    "volatile-lru",
                    "allkeys-random",
                    "volatile-random",
                    "volatile-ttl"
                ],
                help="Redis eviction policy for when memory limit is reached"
            )

            tps = st.number_input(
                "Transactions Per Second (optional)",
                min_value=0,
                value=1000,
                help="Expected transactions per second"
            )

        submitted = st.form_submit_button("Calculate Requirements")

    if submitted:
        # Convert size to bytes before calculation
        avg_size_bytes = convert_to_bytes(avg_size, size_unit)

        # Calculate requirements
        memory_bytes = RedisCalculator.calculate_memory(avg_size_bytes, num_keys)
        latency = RedisCalculator.calculate_latency(avg_size_bytes, num_keys, tps)
        cpu_cores = RedisCalculator.calculate_cpu_cores(num_keys, tps)

        # Display results
        st.header("Deployment Requirements")

        # Get 24-hour projection from simulation
        df = RedisCalculator.simulate_memory_usage(
            avg_size_bytes, num_keys, tps, ttl, eviction_policy
        )
        projected_memory = df['memory'].iloc[-1]  # Last value in simulation
        trend, percent_change = RedisCalculator.analyze_memory_trend(df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Initial Memory Required",
                value=RedisCalculator.format_memory_size(memory_bytes)
            )
            st.info("""
            Includes:
            - Data size
            - Key overhead
            - Base Redis memory
            """)

        with col2:
            st.metric(
                label="Projected Memory (24h)",
                value=RedisCalculator.format_memory_size(projected_memory),
                delta=f"{percent_change:.1f}%" if trend != "stable" else "stable"
            )
            st.info(f"""
            Memory trend: {trend.upper()}
            Based on:
            - Current TPS
            - TTL settings
            - Eviction policy
            """)

        with col3:
            st.metric(
                label="Estimated Latency",
                value=f"{latency:.2f} ms"
            )
            st.info("""
            Factors:
            - Object size
            - Number of keys
            - Transaction load
            """)

        with col4:
            st.metric(
                label="Recommended CPU Cores",
                value=f"{cpu_cores}"
            )
            st.info("""
            Based on:
            - Key count
            - Transaction rate
            - Processing overhead
            """)

        # Memory usage simulation
        st.subheader("Memory Usage Simulation (24 hours)")

        st.info("""
        This graph simulates how your Redis memory usage may change over the next 24 hours based on:
        - Your initial data (shown as "Memory Required" above)
        - New keys being added at your specified TPS rate
        - Keys being removed based on TTL expiration
        - Your selected eviction policy

        The shape of this graph may differ from the initial memory requirement because it shows the
        dynamic behavior of your Redis instance over time, while the "Memory Required" metric shows
        your immediate memory needs for the current data.

        📈 Rising curve: More keys being added than removed
        📉 Falling curve: Keys being expired/evicted faster than added
        ➡️ Flat line: Equilibrium between new and removed keys
        """)

        df = RedisCalculator.simulate_memory_usage(
            avg_size_bytes, num_keys, tps, ttl, eviction_policy
        )

        # Convert memory from bytes to MB for visualization
        df['memory_mb'] = df['memory'] / (1024 * 1024)

        # Create memory usage chart
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X('timestamp', title='Time (hours)'),
            y=alt.Y('memory_mb', title='Memory Usage (MB)'),
            tooltip=[
                alt.Tooltip('timestamp', title='Time (hours)', format='.1f'),
                alt.Tooltip('memory_mb', title='Memory (MB)', format='.2f')
            ]
        ).properties(
            width=800,
            height=400
        ).interactive()

        st.altair_chart(chart)

        st.caption("""
        This simulation shows estimated memory usage over time based on:
        - Initial data size
        - Transaction rate (TPS)
        - TTL settings
        - Selected eviction policy
        """)

        # Additional recommendations
        st.subheader("Configuration Recommendations")

        # Memory recommendations
        if memory_bytes > 10 * 1024 * 1024 * 1024:  # 10GB
            st.warning("⚠️ Consider sharding your Redis deployment due to high memory usage")

        # Eviction policy recommendations
        if ttl == 0 and eviction_policy.startswith("volatile"):
            st.warning("⚠️ Volatile eviction policies are ineffective when TTL is not set")

        # TPS recommendations
        if tps > 50000:
            st.warning("⚠️ High TPS detected. Consider Redis Cluster for better performance")

if __name__ == "__main__":
    main()