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

from org.cloudsimplus.core import CloudSimPlus
from org.cloudsimplus.datacenters import DatacenterSimple
from org.cloudsimplus.hosts import HostSimple
from org.cloudsimplus.resources import PeSimple
from org.cloudsimplus.vms import VmSimple
from org.cloudsimplus.cloudlets import CloudletSimple
from org.cloudsimplus.brokers import DatacenterBrokerSimple
from org.cloudsimplus.schedulers.cloudlet import CloudletSchedulerTimeShared
from org.cloudsimplus.schedulers.vm import VmSchedulerTimeShared

print("correcto")