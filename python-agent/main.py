import os
import sys
import argparse
import random
from pathlib import Path
import yaml
from py4j.java_gateway import JavaGateway, GatewayParameters, java_import

# Default fallback configuration matching Section 13 schema
DEFAULT_CONFIG = {
    "experiment": {
        "id": "baseline_random_run",
        "hypothesis": "H1",
        "seed": 42
    },
    "datacenter": {
        "n_cloud_hosts": 20,
        "n_edge_nodes": 10,
    },
    "agent": {
        "precision": "fp32",
        "learning_rate": 0.0005,
        "gamma": 0.98,
        "target_update_freq": 750,
        "batch_size": 64,
    },
    "training": {
        "n_episodes": 600,
        "eval_every_n_episodes": 50
    }
}

def load_config(config_path: str) -> dict:
    if not config_path:
        return DEFAULT_CONFIG
    path = Path(config_path)
    if not path.exists():
        print(f"Warning: Config file {config_path} not found. Using default schema.")
        return DEFAULT_CONFIG
    with open(path, "r") as f:
        return yaml.safe_load(f)

def connect_java_gateway(host: str, port: int) -> JavaGateway:
    print(f"Connecting to Java Gateway at {host}:{port}...")
    try:
        gateway = JavaGateway(
            gateway_parameters=GatewayParameters(address=host, port=port, auto_convert=True)
        )
        # Test connection by accessing the JVM
        _ = gateway.jvm.java.lang.System.currentTimeMillis()
        print("Successfully connected to Java Gateway.")
        return gateway
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Ensure the java-sim container is running and accessible.")
        sys.exit(1)

def run_episode(gateway, jvm, config):
    """
    Runs a single simulation episode using the remote JVM.
    This serves as the core lifecycle layout for the Gym environment steps.
    """
    # Import required Java classes from the remote JVM
    java_import(jvm, "java.util.ArrayList")
    java_import(jvm, "org.cloudsimplus.core.CloudSimPlus")
    java_import(jvm, "org.cloudsimplus.datacenters.DatacenterSimple")
    java_import(jvm, "org.cloudsimplus.hosts.HostSimple")
    java_import(jvm, "org.cloudsimplus.resources.PeSimple")
    java_import(jvm, "org.cloudsimplus.vms.VmSimple")
    java_import(jvm, "org.cloudsimplus.cloudlets.CloudletSimple")
    java_import(jvm, "org.cloudsimplus.brokers.DatacenterBrokerSimple")
    java_import(jvm, "org.cloudsimplus.schedulers.cloudlet.CloudletSchedulerTimeShared")
    java_import(jvm, "org.cloudsimplus.schedulers.vm.VmSchedulerTimeShared")

    def to_java_list(py_list):
        java_list = jvm.ArrayList()
        for item in py_list:
            java_list.add(item)
        return java_list

    # Initialize simulation instance
    simulation = jvm.CloudSimPlus()

    # Configure a basic topology
    pe_list = to_java_list([jvm.PeSimple(1000.0) for _ in range(8)])
    host = jvm.HostSimple(16384, 10000, 1000000, pe_list)
    host.setVmScheduler(jvm.VmSchedulerTimeShared())

    datacenter = jvm.DatacenterSimple(simulation, to_java_list([host]))
    broker = jvm.DatacenterBrokerSimple(simulation)

    vm_list = [
        jvm.VmSimple(1000.0, 1)
           .setRam(2048)
           .setBw(1000)
           .setSize(10000)
           .setCloudletScheduler(jvm.CloudletSchedulerTimeShared())
        for _ in range(5)
    ]

    cloudlet_list = [
        jvm.CloudletSimple(10000, 1)
        for _ in range(10)
    ]

    # Assign Cloudlets to VMs
    for cloudlet in cloudlet_list:
        selected_vm = random.choice(vm_list)
        cloudlet.setVm(selected_vm)

    broker.submitVmList(to_java_list(vm_list))
    broker.submitCloudletList(to_java_list(cloudlet_list))

    # Execute simulation
    simulation.start()

    # Log metrics
    print(f"\n--- Episode {config['experiment']['id']} Finished ---")
    for cloudlet in broker.getCloudletFinishedList():
        print(
            f"Cloudlet {cloudlet.getId()} -> "
            f"Assigned to VM {cloudlet.getVm().getId()} | "
            f"CPU Execution Time: {cloudlet.getTotalExecutionTime():.2f}s"
        )

def main():
    parser = argparse.ArgumentParser(description="d2ql Agent Training Orchestrator")
    parser.add_argument("--config", type=str, default="", help="Path to YAML configuration file")
    args = parser.parse_args()

    # Load experimental variables
    config = load_config(args.config)
    
    # Configure random seeds for reproducibility
    seed = config["experiment"]["seed"]
    random.seed(seed)

    # Read network details from environment variables for Docker deployment [1]
    java_host = os.getenv("JAVA_HOST", "localhost")
    java_port = int(os.getenv("JAVA_PORT", 25333))

    # Connect to the running simulation process [1]
    gateway = connect_java_gateway(java_host, java_port)
    jvm = gateway.jvm

    try:
        # Check if the environment wrapper and agent modules are implemented
        try:
            from d2ql.env import CloudSimEnv
            from d2ql.agent import DDQNAgent
            
            print("Imported custom environment and agent modules. Starting training loop...")
            # Placeholder for future Gymnasium loop:
            # env = CloudSimEnv(config)
            # agent = DDQNAgent(env.observation_space.shape[0], env.action_space.n, config)
            # ... training loop logic using the custom components
            
        except ImportError:
            print("Custom d2ql package modules (env/agent) not yet found.")
            print("Executing fallback simulation verification on the connected JVM...")
            run_episode(gateway, jvm, config)

    finally:
        # Safely detach client resources without terminating the remote server
        gateway.close()
        print("Gateway client connection closed.")

if __name__ == "__main__":
    main()