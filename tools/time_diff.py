from scapy.all import rdpcap,IP,TCP
import numpy as np
import matplotlib.pyplot as plt
source_ip = '10.10.10.2'
file_list=['AliStorage','Hadoop','Solar','WebSearch']
paper_names=['AliCloud Storage','Meta Hadoop','Solar RPC','Web Search']


def extract_ethernet_src_address(pcap_file):
    # 读取PCAP文件  
    packets = rdpcap(pcap_file)

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
    return diff[diff<120000]    # 120us

def gen_step(y,x):
    y=np.append(y,y[-1])

    x=np.insert(x,0,0)
    y=np.insert(y,0,0)

    x=np.append(x,x[-1])
    y=np.append(y,0)
    return y,x

def plot_histogram(r,t,index):
    pro_name=pcap_file_rdma.split('_')[1]
    bins = 20
    bin_min = min(r.min(), t.min())  
    bin_max = max(r.max(), t.max())  
    shared_bins = np.linspace(0, bin_max, bins + 1)  
    plt.clf()  # 清除画布

    # 计算直方图数据  
    r_y, r_x = gen_step(*np.histogram(r, bins=shared_bins,density=True))
    t_y, t_x = gen_step(*np.histogram(t, bins=shared_bins,density=True))
    # plt.figure(figsize=(10, 8))



    plt.step(t_x, t_y, where='post', linestyle='--', color='blue', label='TCP',linewidth=2)  
    plt.step(r_x, r_y, where='post',  color='red', label='RDMA',linewidth=2)  

    # plt.xticks(bin_edges)
    # plt.xlim(0,50)
    plt.yscale('log')
    plt.tick_params(axis='x',labelsize=16,rotation=15)
    plt.tick_params(axis='y',labelsize=16)
    plt.xlabel('Time Gaps (ns)',fontsize=18)
    plt.ylabel('Density',fontsize=18)
    plt.title(f'Time Gap Distribution of {paper_names[index]}',fontsize=18)
    # plt.grid(True)
    plt.legend(fontsize=18)
    plt.tight_layout()

    # 显示图表
    plt.savefig(pro_name+'_density.pdf')

if __name__=='__main__':
    i =0
    for file_name in file_list:
        print(f'{file_name} processing...')
        pcap_file_tcp = f'../sniffer/tcp_{file_name}.pcap'
        pcap_file_rdma = f'../sniffer/capture_{file_name}_RDMA.pcap'
        r_addresses = extract_ethernet_src_address(pcap_file_rdma)
        t_addresses = extract_ethernet_src_address(pcap_file_tcp)
        r=cal_diff(r_addresses)
        t=cal_diff(t_addresses)
        plot_histogram(r,t,i)
        print(f'{file_name} complete...')
        i+=1
    print('over...')