from scapy.all import rdpcap,IP,TCP
import numpy as np
import matplotlib.pyplot as plt
source_ip = '10.10.10.2'
file_name = './resources/timegap.pcap'


def extract_ethernet_src_address(pcap_file):
    # 读取PCAP文件  
    packets = rdpcap(pcap_file)
    print(f"Read over packets: {len(packets)}")

    # 创建一个集合以存储唯一的以太网源地址  
    src_addresses = []

    # 遍历每一个数据包  
    for packet in packets:
        # 检查数据包是否包含以太网层  
        if packet.haslayer(IP) and packet[IP].src==source_ip and packet.haslayer('Ether'):
            src = packet['Ether'].src
            src_addresses.append(int(src.replace(':',''),16))

    return sorted(src_addresses)

def cal_diff(data):
    diff= np.diff(data)
    
    return diff[diff<10000]    # 10us

def gen_step(y,x):
    y=np.append(y,y[-1])

    x=np.insert(x,0,0)
    y=np.insert(y,0,0)

    x=np.append(x,x[-1])
    y=np.append(y,0)
    return y,x

def plot_histogram(r):
    bins = 20
    plt.clf()  # 清除画布

    # 计算直方图数据  
    r_y, r_x = gen_step(*np.histogram(r,density=False))
    # plt.figure(figsize=(10, 8))


    plt.step(r_x, r_y, where='post',  color='red', label='RDMA',linewidth=2)  

    # plt.xticks(bin_edges)
    # plt.xlim(0,50)
    plt.yscale('log')
    plt.tick_params(axis='x',labelsize=16,rotation=15)
    plt.tick_params(axis='y',labelsize=16)
    plt.xlabel('Time Gaps (ns)',fontsize=18)
    plt.ylabel('Density',fontsize=18)
    plt.title(f'Time Gap Distribution of Prototype',fontsize=18)
    # plt.grid(True)
    plt.legend(fontsize=18)
    plt.tight_layout()

    # 显示图表
    plt.savefig(file_name+'_density_10000.png')

if __name__=='__main__':
    print(f'{file_name} processing...')
    t_addresses = extract_ethernet_src_address(file_name)
    t=cal_diff(t_addresses)
    plot_histogram(t)
    print(f'{file_name} complete...')
    print('over...')