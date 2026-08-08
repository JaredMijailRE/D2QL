import subprocess
import shutil
from pathlib import Path

def main():
    tmp_dir = Path("/tmp/csplus")
    libs_dir = Path("libs")
    libs_dir.mkdir(exist_ok=True)
    
    # 1. Limpiar carpeta temporal previa si existe
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
        
    print("Clonando y compilando CloudSim Plus...")
    try:
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/cloudsimplus/cloudsimplus.git", str(tmp_dir)], check=True)
        subprocess.run(["mvn", "-f", str(tmp_dir / "pom.xml"), "clean", "package", "dependency:copy-dependencies", "-DskipTests"], check=True)
        
        for jar in (tmp_dir / "target").glob("cloudsimplus-*.jar"):
            shutil.copy(jar, libs_dir)
            
        dep_dir = tmp_dir / "target" / "dependency"
        if dep_dir.exists():
            for dep in dep_dir.glob("*.jar"):
                shutil.copy(dep, libs_dir)
                
        print("Librerías compiladas y copiadas exitosamente en ./libs")
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()