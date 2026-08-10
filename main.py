import random
from pathlib import Path
from py4j.java_gateway import JavaGateway, java_import

libs_path = Path(__file__).parent / "libs" / "*"

gateway = JavaGateway.launch_gateway(
    classpath=str(libs_path),
    javaopts=["--enable-native-access=ALL-UNNAMED"],
    die_on_exit=True
)

jvm = gateway.jvm

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

simulation = jvm.CloudSimPlus()

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

class RandomSchedulerAgent:
    def schedule(self, cloudlets, vms):
        for cloudlet in cloudlets:
            selected_vm = random.choice(vms)
            cloudlet.setVm(selected_vm)

agent = RandomSchedulerAgent()
agent.schedule(cloudlet_list, vm_list)

broker.submitVmList(to_java_list(vm_list))
broker.submitCloudletList(to_java_list(cloudlet_list))

simulation.start()

for cloudlet in broker.getCloudletFinishedList():
    print(
        f"Cloudlet {cloudlet.getId()} -> "
        f"Asignado a VM {cloudlet.getVm().getId()} | "
        f"Tiempo de CPU: {cloudlet.getTotalExecutionTime():.2f}s"
    )

gateway.shutdown()