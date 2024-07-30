# Basic VM

```bash
create_template.py --vmid 2999 --name "Ubuntu24-04" --iso noble-server-cloudimg-amd64.img
```

### with a VLAN

```bash
create_template.py --vmid 2999 --name "Ubuntu24-04" --cinit ubuntu-user-data.yml --iso noble-server-cloudimg-amd64.img --vlan 30
```

### Cloud-init file must be in /var/lib/vz/snippets

```bash
create_template.py --vmid 2999 --name "Ubuntu24-04" --cinit ubuntu-user-data.yml --iso noble-server-cloudimg-amd64.img --vlan 30
```

# Requirements

### Install Dependecies

```
pip install -r requirements.txt
```

### Dependecies

- tqdm
