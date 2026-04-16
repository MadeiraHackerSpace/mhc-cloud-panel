from typing import Any, Dict
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="Proxmox API Mock")

# State
next_vmid_val = 1000
vms = {
    "9000": {"name": "Ubuntu 22.04 Cloud-Init", "template": 1, "status": "stopped"},
    "9001": {"name": "Debian 12 Cloud-Init", "template": 1, "status": "stopped"},
}

@app.get("/api2/json/nodes")
def get_nodes():
    return {
        "data": [
            {
                "node": "pve",
                "status": "online",
                "cpu": 0.05,
                "maxcpu": 8,
                "mem": 4 * 1024 * 1024 * 1024,
                "maxmem": 32 * 1024 * 1024 * 1024,
                "disk": 100 * 1024 * 1024 * 1024,
                "maxdisk": 500 * 1024 * 1024 * 1024,
                "uptime": 3600,
            },
            {
                # Second node with more free resources to exercise NodeScheduler
                "node": "pve2",
                "status": "online",
                "cpu": 0.02,
                "maxcpu": 16,
                "mem": 2 * 1024 * 1024 * 1024,
                "maxmem": 64 * 1024 * 1024 * 1024,
                "disk": 50 * 1024 * 1024 * 1024,
                "maxdisk": 1000 * 1024 * 1024 * 1024,
                "uptime": 7200,
            },
        ]
    }

@app.get("/api2/json/nodes/{node}/storage")
def get_storages(node: str):
    return {
        "data": [
            {
                "storage": "local-lvm",
                "type": "lvmthin",
                "content": "images,rootdir",
                "active": 1,
                "total": 500 * 1024 * 1024 * 1024,
                "used": 100 * 1024 * 1024 * 1024,
            }
        ]
    }

@app.get("/api2/json/nodes/{node}/qemu")
def get_qemu(node: str):
    data = []
    for vmid, vm in vms.items():
        data.append({
            "vmid": int(vmid),
            "name": vm["name"],
            "status": vm["status"],
            "template": vm.get("template", 0),
        })
    return {"data": data}

@app.get("/api2/json/cluster/nextid")
def get_nextid():
    global next_vmid_val
    val = next_vmid_val
    next_vmid_val += 1
    return {"data": str(val)}

@app.post("/api2/json/nodes/{node}/qemu/{vmid}/clone")
async def clone_vm(node: str, vmid: str, request: Request):
    form = await request.form()
    newid = form.get("newid")
    name = form.get("name", f"vm-{newid}")
    if newid:
        vms[str(newid)] = {"name": name, "template": 0, "status": "stopped", "config": {}}
    return {"data": f"UPID:{node}:00000000:00000000:00000000:qmclone:{newid}:root@pam!"}

@app.post("/api2/json/nodes/{node}/qemu/{vmid}/config")
async def config_vm(node: str, vmid: str, request: Request):
    form = await request.form()
    if vmid in vms:
        vms[vmid]["config"] = dict(form)
    return {"data": None}

@app.post("/api2/json/nodes/{node}/qemu/{vmid}/status/start")
def start_vm(node: str, vmid: str):
    if vmid in vms:
        vms[vmid]["status"] = "running"
    return {"data": f"UPID:{node}:00000000:00000000:00000000:qmstart:{vmid}:root@pam!"}

@app.post("/api2/json/nodes/{node}/qemu/{vmid}/status/stop")
def stop_vm(node: str, vmid: str):
    if vmid in vms:
        vms[vmid]["status"] = "stopped"
    return {"data": f"UPID:{node}:00000000:00000000:00000000:qmstop:{vmid}:root@pam!"}

@app.post("/api2/json/nodes/{node}/qemu/{vmid}/status/reboot")
def reboot_vm(node: str, vmid: str):
    if vmid in vms:
        vms[vmid]["status"] = "running"
    return {"data": f"UPID:{node}:00000000:00000000:00000000:qmreboot:{vmid}:root@pam!"}

@app.get("/api2/json/nodes/{node}/qemu/{vmid}/status/current")
def current_status(node: str, vmid: str):
    vm = vms.get(vmid, {"status": "stopped"})
    return {
        "data": {
            "status": vm["status"],
            "cpu": 0.05 if vm["status"] == "running" else 0.0,
            "mem": 512 * 1024 * 1024 if vm["status"] == "running" else 0,
            "maxmem": 2048 * 1024 * 1024,
            "netin": 1000,
            "netout": 2000,
            "diskread": 0,
            "diskwrite": 0,
        }
    }

@app.delete("/api2/json/nodes/{node}/qemu/{vmid}")
def delete_vm(node: str, vmid: str):
    if vmid in vms:
        del vms[vmid]
    return {"data": f"UPID:{node}:00000000:00000000:00000000:qmdestroy:{vmid}:root@pam!"}


@app.post("/api2/json/nodes/{node}/qemu/{vmid}/migrate")
async def migrate_vm(node: str, vmid: str, request: Request):
    """Mock live migration — just records the new node in VM state."""
    form = await request.form()
    target = form.get("target", node)
    if vmid in vms:
        vms[vmid]["node"] = target  # Track where the VM "moved"
    return {"data": f"UPID:{target}:00000000:00000000:00000000:qmmigrate:{vmid}:root@pam!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("proxmox_mock:app", host="0.0.0.0", port=8001, reload=True)


@app.post("/api2/json/nodes/{node}/qemu/{vmid}/vncproxy")
def create_vnc_proxy(node: str, vmid: str):
    return {
        "data": {
            "ticket": "mock-vnc-ticket-" + vmid,
            "port": 5900 + int(vmid) % 100,
            "upid": f"UPID:{node}:00000000:00000000:00000000:qmvncproxy:{vmid}:root@pam!"
        }
    }