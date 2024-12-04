#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import argparse
import matplotlib.pyplot as plt  

file_size=143

def plot_cdf(data):  
    # 将二维列表转换为两个列表：时间和CDF值  
    time = data[0]  
    cdf =  data[1]   
    # 创建图形  
    fig=plt.figure(figsize=(10, 6))  

    ax=fig.add_subplot(111)
    
    
    ax.set_title('CDF Plot')  
    ax.set_xlabel('Msg/Flow Size(Bytes)')  
    ax.set_ylabel('CDF')  
    ax.set_xscale('log')
    ax.set_xticks([10,1000,100000,10000000])
    ax.set_xticklabels(['10B','1KB','100KB','10MB'])
    ax.set_xlim(10, 10200000)

    ax.plot(time, cdf, linestyle='--', color='b')  
    
    plt.grid(True)  
    
    plt.show() 
    plt.savefig('fig.png',dpi=300)

def get_cdf(v: list):        
    # calculate cdf
    v_sorted = sorted(v,key=lambda x:x[0])
    p = 1. * np.arange(len(v)) / (len(v) - 1)
    od = []
    bkt = [0,0,0,0]
    len_accum = 0
    time=[]
    cdf=[]
    for i in range(len(v_sorted)):
        key = v_sorted[i][1]/1000.0 
        len_accum = v_sorted[i][0]
        if bkt[0] == key:
            bkt[1] += 1
            bkt[2] = len_accum
            bkt[3] = p[i]
        else:
            od.append(bkt)
            bkt = [0,0,0,0]
            bkt[0] = key
            bkt[1] = 1
            bkt[2] = len_accum
            bkt[3] = p[i]
    if od[-1][0] != bkt[0]:
        od.append(bkt)
    od.pop(0)

    ret = ""
    for bkt in od:
        var = str(bkt[0]) + " " + str(bkt[1]) + " " + str(bkt[2]) + " " + str(bkt[3]) + "\n"
        ret += var
        # time.append(bkt[1]*file_size+time[-1] if len(time)!=0 else 0)
        time.append(bkt[2])
        cdf.append(bkt[3])
        
    return ret,[time,cdf]

def get_bandwidth_utilization(data:list):
    """  
    Calculate network bandwidth utilization.  

    Parameters:  
    data (list of lists): n*3 list, where:  
        - First column is the packet size in bytes.  
        - Third column is the time of sending in seconds.  
        
    Returns:  
    float: Bandwidth utilization as a percentage.  
    """  
    
    # Calculate the total data sent in bits  
    total_data_sent_bits = sum(row[0] * 8 for row in data)  
    
    print(sum(row[1] for row in data))
    # Calculate the total time in seconds 
    total_time =  sum(row[1] for row in data) /1_000_000_000
    
    max_network_capacity_bps = 40 * (10**9)  # 40 Gbps  
    
    # Calculate the actual bandwidth used  
    actual_bandwidth_bps = total_data_sent_bits / total_time  
    print(actual_bandwidth_bps)
    
    # Calculate the utilization percentage  
    utilization_percentage = (actual_bandwidth_bps / max_network_capacity_bps) * 100  
    
    return utilization_percentage  


def main():
    parser = argparse.ArgumentParser(description='get CDF of FCTs')
    parser.add_argument('-name', dest='name', action='store', required=True, help="Output filename in /log folder")
    # args = parser.parse_args()
    args='./log/log.dat'

    # filename = os.getcwd() + "/{}".format(args.name)
    filename = os.getcwd() + "/{}".format(args)
    print("Read output log file: {}".format(filename))
    
    if os.path.exists(filename) != True:
        print("ERROR - Cannot find the file!!")
        exit(1)

    pkg_data=[]
    with open(filename, "r") as f:
        for line in f.readlines():
            parsed_line = line.replace("\n","").split(",")
            pkg_data.append([float(parsed_line[0]),float(parsed_line[1]),float(parsed_line[2])])
    

    _,data=get_cdf(pkg_data)
    plot_cdf(data)

    utilization = get_bandwidth_utilization(pkg_data)  
    print(f"Bandwidth utilization: {utilization:.2f}%") 



if __name__ == "__main__":
    main()