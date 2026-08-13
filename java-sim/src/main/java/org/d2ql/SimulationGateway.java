```java
package org.d2ql;

import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.utilizationmodels.UtilizationModelFull;
import org.cloudsimplus.vms.VmSimple;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import py4j.GatewayServer;

import java.net.InetAddress;
import java.util.ArrayList;
import java.util.List;

public class SimulationGateway {

    private static final Logger logger = LoggerFactory.getLogger(SimulationGateway.class);

    // Simulation state held at instance level, reset() rebuilds it
    private CloudSimPlus simulation;
    private DatacenterBrokerSimple broker;

    // Placeholder constants — these will be driven by config/dataset later
    private static final int NUM_HOSTS = 4;
    private static final int HOST_PES = 8;
    private static final long HOST_RAM = 16_384;  // MB
    private static final long HOST_BW = 10_000;   // Mbps
    private static final long HOST_STORAGE = 1_000_000; // MB
    private static final int VM_PES = 2;
    private static final long VM_MIPS = 1000;
    private static final int NUM_VMS = 4;

    public SimulationGateway() {
        // Instance is the Py4j entry point; initialization deferred to reset()
    }

    // reset() rebuilds the full simulation for each RL episode.
    // CloudSimPlus simulations cannot be restarted in place, so a fresh
    // CloudSimPlus instance and datacenter are constructed on every call.
    public void reset() {
        logger.info("Resetting simulation environment for new episode.");
        simulation = new CloudSimPlus();

        // Build hosts
        List<HostSimple> hosts = new ArrayList<>();
        for (int i = 0; i < NUM_HOSTS; i++) {
            List<Pe> peList = new ArrayList<>();
            for (int j = 0; j < HOST_PES; j++) {
                peList.add(new PeSimple(VM_MIPS));
            }
            hosts.add(new HostSimple(HOST_RAM, HOST_BW, HOST_STORAGE, peList));
        }

        // Build datacenter and broker
        new DatacenterSimple(simulation, hosts);
        broker = new DatacenterBrokerSimple(simulation);

        // Submit placeholder VMs — workload submission will be added
        // once the dataset module is ready
        List<VmSimple> vms = new ArrayList<>();
        for (int i = 0; i < NUM_VMS; i++) {
            vms.add(new VmSimple(VM_MIPS, VM_PES));
        }
        broker.submitVmList(vms);

        logger.info("Simulation reset complete. {} hosts, {} VMs ready.", NUM_HOSTS, NUM_VMS);
    }

    // step() advances the simulation by running it and returning
    // a basic observation. Action handling and reward calculation will be
    // wired in once the RL interface and dataset are finalized 
    public double[] step(int action) {
        if (simulation == null) {
            throw new IllegalStateException("Simulation not initialized. Call reset() first.");
        }
        simulation.start();
        return getObservation();
    }

    // getObservation() returns a primitive double[] for efficient
    // Py4j transfer. Java objects and collections are significantly
    // slower across the bridge under RL training throughput.
    public double[] getObservation() {
        if (broker == null) {
            return new double[]{0.0, 0.0, 0.0};
        }
        double finishedCloudlets = broker.getCloudletFinishedList().size();
        double createdVms = broker.getVmCreatedList().size();
        // Placeholder: extend with queue lengths, SLA metrics, etc. once
        // dataset and reward module are integrated
        return new double[]{finishedCloudlets, createdVms, 0.0};
    }

    // isDone() signals episode termination to the Gymnasium wrapper
    public boolean isDone() {
        return simulation != null && simulation.isTerminationTimeSet();
    }

    public static void main(String[] args) {
        // Port configurable via environment variable, not hardcoded
        int port = Integer.parseInt(System.getenv().getOrDefault("GATEWAY_PORT", "25333"));

        try {
            InetAddress bindAddress = InetAddress.getByName("0.0.0.0");
            SimulationGateway app = new SimulationGateway();

            GatewayServer server = new GatewayServer.GatewayServerBuilder(app)
                    .javaAddress(bindAddress)
                    .javaPort(port)
                    .build();

            // JVM shutdown hook for clean server teardown
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                logger.info("Shutting down Py4J Gateway Server...");
                server.shutdown();
            }));

            logger.info("Starting Py4J Gateway Server on 0.0.0.0:{}...", port);
            server.start();

        } catch (Exception e) {
            //  Descriptive error message before exit, not just a stack trace
            logger.error("Fatal error starting Gateway Server on port {}: {}", port, e.getMessage(), e);
            System.exit(1);
        }
    }
}
```