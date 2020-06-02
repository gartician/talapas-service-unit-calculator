# UO Talapas Service Unit Calculator

The purpose of this tool is to allow UO personnel to calculate the price of their computational jobs.



# Talapas Cluster Scheme

## Club Nodes

Everyone with a Linux account can access club nodes.

| Qty  | Node Type         | Processors (total cores)  | Memory              | Local Storage (SSD) |
| ---- | ----------------- | ------------------------- | ------------------- | ------------------- |
| 96   | Standard          | dual E5-2690v4 (28 cores) | 128 GB              | 200 GB              |
| 24   | GPU               | dual E5-2690v4 (28 cores) | 256 GB              | 200 GB              |
| 8    | Large Memory Node | quad E7-4830v4 (56 cores) | 1 TB, 2 TB, or 4 TB | dual 480 GB         |

## Condo Nodes

Condo nodes are reserved for PI's who rented nodes for the lab's consumption.

| Qty  | Node Type | Processors (total cores)  | Memory            | Local Storage (SSD) |
| ---- | --------- | ------------------------- | ----------------- | ------------------- |
| 82   | Standard  | dual Gold 6148 (40 cores) | 192 GB, or 384 GB | 240 GB              |

# How is cost calculated?

Premise: service units are rooted around the concept that when using the base compute node, 1 CPU = 1 Service Unit. The idea here is that a job's usage effectively amounts to the largest  fraction of resources utilized by the job on a node. For instance, if a job uses all the available cores on a node but little memory then the  job is using 100% of the node (i.e. there are no cores available for  other jobs). Likewise, if a job is only using one core but requires  100% of the memory on a node, that job is also using 100% of the node  (there is insufficient memory for other jobs).



$$
Service\ Units = \sum_{1}^{allocNodes} (max(allocCPU / totalCPU, allocRAM / totalRAM, allocGPU / totalGPU) * NTF) * 28 SU / hr * job\_duration\ (hr)
$$




| Term         | Resources requested                                          |
| ------------ | ------------------------------------------------------------ |
| allocNodes   | Number of nodes                                              |
| allocCPU     | Number of CPU cores                                          |
| totalCPU     | Total available CPU cores in a node                          |
| allocRAM     | Quantity of RAM (GB)                                         |
| totalRAM     | Total quantity of RAM (GB) in a node<br />  In fat nodes, totalRAM is normalized to 1024 GB |
| allocGPU     | Number of GPU cores                                          |
| totalGPU     | Total quantity of GPU cores in a node                        |
| NTF          | Node type factor <br /> 1 = standard node<br /> 2 = gpu node <br /> 6 = fat node |
| 28 SU / hr   | Normalization factor.                                        |
| job_duration | Expected time required for the job (hr)                      |

# How to use the calculator

1. Click a link
2. Fill out first component
3. Tab through each field
4. Get results

