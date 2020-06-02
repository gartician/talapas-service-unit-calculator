# UO Talapas Service Unit Calculator

The purpose of this tool is to allow UO personnel to calculate the price of their computational jobs.



# Talapas Cluster Scheme

![image-20200602125946614](C:\Users\Garth_Kong\AppData\Roaming\Typora\typora-user-images\image-20200602125946614.png)

# How is cost calculated?


$$
\sum_{1}^{allocNodes} (max(allocCPU / totalCPU, allocRAM / totalRAM, allocGPU / totalGPU) * NTF) * 28 SU / hr * job\_duration\ (hr)
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

