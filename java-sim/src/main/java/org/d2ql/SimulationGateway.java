package org.d2ql;

import py4j.GatewayServer;
import java.net.InetAddress;
import org.cloudsimplus.core.CloudSimPlus;

public class SimulationGateway {
    private CloudSimPlus simulation;

    public SimulationGateway() {
        // Entry point instance. Additional helper methods can be added here
        // to simplify simulation initialization for Py4j.
    }

    public CloudSimPlus createSimulation() {
        this.simulation = new CloudSimPlus();
        return this.simulation;
    }

    public static void main(String[] args) {
        try {
            // Bind to 0.0.0.0 to allow container network communication
            InetAddress bindAddress = InetAddress.getByName("0.0.0.0");
            SimulationGateway app = new SimulationGateway();
            GatewayServer server = new GatewayServer(app, 25333, bindAddress);
            
            System.out.println("Starting Py4J Gateway Server on 0.0.0.0:25333...");
            server.start();
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}