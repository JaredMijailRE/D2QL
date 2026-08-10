import random
from pathlib import Path
import jpype
import jpype.imports

libs_path = Path(__file__).parent / "libs" / "*"

if not jpype.isJVMStarted():
    jpype.startJVM(
        "--enable-native-access=ALL-UNNAMED",
        classpath=[str(libs_path)]
    )

from java.util import ArrayList

from org.cloudsimplus.core import CloudSimPlus
from org.cloudsimplus.datacenters import DatacenterSimple
from org.cloudsimplus.hosts import HostSimple
from org.cloudsimplus.resources import PeSimple
from org.cloudsimplus.vms import VmSimple
from org.cloudsimplus.cloudlets import CloudletSimple
from org.cloudsimplus.brokers import DatacenterBrokerSimple
from org.cloudsimplus.schedulers.cloudlet import CloudletSchedulerTimeShared
from org.cloudsimplus.schedulers.vm import VmSchedulerTimeShared

simulation = CloudSimPlus()

pe_list = ArrayList([PeSimple(1000) for _ in range(8)])
host = HostSimple(16384, 10000, 1000000, pe_list)
host.setVmScheduler(VmSchedulerTimeShared())

datacenter = DatacenterSimple(simulation, ArrayList([host]))
broker = DatacenterBrokerSimple(simulation)

vm_list = [
    VmSimple(1000, 1).setRam(2048).setBw(1000).setSize(10000).setCloudletScheduler(CloudletSchedulerTimeShared())
    for _ in range(5)
]

cloudlet_list = [
    CloudletSimple(10000, 1)
    for _ in range(10)
]

class RandomSchedulerAgent:
    def schedule(self, cloudlets, vms):
        for cloudlet in cloudlets:
            selected_vm = random.choice(vms)
            cloudlet.setVm(selected_vm)

agent = RandomSchedulerAgent()
agent.schedule(cloudlet_list, vm_list)

broker.submitVmList(ArrayList(vm_list))
broker.submitCloudletList(ArrayList(cloudlet_list))

simulation.start()

# Imprimir resultados
for cloudlet in broker.getCloudletFinishedList():
    print(
        f"Cloudlet {cloudlet.getId()} -> "
        f"Asignado a VM {cloudlet.getVm().getId()} | "
        f"Tiempo de CPU: {cloudlet.getTotalExecutionTime():.2f}s"
    )
    
jpype.shutdownJVM()