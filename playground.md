# Class Machine Inventory

Assessment date: 2026-08-11.

| Assignment | Student VM/user | Cloud | Public IP | Region | Zone | Status | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | abuafefa10/ubuntu | GCE | 34.89.213.74 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 02 | afayyad/ubuntu | GCE | 35.242.241.214 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 03 | ahmad941444/ubuntu | GCE | 34.40.24.124 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 04 | ahmadmansoor343/ubuntu | GCE | 34.159.133.89 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 05 | akhraisat/ubuntu | GCE | 34.89.184.140 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 06 | aomari/ubuntu | GCE | 34.179.227.140 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 07 | gsmadi/ubuntu | GCE | 34.159.107.1 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 08 | masalhahahmad/ubuntu | GCE | 34.40.126.38 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 09 | mhamaydeh/ubuntu | GCE | 35.246.145.213 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 10 | mohammadalmahsere26/ubuntu | GCE | 136.92.21.181 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 11 | mwedyan/ubuntu | GCE | 34.89.250.191 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 12 | qdaqa/ubuntu | GCE | 34.185.149.73 | europe-west3 | europe-west3-a | Ready | Assessed baseline passes. |
| 13 | radumoisan/ubuntu | GCE | 34.179.138.102 | europe-west3 | europe-west3-a | Blocked | NTP not synchronized; all other assessed baseline checks pass. |
| 14 | rhatter/ubuntu | GCE | 34.40.65.44 | europe-west3 | europe-west3-a | Blocked | NTP not synchronized; all other assessed baseline checks pass. |
| 15 | rhourani/ubuntu | GCE | 34.89.230.234 | europe-west3 | europe-west3-a | Blocked | NTP not synchronized; all other assessed baseline checks pass. |
| 16 | rtarawneh/ubuntu | GCE | 34.107.15.207 | europe-west3 | europe-west3-a | Blocked | NTP not synchronized; all other assessed baseline checks pass. |
| 17 | srehenkhaled7/ubuntu | GCE | 35.198.141.98 | europe-west3 | europe-west3-a | Blocked | NTP not synchronized; all other assessed baseline checks pass. |

## Assessment baseline

All 17 assignments passed SSH access, Ubuntu 24.04, 8 vCPUs, approximately 32 GiB RAM, approximately 250 GB disk, KVM device availability, passwordless `sudo`, required files (7 in `~/config` and 24 in `~/resources`), `snapd`/`systemd`, LXD absent or uninitialized, and outbound HTTPS. `gce-pvc.yaml` is not required initially because the lab supplies its manifest inline.
