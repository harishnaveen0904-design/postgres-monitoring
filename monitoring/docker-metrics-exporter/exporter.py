import time
import docker
from prometheus_client import Gauge, start_http_server

CPU = Gauge("docker_container_cpu_percent", "Docker container CPU usage percent", ["name"])
MEM = Gauge("docker_container_memory_usage_bytes", "Docker container memory usage bytes", ["name"])
MEM_LIMIT = Gauge("docker_container_memory_limit_bytes", "Docker container memory limit bytes", ["name"])

client = docker.from_env()


def cpu_percent(stats):
    cpu = stats.get("cpu_stats", {})
    prev = stats.get("precpu_stats", {})
    cpu_delta = cpu.get("cpu_usage", {}).get("total_usage", 0) - prev.get("cpu_usage", {}).get("total_usage", 0)
    system_delta = cpu.get("system_cpu_usage", 0) - prev.get("system_cpu_usage", 0)
    online = cpu.get("online_cpus") or 1
    if cpu_delta > 0 and system_delta > 0:
        return (cpu_delta / system_delta) * online * 100.0
    return 0.0


def collect():
    for c in client.containers.list():
        name = c.name
        try:
            stats = c.stats(stream=False)
            memory = stats.get("memory_stats", {})
            CPU.labels(name=name).set(cpu_percent(stats))
            MEM.labels(name=name).set(memory.get("usage", 0))
            MEM_LIMIT.labels(name=name).set(memory.get("limit", 0))
        except Exception:
            continue


if __name__ == "__main__":
    start_http_server(9323)
    while True:
        collect()
        time.sleep(5)
