#!/usr/bin/env python3

import subprocess
import argparse
import sys
import logging
import os
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def create_template(
    vm_id: int,
    vm_name: str,
    vm_vlan: int,
    mem: int,
    cores: int,
    cinit: str,
    iso_file: str,
    ostype: str,
):
    """Create a template from ISO.

    Args:
        vm_id (int): Virtual Machine ID
        vm_name (str): Virtual Machine name
        vm_vlan (int): VLAN ID
        mem (int): Memory size in MB
        cores (int): Number of CPU cores
        cinit (str): Cloud-Init configuration file name
        iso_file (str): Path to the ISO file
        ostype (str): Operating system type
    """

    steps = [
        ("Creating VM", [
            "qm", "create", str(vm_id), "--name", vm_name, "--ostype", ostype, "--tablet", "0"
        ]),
        ("Configuring Network", [
            "qm", "set", str(vm_id), "--net0", f"virtio,bridge=vmbr0" + (f",tag={vm_vlan}" if vm_vlan else ""),
            "--memory", str(mem), "--cores", str(cores), "--cpu", "host"
        ]),
        ("Setting ISO", [
            "qm", "set", str(vm_id), "--scsi0", f"local-lvm:0,import-from={iso_file},discard=on,ssd=1"
        ]),
        ("Configuring Boot", [
            "qm", "set", str(vm_id), "--boot", "order=scsi0", "--scsihw", "virtio-scsi-single",
            "--agent", "enabled=1,fstrim_cloned_disks=1"
        ]),
        ("Configuring Cloud-Init", [
            "qm", "set", str(vm_id), "--ide2", "local-lvm:cloudinit", "--ipconfig0", "ip=dhcp"
        ]),
        ("Setting Cloud-Init Customization", [
            "qm", "set", str(vm_id), "--cicustom", f"user=local:snippets/{cinit}"
        ] if cinit else []),
        ("Creating Template", ["qm", "template", str(vm_id)])
    ]

    try:
        with tqdm(total=len(steps), desc="Creating Template") as pbar:
            for desc, cmd in steps:
                if cmd:  # Only run if command is not empty
                    logging.info(f"{desc} for VM ID {vm_id}")
                    subprocess.check_call(cmd)
                pbar.update(1)

        logging.info("Template creation for VM ID %s completed successfully", vm_id)
    except subprocess.CalledProcessError as e:
        logging.error("An error occurred while creating the template: %s", e)
    except FileNotFoundError as e:
        logging.error("File not found error: %s", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)


def main():
    parser = argparse.ArgumentParser(
        description="Create a VM template from an ISO file."
    )
    parser.add_argument("--vmid", type=int, required=True, help="Virtual Machine ID")
    parser.add_argument("--name", type=str, required=True, help="Virtual Machine name")
    parser.add_argument(
        "--vlan", type=int, required=False, default=0, help="VLAN ID"
    )
    parser.add_argument(
        "--memory", type=int, required=False, default=2046, help="Memory size in MB"
    )
    parser.add_argument(
        "--cores", type=int, required=False, default=2, help="Number of CPU cores"
    )
    parser.add_argument(
        "--cinit",
        type=str,
        required=False,
        default="",
        help="Cloud-Init configuration file name",
    )
    parser.add_argument("--iso", type=str, required=True, help="Path to the ISO file")
    parser.add_argument(
        "--ostype",
        type=str,
        required=False,
        default="l26",
        help="Operating system type (default: l26)",
    )
    args = parser.parse_args()

    # Pre-checks
    # No spaces in the template name
    if " " in args.name:
        logging.error("VM name contains spaces. Please use a name without spaces.")
        sys.exit()

    # Convert path to full path for the iso
    if not os.path.isabs(args.iso):
        args.iso = os.path.join(os.getcwd(), args.iso)
        logging.info(f"Converted ISO path to absolute path: {args.iso}")

    # Check that the ISO file is in the current directory or the correct ISO directory
    iso_dir = "/var/lib/vz/template/iso"
    if not os.path.exists(args.iso):
        logging.info(f"ISO file not found in current directory, checking {iso_dir}")
        iso_file_in_dir = os.path.join(iso_dir, os.path.basename(args.iso))
        if os.path.exists(iso_file_in_dir):
            args.iso = iso_file_in_dir
            logging.info(f"ISO file found in {iso_dir}, using path: {args.iso}")
        else:
            logging.error(f"The ISO file must be located in the current directory or '{iso_dir}'")
            sys.exit(1)

    # Check that the cloud-init file is there
    if args.cinit:
        snippets_dir = "/var/lib/vz/snippets"
        cinit_file = os.path.join(snippets_dir, args.cinit)
        if not os.path.exists(cinit_file):
            logging.error(
                f"The Cloud-Init file '{args.cinit}' does not exist in '{snippets_dir}'"
            )
            sys.exit(1)

    create_template(
        args.vmid,
        args.name,
        args.vlan,
        args.memory,
        args.cores,
        args.cinit,
        args.iso,
        args.ostype,
    )

if __name__ == "__main__":
    main()
