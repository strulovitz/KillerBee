#!/usr/bin/env python3
import subprocess, sys, os, xml.etree.ElementTree as ET

NAMES = ["giantqueen-b", "dwarfqueen-b1", "dwarfqueen-b2",
         "worker-b1", "worker-b2", "worker-b3", "worker-b4"]
POOL = "/var/lib/libvirt/images/phase3"
TEMPLATE = "desktop-template"
TEMPLATE_DISK = f"{POOL}/{TEMPLATE}.qcow2"

def run(cmd, check=True):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("STDOUT:", r.stdout); print("STDERR:", r.stderr)
        sys.exit(1)
    return r.stdout

xml_src = run(["sudo", "virsh", "dumpxml", TEMPLATE])

for name in NAMES:
    print(f"=== cloning {TEMPLATE} -> {name} ===")
    dst_disk = f"{POOL}/{name}.qcow2"
    tmp_disk = f"/tmp/{name}.qcow2"

    # qcow2 differential clone (backing file = template). Created in /tmp as
    # 'nir' (libvirt pool dir is root-owned), then sudo-mv into the pool.
    if os.path.exists(tmp_disk):
        os.remove(tmp_disk)
    run(["qemu-img", "create", "-f", "qcow2",
         "-b", TEMPLATE_DISK, "-F", "qcow2", tmp_disk])
    run(["sudo", "mv", tmp_disk, dst_disk])

    # Build the clone's libvirt XML from the template's
    root = ET.fromstring(xml_src)
    root.find("name").text = name
    uuid = root.find("uuid")
    if uuid is not None: root.remove(uuid)

    devices = root.find("devices")
    # Point vda at new disk, drop sdb (seed iso)
    for disk in list(devices.findall("disk")):
        tgt = disk.find("target")
        if tgt is None: continue
        if tgt.get("dev") == "vda":
            src = disk.find("source")
            if src is not None: src.set("file", dst_disk)
            bs = disk.find("backingStore")
            if bs is not None: disk.remove(bs)
        elif tgt.get("dev") == "sdb":
            devices.remove(disk)

    # Regenerate MACs, pty paths, aliases, PCI addresses
    for iface in root.findall("devices/interface"):
        mac = iface.find("mac")
        if mac is not None: iface.remove(mac)
    for el in root.findall("devices/serial/source"):
        if el.get("path") is not None: del el.attrib["path"]
    for el in root.findall("devices/console/source"):
        if el.get("path") is not None: del el.attrib["path"]
    for parent in root.iter():
        for alias in list(parent.findall("alias")):
            parent.remove(alias)
    for parent in root.iter():
        if parent.tag == "hostdev":
            continue
        for addr in list(parent.findall("address")):
            parent.remove(addr)

    out_xml = f"/tmp/{name}.xml"
    ET.ElementTree(root).write(out_xml)
    run(["sudo", "virsh", "define", out_xml])

print("All 7 clones defined.")
print(run(["sudo", "virsh", "list", "--all"]))
